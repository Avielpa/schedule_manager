"""
🚨 Daily Requirements Constraints - V9.0
Ensures a minimum number of soldiers are present each day
"""

from typing import TYPE_CHECKING
from ..config import WEEKEND_SHORTAGE_PENALTY_MULTIPLIER, WEEKEND_BONUS_VALUE

if TYPE_CHECKING:
    from ..solver import SmartScheduleSoldiers


class DailyRequirementsConstraints:
    """Class for managing daily soldier requirements"""
    
    def __init__(self, solver_instance: 'SmartScheduleSoldiers'):
        self.solver = solver_instance
        self.model = solver_instance.model
        self.soldiers = solver_instance.soldiers
        self.calendar = solver_instance.calendar
        self.variables = solver_instance.variables
        self.min_required_soldiers = solver_instance.min_required_soldiers_per_day
        self.penalty_shortage = solver_instance.penalty_shortage
        self.problem_analysis = solver_instance.problem_analysis
        
    def apply(self) -> None:
        """Applies daily requirements constraints"""
        print(f"💀 Adding critical daily soldier constraints (target: {self.min_required_soldiers})...")
        
        self._determine_flexibility()
        self._add_daily_soldiers_constraints()
        self._add_shortage_penalties()
        self._add_weekend_bonuses()
        
        print("✅ Daily requirements constraints applied successfully")
    
    def _determine_flexibility(self) -> None:
        """Determines the level of flexibility based on problem difficulty"""
        difficulty = self.problem_analysis['difficulty']
        
        # Dynamic minimum flexibility based on difficulty level
        flexibility_map = {
            "APOCALYPTIC": 3,
            "CATASTROPHIC": 3,
            "EXTREME": 2,
            "VERY_HARD": 1,
            "HARD": 1,
            "MEDIUM": 0,
            "EASY": 0
        }
        
        self.flexibility_range = flexibility_map.get(difficulty, 0)
        
        # Absolute minimum (e.g., 3 soldiers) to prevent completely empty days
        self.min_allowed_dynamic = max(3, self.min_required_soldiers - self.flexibility_range)
        self.max_allowed_dynamic = self.min_required_soldiers + self.flexibility_range
        
        print(f"    💡 Allowed range: {self.min_allowed_dynamic}-{self.max_allowed_dynamic} soldiers per day")
        print(f"    💀 Shortage penalty: {self.penalty_shortage:,} per missing soldier")
    
    def _add_daily_soldiers_constraints(self) -> None:
        """Adds hard constraints on the number of soldiers per day"""
        daily_soldiers_count = self.variables.get_daily_count_variables()
        
        constraints_added = 0
        
        for day in self.calendar:
            # Hard minimum constraint
            self.model.Add(daily_soldiers_count[day] >= self.min_allowed_dynamic)
            constraints_added += 1
            
            # 🆕 Hard maximum constraint - no more than required except in emergencies
            # max_allowed_strict = self.min_required_soldiers + 1  # Only one additional soldier maximum
            # self.model.Add(daily_soldiers_count[day] <= max_allowed_strict)
            # constraints_added += 1
        
        print(f"    📊 Added {constraints_added} daily minimum/maximum constraints")
        print(f"    🎯 Strict range: {self.min_allowed_dynamic}-{self.min_required_soldiers + 1} soldiers per day")
    
    def _add_shortage_penalties(self) -> None:
        """Adds penalties for soldier shortages"""
        daily_soldiers_count = self.variables.get_daily_count_variables()
        
        # Create shortage variables
        self.variables.create_shortage_variables(self.min_required_soldiers)
        shortage_variables = self.variables.shortage_variables
        
        penalties_added = 0
        
        for day in self.calendar:
            shortage_var = shortage_variables[day]
            
            # Define shortage variable
            self.model.Add(shortage_var >= self.min_required_soldiers - daily_soldiers_count[day])
            self.model.Add(shortage_var >= 0)
            
            # Day-adjusted penalty - less on weekends, more on weekdays
            weekday = day.weekday()
            is_weekend_day = weekday in [4, 5]  # Friday (4) and Saturday (5)
            
            if is_weekend_day:
                shortage_penalty_value = int(self.penalty_shortage * WEEKEND_SHORTAGE_PENALTY_MULTIPLIER)
            else:
                shortage_penalty_value = self.penalty_shortage
            
            # Add to objective function
            self.solver.objective_terms.append(shortage_var * shortage_penalty_value)
            penalties_added += 1
        
        print(f"    💀 Added {penalties_added} shortage penalties (with weekend adjustment)")
    
    def _add_weekend_bonuses(self) -> None:
        """Adds special bonuses for weekends with weekend soldiers"""
        base_assignment, _ = self.variables.get_assignment_variables()
        weekend_soldiers = [s for s in self.soldiers if s.is_weekend_only_soldier_flag]
        
        if not weekend_soldiers:
            print("    ℹ️ No weekend soldiers - skipping weekend bonuses")
            return
        
        weekend_bonus_vars = self.variables.create_weekend_bonus_variables(
            [s.name for s in weekend_soldiers]
        )
        
        bonuses_added = 0
        
        for day in self.calendar:
            weekday = day.weekday()
            is_weekend_day = weekday in [4, 5]  # Friday and Saturday
            
            if is_weekend_day and day in weekend_bonus_vars:
                weekend_contribution = sum(
                    base_assignment[(s.name, day)] for s in weekend_soldiers
                )
                
                weekend_bonus_var = weekend_bonus_vars[day]
                self.model.Add(weekend_bonus_var == weekend_contribution)
                
                # Strong bonus for weekend soldiers on weekends
                self.solver.objective_terms.append(weekend_bonus_var * WEEKEND_BONUS_VALUE)
                bonuses_added += 1
        
        print(f"    🏖️ Added {bonuses_added} weekend bonuses for {len(weekend_soldiers)} weekend soldiers")
    
    def validate_daily_requirements(self) -> bool:
        """
        Ensures daily requirements are logical
        
        Returns:
            bool: True if requirements are valid
        """
        total_available_soldiers = len(self.soldiers)
        
        if self.min_required_soldiers > total_available_soldiers:
            print(f"❌ Error: {self.min_required_soldiers} soldiers required but only {total_available_soldiers} available")
            return False
        
        if self.min_allowed_dynamic <= 0:
            print(f"❌ Error: Invalid dynamic minimum: {self.min_allowed_dynamic}")
            return False
        
        # Check general availability
        total_days = len(self.calendar)
        total_constraints = sum(len(s.raw_constraints) for s in self.soldiers)
        total_available_days = (total_available_soldiers * total_days) - total_constraints
        required_total_days = total_days * self.min_required_soldiers
        
        availability_ratio = total_available_days / required_total_days if required_total_days > 0 else 1.0
        
        if availability_ratio < 0.8:
            print(f"⚠️ Warning: Low availability ratio ({availability_ratio:.2f}) - problem might not be solvable")
        
        print(f"✅ Daily requirements are valid (availability ratio: {availability_ratio:.2f})")
        return True
    
    def get_daily_requirements_summary(self) -> dict:
        """
        Returns a summary of daily requirements
        
        Returns:
            dict: Summary of requirements
        """
        return {
            'min_required_soldiers': self.min_required_soldiers,
            'min_allowed_dynamic': self.min_allowed_dynamic,
            'max_allowed_dynamic': self.max_allowed_dynamic,
            'flexibility_range': self.flexibility_range,
            'penalty_shortage': self.penalty_shortage,
            'difficulty': self.problem_analysis['difficulty']
        }