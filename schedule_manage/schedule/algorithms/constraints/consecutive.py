"""
⏰ Consecutive Days Constraints - V9.0
Handles maximum consecutive base and home days with flexibility for heavily constrained soldiers
"""

from typing import TYPE_CHECKING
from ..config import HEAVY_CONSTRAINTS_THRESHOLD, HOME_FLEXIBILITY_MULTIPLIER, BASE_FLEXIBILITY_MULTIPLIER
from ..utils import calculate_constraints_ratio

if TYPE_CHECKING:
    from ..solver import SmartScheduleSoldiers


class ConsecutiveConstraints:
    """Class for managing consecutive days constraints"""
    
    def __init__(self, solver_instance: 'SmartScheduleSoldiers'):
        self.solver = solver_instance
        self.model = solver_instance.model
        self.soldiers = solver_instance.soldiers
        self.calendar = solver_instance.calendar
        self.variables = solver_instance.variables
        self.max_consecutive_base_days = solver_instance.max_consecutive_base_days
        self.max_consecutive_home_days = solver_instance.max_consecutive_home_days
        self.total_days = len(solver_instance.calendar)
        
    def apply(self) -> None:
        """Applies consecutive days constraints"""
        print("⏰ Adding maximum consecutive days constraints...")
        
        for soldier in self.soldiers:
            self._add_soldier_consecutive_constraints(soldier)
        
        print("✅ Consecutive days constraints applied successfully")
    
    def _add_soldier_consecutive_constraints(self, soldier) -> None:
        """
        Adds consecutive days constraints for a specific soldier
        
        Args:
            soldier: The soldier object
        """
        base_assignment, home_assignment = self.variables.get_assignment_variables()
        
        # Calculate effective limits for the specific soldier
        effective_max_base, effective_max_home = self._calculate_effective_limits(soldier)
        
        print(f"    👤 {soldier.name}: Max {effective_max_base} base, {effective_max_home} home")
        
        # Maximum consecutive base days constraints
        self._add_consecutive_base_constraints(soldier, base_assignment, effective_max_base)
        
        # Maximum consecutive home days constraints
        self._add_consecutive_home_constraints(soldier, home_assignment, effective_max_home)
    
    def _calculate_effective_limits(self, soldier) -> tuple[int, int]:
        """
        Calculates effective limits for a specific soldier
        
        Args:
            soldier: The soldier object
            
        Returns:
            tuple: (effective_max_base, effective_max_home)
        """
        # Basic limits from soldier or global
        if hasattr(soldier, 'get_effective_max_consecutive_base_days'):
            effective_max_base = soldier.get_effective_max_consecutive_base_days(self.max_consecutive_base_days)
        else:
            effective_max_base = self.max_consecutive_base_days
            
        if hasattr(soldier, 'get_effective_max_consecutive_home_days'):
            effective_max_home = soldier.get_effective_max_consecutive_home_days(self.max_consecutive_home_days)
        else:
            effective_max_home = self.max_consecutive_home_days
        
        # Increased flexibility for heavily constrained soldiers
        constraints_ratio = calculate_constraints_ratio(soldier, self.total_days)
        
        if constraints_ratio > HEAVY_CONSTRAINTS_THRESHOLD:
            # Dynamic additions based on constraint percentage
            home_flexibility_add = int(self.max_consecutive_home_days * HOME_FLEXIBILITY_MULTIPLIER)
            base_flexibility_add = int(self.max_consecutive_base_days * BASE_FLEXIBILITY_MULTIPLIER)
            
            effective_max_home += home_flexibility_add
            effective_max_base += base_flexibility_add
            
            print(f"        💡 Increased flexibility due to heavy constraints (ratio: {constraints_ratio:.2f})")
        
        return effective_max_base, effective_max_home
    
    def _add_consecutive_base_constraints(self, soldier, base_assignment, effective_max_base: int) -> None:
        """
        Adds maximum consecutive base days constraints
        
        Args:
            soldier: The soldier object
            base_assignment: Base assignment variables
            effective_max_base: Effective maximum base days
        """
        num_days = len(self.calendar)
        constraints_added = 0
        
        # For every possible sequence that is too long
        for i in range(num_days - effective_max_base):
            base_segment = [
                base_assignment[(soldier.name, self.calendar[j])]
                for j in range(i, i + effective_max_base + 1)
            ]
            
            # Limit the sum to the allowed maximum
            self.model.Add(sum(base_segment) <= effective_max_base)
            constraints_added += 1
        
        if constraints_added > 0:
            print(f"        📏 Added {constraints_added} maximum consecutive base days constraints")
    
    def _add_consecutive_home_constraints(self, soldier, home_assignment, effective_max_home: int) -> None:
        """
        Adds maximum consecutive home days constraints
        
        Args:
            soldier: The soldier object
            home_assignment: Home assignment variables
            effective_max_home: Effective maximum home days
        """
        num_days = len(self.calendar)
        constraints_added = 0
        
        # For every possible sequence that is too long
        for i in range(num_days - effective_max_home):
            home_segment = [
                home_assignment[(soldier.name, self.calendar[j])]
                for j in range(i, i + effective_max_home + 1)
            ]
            
            # Limit the sum to the allowed maximum
            self.model.Add(sum(home_segment) <= effective_max_home)
            constraints_added += 1
        
        if constraints_added > 0:
            print(f"        🏠 Added {constraints_added} maximum consecutive home days constraints")
    
    def validate_consecutive_constraints(self) -> bool:
        """
        Ensures consecutive days constraints are logical
        
        Returns:
            bool: True if constraints are valid
        """
        if self.max_consecutive_base_days <= 0:
            print(f"❌ Error: Invalid maximum consecutive base days: {self.max_consecutive_base_days}")
            return False
        
        if self.max_consecutive_home_days <= 0:
            print(f"❌ Error: Invalid maximum consecutive home days: {self.max_consecutive_home_days}")
            return False
        
        # Check that limits are not too large relative to the entire calendar
        if self.max_consecutive_base_days > len(self.calendar):
            print(f"⚠️ Warning: Maximum base days ({self.max_consecutive_base_days}) is greater than calendar ({len(self.calendar)})")
        
        if self.max_consecutive_home_days > len(self.calendar):
            print(f"⚠️ Warning: Maximum home days ({self.max_consecutive_home_days}) is greater than calendar ({len(self.calendar)})")
        
        # Check logic between different limits
        min_base_block = getattr(self.solver, 'min_base_block_days', 3)
        if self.max_consecutive_base_days < min_base_block:
            print(f"❌ Error: Maximum base ({self.max_consecutive_base_days}) is less than minimum block ({min_base_block})")
            return False
        
        print("✅ Consecutive days constraints are valid")
        return True
    
    def get_consecutive_constraints_summary(self) -> dict:
        """
        Returns a summary of consecutive days constraints
        
        Returns:
            dict: Summary of constraints
        """
        soldiers_with_flexibility = []
        
        for soldier in self.soldiers:
            constraints_ratio = calculate_constraints_ratio(soldier, self.total_days)
            if constraints_ratio > HEAVY_CONSTRAINTS_THRESHOLD:
                soldiers_with_flexibility.append({
                    'name': soldier.name,
                    'constraints_ratio': constraints_ratio,
                    'gets_flexibility': True
                })
        
        return {
            'max_consecutive_base_days': self.max_consecutive_base_days,
            'max_consecutive_home_days': self.max_consecutive_home_days,
            'heavy_constraints_threshold': HEAVY_CONSTRAINTS_THRESHOLD,
            'home_flexibility_multiplier': HOME_FLEXIBILITY_MULTIPLIER,
            'base_flexibility_multiplier': BASE_FLEXIBILITY_MULTIPLIER,
            'soldiers_with_flexibility': soldiers_with_flexibility,
            'total_soldiers': len(self.soldiers)
        }
    
    def get_soldier_effective_limits(self, soldier_name: str) -> dict:
        """
        Returns the effective limits for a specific soldier
        
        Args:
            soldier_name: Soldier's name
            
        Returns:
            dict: The effective limits or None if the soldier is not found
        """
        soldier = next((s for s in self.soldiers if s.name == soldier_name), None)
        if not soldier:
            return None
        
        effective_max_base, effective_max_home = self._calculate_effective_limits(soldier)
        constraints_ratio = calculate_constraints_ratio(soldier, self.total_days)
        
        return {
            'soldier_name': soldier_name,
            'effective_max_base_days': effective_max_base,
            'effective_max_home_days': effective_max_home,
            'original_max_base_days': self.max_consecutive_base_days,
            'original_max_home_days': self.max_consecutive_home_days,
            'constraints_ratio': constraints_ratio,
            'has_flexibility': constraints_ratio > HEAVY_CONSTRAINTS_THRESHOLD
        }