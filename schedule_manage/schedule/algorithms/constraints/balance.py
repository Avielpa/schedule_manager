"""
⚖️ Balance and Fairness Constraints - V9.0
Ensures fair distribution of work days and prevents extreme deviations
"""

from typing import TYPE_CHECKING
from ..config import (
    FAIRNESS_PENALTY_BASE, FAIRNESS_PENALTY_HOME, 
    EXCESS_BASE_PENALTY_MULTIPLIER, SHORTAGE_BASE_PENALTY_DIVISOR
)

if TYPE_CHECKING:
    from ..solver import SmartScheduleSoldiers


class BalanceConstraints:
    """Class for managing balance and fairness"""
    
    def __init__(self, solver_instance: 'SmartScheduleSoldiers'):
        self.solver = solver_instance
        self.model = solver_instance.model
        self.soldiers = solver_instance.soldiers
        self.calendar = solver_instance.calendar
        self.variables = solver_instance.variables
        self.target_base_days = solver_instance.default_base_days_target
        self.target_home_days = solver_instance.default_home_days_target
        self.max_total_home_days = solver_instance.max_total_home_days
        self.max_weekend_base_days_per_soldier = solver_instance.max_weekend_base_days_per_soldier
        self.penalty_no_work = solver_instance.penalty_no_work
        
    def apply(self) -> None:
        """Applies balance and fairness constraints"""
        print("⚖️ Adding balance and fairness objectives...")
        
        self._add_base_days_balance_objectives()
        self._add_home_days_balance_objectives()
        self._add_maximum_limits_constraints()
        
        print("✅ Balance and fairness constraints applied successfully")
    
    def _add_base_days_balance_objectives(self) -> None:
        """Adds strict balance objectives for base days"""
        total_base_days, _, _ = self.variables.get_summary_variables()
        soldiers_names = [s.name for s in self.soldiers]
        
        # Create fairness variables
        fairness_vars = self.variables.create_fairness_variables(soldiers_names)
        self.variables.fairness_variables = fairness_vars  # Store for later access
        
        base_balance_penalties = 0
        
        for soldier in self.soldiers:
            soldier_fairness = fairness_vars[soldier.name]
            
            # 🚨 Hard constraint: do not exceed target by more than two days
            max_allowed_base = self.target_base_days + 2
            min_allowed_base = max(1, self.target_base_days - 2)
            
            # Hard constraint on allowed range
            self.model.Add(total_base_days[soldier.name] <= max_allowed_base)
            self.model.Add(total_base_days[soldier.name] >= min_allowed_base)
            
            # Calculate difference from target
            diff_base = soldier_fairness['diff_base']
            self.model.Add(diff_base == total_base_days[soldier.name] - self.target_base_days)
            
            # Excess base days (severe penalty)
            excess_base_days = soldier_fairness['excess_base']
            self.model.AddMaxEquality(excess_base_days, [diff_base, 0])
            
            # Critical penalty for excess base days (beyond target)
            excess_penalty = self.penalty_no_work * 5  # 5x penalty!
            self.solver.objective_terms.append(excess_base_days * excess_penalty)
            
            # Shortage of base days (medium penalty)
            shortage_base_days = soldier_fairness['shortage_base']
            self.model.AddMaxEquality(shortage_base_days, [-diff_base, 0])
            
            shortage_penalty = self.penalty_no_work // 2
            self.solver.objective_terms.append(shortage_base_days * shortage_penalty)
            
            base_balance_penalties += 1
            
            print(f"    🎯 {soldier.name}: Allowed range {min_allowed_base}-{max_allowed_base} base days")
        
        print(f"    📊 Added {base_balance_penalties} strict base days balance constraints")
    
    def _add_home_days_balance_objectives(self) -> None:
        """Adds balance objectives for home days"""
        _, total_home_days, _ = self.variables.get_summary_variables()
        soldiers_names = [s.name for s in self.soldiers]
        
        # Use already created fairness variables or create new ones
        if hasattr(self.variables, 'fairness_variables') and self.variables.fairness_variables:
            fairness_vars = self.variables.fairness_variables
        else:
            fairness_vars = self.variables.create_fairness_variables(soldiers_names)
            self.variables.fairness_variables = fairness_vars
        
        home_balance_penalties = 0
        
        for soldier in self.soldiers:
            soldier_fairness = fairness_vars[soldier.name]
            
            # Calculate difference from target
            diff_home = soldier_fairness['diff_home']
            self.model.Add(diff_home == total_home_days[soldier.name] - self.target_home_days)
            
            # Absolute value of deviation
            abs_diff_home = soldier_fairness['abs_diff_home']
            self.model.AddAbsEquality(abs_diff_home, diff_home)
            
            # Penalty for home days deviations
            self.solver.objective_terms.append(abs_diff_home * FAIRNESS_PENALTY_HOME)
            home_balance_penalties += 1
        
        print(f"    🏠 Added {home_balance_penalties} home days balance penalties")
    
    def _add_maximum_limits_constraints(self) -> None:
        """Adds maximum limit constraints"""
        _, total_home_days, total_weekend_base_days = self.variables.get_summary_variables()
        
        limits_added = 0
        
        # Maximum total home days constraint (if defined)
        if self.max_total_home_days is not None:
            for soldier in self.soldiers:
                self.model.Add(total_home_days[soldier.name] <= self.max_total_home_days)
                limits_added += 1
            
            print(f"    🏠 Max home days limited to {self.max_total_home_days} for {len(self.soldiers)} soldiers")
        
        # Maximum weekend base days constraint (if defined)
        if self.max_weekend_base_days_per_soldier is not None:
            weekend_limits = 0
            for soldier in self.soldiers:
                self.model.Add(total_weekend_base_days[soldier.name] <= self.max_weekend_base_days_per_soldier)
                weekend_limits += 1
            
            print(f"    🏖️ Max weekend base days limited to {self.max_weekend_base_days_per_soldier} for {weekend_limits} soldiers")
            limits_added += weekend_limits
        
        if limits_added == 0:
            print("    ℹ️ No additional maximum limits defined")
    
    def validate_balance_constraints(self) -> bool:
        """
        Ensures balance constraints are logical
        
        Returns:
            bool: True if constraints are valid
        """
        total_days = len(self.calendar)
        
        # Check base and home targets
        if self.target_base_days < 0:
            print(f"❌ Error: Negative base days target: {self.target_base_days}")
            return False
        
        if self.target_home_days < 0:
            print(f"❌ Error: Negative home days target: {self.target_home_days}")
            return False
        
        if self.target_base_days + self.target_home_days > total_days:
            print(f"⚠️ Warning: Sum of targets ({self.target_base_days + self.target_home_days}) is greater than calendar ({total_days})")
        
        # Check maximum limits
        if self.max_total_home_days is not None:
            if self.max_total_home_days > total_days:
                print(f"⚠️ Warning: Max home days ({self.max_total_home_days}) is greater than calendar ({total_days})")
            
            if self.max_total_home_days < self.target_home_days:
                print(f"⚠️ Warning: Max home days ({self.max_total_home_days}) is less than target ({self.target_home_days})")
        
        if self.max_weekend_base_days_per_soldier is not None:
            max_possible_weekends = len([d for d in self.calendar if d.weekday() == 5])  # Weekends
            if self.max_weekend_base_days_per_soldier > max_possible_weekends:
                print(f"⚠️ Warning: Max weekends ({self.max_weekend_base_days_per_soldier}) is greater than possible ({max_possible_weekends})")
        
        print("✅ Balance constraints are valid")
        return True
    
    def get_balance_summary(self) -> dict:
        """
        Returns a summary of balance settings
        
        Returns:
            dict: Summary of settings
        """
        soldiers_count = len(self.soldiers)
        total_days = len(self.calendar)
        max_possible_weekends = len([d for d in self.calendar if d.weekday() == 5])
        
        return {
            'target_base_days': self.target_base_days,
            'target_home_days': self.target_home_days,
            'max_total_home_days': self.max_total_home_days,
            'max_weekend_base_days_per_soldier': self.max_weekend_base_days_per_soldier,
            'total_soldiers': soldiers_count,
            'total_days': total_days,
            'max_possible_weekends': max_possible_weekends,
            'targets_sum': self.target_base_days + self.target_home_days,
            'penalty_settings': {
                'fairness_penalty_base': FAIRNESS_PENALTY_BASE,
                'fairness_penalty_home': FAIRNESS_PENALTY_HOME,
                'excess_base_multiplier': EXCESS_BASE_PENALTY_MULTIPLIER,
                'shortage_base_divisor': SHORTAGE_BASE_PENALTY_DIVISOR
            }
        }
    
    def calculate_theoretical_balance(self) -> dict:
        """
        Calculates ideal theoretical balance
        
        Returns:
            dict: Theoretical balance calculation
        """
        total_days = len(self.calendar)
        soldiers_count = len(self.soldiers)
        
        # Calculate total available days
        total_available_days = sum(
            total_days - len(soldier.raw_constraints) 
            for soldier in self.soldiers
        )
        
        # Calculate theoretical average
        avg_available_per_soldier = total_available_days / soldiers_count if soldiers_count > 0 else 0
        
        # Calculate total requirements
        min_required_total = getattr(self.solver, 'min_required_soldiers_per_day', 0) * total_days
        
        return {
            'total_days': total_days,
            'total_soldiers': soldiers_count,
            'total_available_days': total_available_days,
            'avg_available_per_soldier': avg_available_per_soldier,
            'min_required_total_days': min_required_total,
            'availability_ratio': total_available_days / min_required_total if min_required_total > 0 else 1.0,
            'theoretical_balance_possible': total_available_days >= min_required_total
        }