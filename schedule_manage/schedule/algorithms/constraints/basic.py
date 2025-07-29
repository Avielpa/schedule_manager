"""
🔒 Basic Constraints - V9.0
Contains the most basic hard constraints of the system
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..solver import SmartScheduleSoldiers


class BasicConstraints:
    """Class for managing basic hard constraints"""
    
    def __init__(self, solver_instance: 'SmartScheduleSoldiers'):
        self.solver = solver_instance
        self.model = solver_instance.model
        self.soldiers = solver_instance.soldiers
        self.calendar = solver_instance.calendar
        self.variables = solver_instance.variables
        
    def apply(self) -> None:
        """Applies all basic constraints"""
        print("🔒 Adding basic constraints...")
        
        self._add_presence_constraints()
        self._add_personal_constraints()
        self._add_summary_calculation_constraints()
        
        print("✅ Basic constraints applied successfully")
    
    def _add_presence_constraints(self) -> None:
        """
        Hard constraint: a soldier must be either on base or at home (not both and not neither)
        This is the most basic constraint in the system
        """
        base_assignment, home_assignment = self.variables.get_assignment_variables()
        
        for soldier in self.soldiers:
            for day in self.calendar:
                key = (soldier.name, day)
                
                # Hard constraint: soldier must be on base or at home (exactly one of them)
                self.model.Add(base_assignment[key] + home_assignment[key] == 1)
    
    def _add_personal_constraints(self) -> None:
        """
        Hard constraint: personal constraints of soldiers
        If a soldier has a constraint on a specific day, they must be at home
        """
        base_assignment, home_assignment = self.variables.get_assignment_variables()
        
        personal_constraints_count = 0
        
        for soldier in self.soldiers:
            soldier_constraints = 0
            
            for day in self.calendar:
                key = (soldier.name, day)
                
                # Hard constraint: personal constraints - soldier at home if there is a constraint
                if day in soldier.raw_constraints:
                    self.model.Add(base_assignment[key] == 0)
                    self.model.Add(home_assignment[key] == 1)
                    soldier_constraints += 1
                    personal_constraints_count += 1
            
            if soldier_constraints > 0:
                print(f"    🚫 {soldier.name}: {soldier_constraints} personal constraints")
        
        print(f"    📊 Total {personal_constraints_count} personal constraints applied")
    
    def _add_summary_calculation_constraints(self) -> None:
        """
        Summary calculation constraints - links daily variables to summaries
        """
        base_assignment, home_assignment = self.variables.get_assignment_variables()
        total_base_days, total_home_days, total_weekend_base_days = self.variables.get_summary_variables()
        daily_soldiers_count = self.variables.get_daily_count_variables()
        
        print("    📊 Adding summary calculation constraints...")
        
        # Individual soldier summaries
        for soldier in self.soldiers:
            # Total base days for soldier
            self.model.Add(
                total_base_days[soldier.name] == 
                sum(base_assignment[(soldier.name, day)] for day in self.calendar)
            )
            
            # Total home days for soldier
            self.model.Add(
                total_home_days[soldier.name] == 
                sum(home_assignment[(soldier.name, day)] for day in self.calendar)
            )
            
            # Total weekend base days for soldier
            weekend_assignments = [
                base_assignment[(soldier.name, day)] 
                for day in self.calendar 
                if day.weekday() == 5  # Saturdays only
            ]
            
            if weekend_assignments:
                self.model.Add(
                    total_weekend_base_days[soldier.name] == sum(weekend_assignments)
                )
            else:
                self.model.Add(total_weekend_base_days[soldier.name] == 0)
        
        # Daily count of soldiers on base
        for day in self.calendar:
            self.model.Add(
                daily_soldiers_count[day] == 
                sum(base_assignment[(s.name, day)] for s in self.soldiers)
            )
    
    def validate_basic_setup(self) -> bool:
        """
        Ensures the basic setup is valid
        
        Returns:
            bool: True if the setup is valid
        """
        # Check for existence of basic variables
        base_assignment, home_assignment = self.variables.get_assignment_variables()
        
        if not base_assignment or not home_assignment:
            print("❌ Error: Basic assignment variables not created")
            return False
        
        # Check for consistency between soldiers and calendar
        expected_vars = len(self.soldiers) * len(self.calendar)
        if len(base_assignment) != expected_vars or len(home_assignment) != expected_vars:
            print(f"❌ Error: Number of variables mismatch ({len(base_assignment)}, {len(home_assignment)} instead of {expected_vars})")
            return False
        
        print("✅ Basic setup is valid")
        return True