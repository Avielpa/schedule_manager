"""
🚨 Minimum Work Constraints - V9.0
Ensures every soldier performs a minimum amount of work and prevents soldiers from having no work
"""

from typing import TYPE_CHECKING
from ..config import (
    BASE_MIN_REGULAR_DAYS_THRESHOLD, BASE_MIN_WEEKEND_DAYS_THRESHOLD,
    EXCESS_BASE_PENALTY_MULTIPLIER, SHORTAGE_BASE_PENALTY_DIVISOR
)
from ..utils import calculate_constraints_ratio, calculate_available_days

if TYPE_CHECKING:
    from ..solver import SmartScheduleSoldiers


class MinimumWorkConstraints:
    """Class for managing minimum work constraints"""
    
    def __init__(self, solver_instance: 'SmartScheduleSoldiers'):
        self.solver = solver_instance
        self.model = solver_instance.model
        self.soldiers = solver_instance.soldiers
        self.calendar = solver_instance.calendar
        self.variables = solver_instance.variables
        self.penalty_no_work = solver_instance.penalty_no_work
        self.min_base_block_days = solver_instance.min_base_block_days
        self.exceptional_minimums = solver_instance.exceptional_minimums
        self.total_days = len(solver_instance.calendar)
        
    def apply(self) -> None:
        """Applies minimum work constraints"""
        print("💀 Adding deadly constraints against soldiers with no work...")
        
        self._add_exceptional_soldiers_constraints()
        self._add_weekend_soldiers_constraints() 
        self._add_regular_soldiers_constraints()
        
        print("✅ Minimum work constraints applied successfully")
    
    def _add_exceptional_soldiers_constraints(self) -> None:
        """Adds constraints for exceptional soldiers with a strict minimum"""
        _, _, total_weekend_base_days = self.variables.get_summary_variables()
        total_base_days, _, _ = self.variables.get_summary_variables()
        
        exceptional_count = 0
        
        for soldier in self.soldiers:
            # 🚨 Exceptional soldiers or those with many constraints receive a strict minimum
            constraints_ratio = len(soldier.raw_constraints) / self.total_days
            is_heavily_constrained = constraints_ratio > 0.4
            
            if soldier.name in self.exceptional_minimums or soldier.is_exceptional_output or is_heavily_constrained:
                
                if soldier.name in self.exceptional_minimums:
                    minimum_required = self.exceptional_minimums[soldier.name]
                else:
                    # Calculate dynamic minimum for exceptional soldiers
                    available_days = self.total_days - len(soldier.raw_constraints)
                    if soldier.is_weekend_only_soldier_flag:
                        minimum_required = max(2, min(6, available_days // 8))  # More strict
                    else:
                        minimum_required = max(8, min(20, available_days // 3))  # More strict
                
                print(f"    🚨 {soldier.name}: Strict minimum {minimum_required} days (exceptional)")
                
                # Strong hard constraint - must meet minimum
                self.model.Add(total_base_days[soldier.name] >= minimum_required)
                
                # Create shortage variable and deadly penalty
                shortage_vars = self.variables.create_exceptional_shortage_variables(
                    soldier.name, minimum_required
                )
                shortage_var = shortage_vars['shortage']
                
                self.model.Add(shortage_var >= minimum_required - total_base_days[soldier.name])
                self.model.Add(shortage_var >= 0)
                
                # Increased deadly penalty for shortage of exceptional soldiers
                exceptional_penalty = self.penalty_no_work * 3  # 3x penalty!
                self.solver.objective_terms.append(shortage_var * exceptional_penalty)
                exceptional_count += 1
        
        print(f"    📊 {exceptional_count} exceptional soldiers defined with strict minimums")
    
    def _add_weekend_soldiers_constraints(self) -> None:
        """Adds constraints for weekend soldiers"""
        total_base_days, _, _ = self.variables.get_summary_variables()
        _, _, total_weekend_base_days = self.variables.get_summary_variables()
        
        weekend_soldiers_count = 0
        
        for soldier in self.soldiers:
            if soldier.is_weekend_only_soldier_flag and soldier.name not in self.exceptional_minimums:
                minimum_weekends = BASE_MIN_WEEKEND_DAYS_THRESHOLD
                
                print(f"    🏖️ {soldier.name}: Minimum {minimum_weekends} weekends")
                
                # Hard constraint on number of weekends
                self.model.Add(total_weekend_base_days[soldier.name] >= minimum_weekends)
                
                # Hard constraint on total base days (weekends * minimum days in block)
                min_total_base = minimum_weekends * max(3, self.min_base_block_days)
                self.model.Add(total_base_days[soldier.name] >= min_total_base)
                
                # Shortage variable and penalty
                weekend_shortage_vars = self.variables.create_weekend_shortage_variables(soldier.name)
                weekend_shortage_var = weekend_shortage_vars['shortage']
                
                self.model.Add(weekend_shortage_var >= minimum_weekends - total_weekend_base_days[soldier.name])
                self.model.Add(weekend_shortage_var >= 0)
                
                # Deadly penalty for weekend shortage
                self.solver.objective_terms.append(weekend_shortage_var * self.penalty_no_work)
                weekend_soldiers_count += 1
        
        print(f"    🏖️ {weekend_soldiers_count} weekend soldiers defined with minimums")
    
    def _add_regular_soldiers_constraints(self) -> None:
        """Adds constraints for regular soldiers"""
        total_base_days, _, _ = self.variables.get_summary_variables()
        
        regular_soldiers_count = 0
        
        for soldier in self.soldiers:
            # Only regular soldiers (not weekend-only and not exceptional with strict minimum)
            if (not soldier.is_weekend_only_soldier_flag and 
                soldier.name not in self.exceptional_minimums):
                
                minimum_base = self._calculate_regular_soldier_minimum(soldier)
                
                print(f"    👤 {soldier.name}: Minimum {minimum_base} base days")
                
                # Shortage variable and penalty (softer than for exceptional soldiers)
                regular_shortage_vars = self.variables.create_regular_shortage_variables(soldier.name, minimum_base)
                shortage_var = regular_shortage_vars['shortage']
                
                self.model.Add(shortage_var >= minimum_base - total_base_days[soldier.name])
                self.model.Add(shortage_var >= 0)
                
                # Half-strength penalty for regular soldiers
                penalty_value = self.penalty_no_work // SHORTAGE_BASE_PENALTY_DIVISOR
                self.solver.objective_terms.append(shortage_var * penalty_value)
                regular_soldiers_count += 1
        
        print(f"    👤 {regular_soldiers_count} regular soldiers defined with minimums")
    
    def _calculate_regular_soldier_minimum(self, soldier) -> int:
        """
        Calculates minimum work days for a regular soldier
        
        Args:
            soldier: The soldier object
            
        Returns:
            int: Minimum base days
        """
        constraints_ratio = calculate_constraints_ratio(soldier, self.total_days)
        minimum_base = BASE_MIN_REGULAR_DAYS_THRESHOLD
        
        # Dynamic adjustment based on constraint level
        if constraints_ratio < 0.1:  # Very available soldiers - more work
            minimum_base = int(BASE_MIN_REGULAR_DAYS_THRESHOLD * 1.5)
        elif constraints_ratio > 0.3:  # Heavily constrained soldiers - fewer requirements
            minimum_base = max(1, int(BASE_MIN_REGULAR_DAYS_THRESHOLD * 0.6))
        
        return minimum_base
    
    def validate_minimum_work_setup(self) -> bool:
        """
        Ensures minimum work settings are logical
        
        Returns:
            bool: True if settings are valid
        """
        # Check minimum for exceptional soldiers
        for soldier_name, minimum in self.exceptional_minimums.items():
            soldier = next((s for s in self.soldiers if s.name == soldier_name), None)
            if not soldier:
                print(f"❌ Error: Exceptional soldier {soldier_name} not found in list")
                return False
            
            available_days = calculate_available_days(soldier, self.total_days)
            if minimum > available_days:
                print(f"❌ Error: Minimum {minimum} for {soldier_name} is higher than available days ({available_days})")
                return False
        
        # Check weekend soldiers
        weekend_count = len([d for d in self.calendar if d.weekday() == 5])  # Saturdays
        if weekend_count < BASE_MIN_WEEKEND_DAYS_THRESHOLD:
            print(f"⚠️ Warning: Few weekends ({weekend_count}) for required minimum ({BASE_MIN_WEEKEND_DAYS_THRESHOLD})")
        
        print("✅ Minimum work settings are valid")
        return True
    
    def get_minimum_work_summary(self) -> dict:
        """
        Returns a summary of minimum work settings
        
        Returns:
            dict: Summary of settings
        """
        exceptional_soldiers = len(self.exceptional_minimums)
        weekend_soldiers = len([s for s in self.soldiers if s.is_weekend_only_soldier_flag])
        regular_soldiers = len([s for s in self.soldiers 
                              if not s.is_weekend_only_soldier_flag and 
                              s.name not in self.exceptional_minimums])
        
        return {
            'exceptional_soldiers_count': exceptional_soldiers,
            'weekend_soldiers_count': weekend_soldiers,
            'regular_soldiers_count': regular_soldiers,
            'base_min_regular_threshold': BASE_MIN_REGULAR_DAYS_THRESHOLD,
            'base_min_weekend_threshold': BASE_MIN_WEEKEND_DAYS_THRESHOLD,
            'penalty_no_work': self.penalty_no_work,
            'exceptional_minimums': self.exceptional_minimums.copy()
        }