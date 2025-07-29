"""
🔒 Advanced Constraints - V2.0
Contains advanced constraint types for complex scheduling scenarios
"""

from typing import TYPE_CHECKING, Dict, List, Set
from datetime import date, timedelta

if TYPE_CHECKING:
    from ..solver import SmartScheduleSoldiers


class AdvancedConstraints:
    """Class for managing advanced constraint types"""
    
    def __init__(self, solver_instance: 'SmartScheduleSoldiers'):
        self.solver = solver_instance
        self.model = solver_instance.model
        self.soldiers = solver_instance.soldiers
        self.calendar = solver_instance.calendar
        self.variables = solver_instance.variables
        
    def apply(self) -> None:
        """Applies all advanced constraints"""
        print("🔒 Adding advanced constraints...")
        
        self._add_team_coverage_constraints()
        self._add_skill_based_constraints()
        self._add_workload_distribution_constraints()
        self._add_rest_period_constraints()
        self._add_special_event_constraints()
        
        print("✅ Advanced constraints applied successfully")
    
    def _add_team_coverage_constraints(self) -> None:
        """
        Ensures that each team/unit has adequate coverage at all times
        """
        base_assignment, _ = self.variables.get_assignment_variables()
        
        # Group soldiers by team (if team information is available)
        teams = self._get_soldier_teams()
        
        if not teams:
            print("    ⚠️ No team information available, skipping team coverage constraints")
            return
        
        min_per_team = max(1, len(self.soldiers) // (len(teams) * 3))  # At least 1/3 of average team size
        
        for day in self.calendar:
            for team_name, team_soldiers in teams.items():
                if len(team_soldiers) > 1:  # Only apply if team has multiple soldiers
                    team_on_base = [
                        base_assignment[(soldier.name, day)] 
                        for soldier in team_soldiers
                    ]
                    
                    # At least min_per_team soldiers from each team should be on base
                    self.model.Add(sum(team_on_base) >= min_per_team)
        
        print(f"    👥 Team coverage constraints applied for {len(teams)} teams")
    
    def _add_skill_based_constraints(self) -> None:
        """
        Ensures that soldiers with critical skills are distributed properly
        """
        base_assignment, _ = self.variables.get_assignment_variables()
        
        # Identify critical skill soldiers (exceptional soldiers in our case)
        critical_soldiers = [s for s in self.soldiers if s.is_exceptional_output]
        
        if not critical_soldiers:
            print("    ⚠️ No critical skill soldiers identified")
            return
        
        # Ensure at least one critical soldier is on base each day
        for day in self.calendar:
            critical_on_base = [
                base_assignment[(soldier.name, day)] 
                for soldier in critical_soldiers
            ]
            
            if critical_on_base:  # Only if there are critical soldiers
                self.model.Add(sum(critical_on_base) >= 1)
        
        print(f"    🎯 Critical skill constraints applied for {len(critical_soldiers)} soldiers")
    
    def _add_workload_distribution_constraints(self) -> None:
        """
        Ensures fair distribution of workload among soldiers
        """
        total_base_days, _, _ = self.variables.get_summary_variables()
        
        # Calculate target workload per soldier
        total_days = len(self.calendar)
        total_required_days = total_days * self.solver.min_required_soldiers_per_day
        avg_days_per_soldier = total_required_days // len(self.soldiers)
        
        # Allow some flexibility in workload distribution
        min_workload = max(1, int(avg_days_per_soldier * 0.8))
        max_workload = int(avg_days_per_soldier * 1.2)
        
        workload_violations = 0
        for soldier in self.soldiers:
            # Don't apply strict limits to weekend-only soldiers
            if soldier.is_weekend_only_soldier_flag:
                continue
                
            soldier_base_days = total_base_days[soldier.name]
            
            # Soft constraints - add penalty terms rather than hard limits
            if hasattr(self.solver, 'objective_manager'):
                # Penalty for being below minimum workload
                below_min = self.model.NewIntVar(0, max_workload, f'below_min_{soldier.name}')
                self.model.Add(below_min >= min_workload - soldier_base_days)
                self.solver.objective_manager.add_term(below_min * 1000)
                
                # Penalty for being above maximum workload
                above_max = self.model.NewIntVar(0, max_workload, f'above_max_{soldier.name}')
                self.model.Add(above_max >= soldier_base_days - max_workload)
                self.solver.objective_manager.add_term(above_max * 1000)
                
                workload_violations += 1
        
        print(f"    ⚖️ Workload distribution constraints applied to {workload_violations} soldiers")
    
    def _add_rest_period_constraints(self) -> None:
        """
        Ensures adequate rest periods between intensive work periods
        """
        base_assignment, home_assignment = self.variables.get_assignment_variables()
        
        # Define what constitutes an intensive period (e.g., 3+ consecutive base days)
        intensive_period_length = 3
        required_rest_days = 1
        
        rest_constraints_added = 0
        
        for soldier in self.soldiers:
            # Skip weekend-only soldiers as they have different patterns
            if soldier.is_weekend_only_soldier_flag:
                continue
            
            # Look for patterns where soldier works intensive_period_length consecutive days
            for i in range(len(self.calendar) - intensive_period_length - required_rest_days):
                # Check if soldier works intensive period
                intensive_period = [
                    base_assignment[(soldier.name, self.calendar[i + j])]
                    for j in range(intensive_period_length)
                ]
                
                # If all days in intensive period are base days
                intensive_indicator = self.model.NewBoolVar(f'intensive_{soldier.name}_{i}')
                self.model.Add(sum(intensive_period) >= intensive_period_length).OnlyEnforceIf(intensive_indicator)
                self.model.Add(sum(intensive_period) < intensive_period_length).OnlyEnforceIf(intensive_indicator.Not())
                
                # Then next day(s) should be rest
                if i + intensive_period_length < len(self.calendar):
                    rest_day = home_assignment[(soldier.name, self.calendar[i + intensive_period_length])]
                    self.model.Add(rest_day == 1).OnlyEnforceIf(intensive_indicator)
                    rest_constraints_added += 1
        
        if rest_constraints_added > 0:
            print(f"    😴 Rest period constraints applied: {rest_constraints_added} constraints")
    
    def _add_special_event_constraints(self) -> None:
        """
        Handles special events that require specific soldier assignments
        """
        base_assignment, _ = self.variables.get_assignment_variables()
        
        # Get special events from database (if Event model has data)
        try:
            from ..models import Event
            special_events = Event.objects.filter(
                event_type__in=['TRAINING', 'HOLIDAY'],
                start_date__lte=max(self.calendar),
                end_date__gte=min(self.calendar)
            )
            
            events_processed = 0
            for event in special_events:
                # Find dates that overlap with our calendar
                event_dates = []
                current_date = max(event.start_date, min(self.calendar))
                end_date = min(event.end_date, max(self.calendar))
                
                while current_date <= end_date:
                    if current_date in self.calendar:
                        event_dates.append(current_date)
                    current_date += timedelta(days=1)
                
                if not event_dates:
                    continue
                
                # Apply event-specific constraints
                if event.min_required_soldiers:
                    # Ensure minimum soldiers for special events
                    for event_date in event_dates:
                        soldiers_on_base = [
                            base_assignment[(soldier.name, event_date)]
                            for soldier in self.soldiers
                        ]
                        self.model.Add(sum(soldiers_on_base) >= event.min_required_soldiers)
                
                # If specific soldiers are assigned to the event
                event_soldiers = event.soldiers.all()
                if event_soldiers:
                    for soldier_obj in event_soldiers:
                        # Find corresponding algorithm soldier
                        algo_soldier = next(
                            (s for s in self.soldiers if s.name == soldier_obj.name), 
                            None
                        )
                        if algo_soldier:
                            for event_date in event_dates:
                                # Force soldier to be on base during event
                                self.model.Add(
                                    base_assignment[(algo_soldier.name, event_date)] == 1
                                )
                
                events_processed += 1
            
            if events_processed > 0:
                print(f"    🎉 Special event constraints applied for {events_processed} events")
                
        except ImportError:
            print("    ⚠️ Event model not available, skipping special event constraints")
        except Exception as e:
            print(f"    ⚠️ Error processing special events: {e}")
    
    def _get_soldier_teams(self) -> Dict[str, List]:
        """
        Extract team information from soldiers (if available)
        
        Returns:
            Dictionary mapping team names to lists of soldiers
        """
        teams = {}
        
        # For now, create simple teams based on soldier properties
        # In a real system, this would come from a Team model or soldier.team field
        
        # Team 1: Regular soldiers
        regular_soldiers = [s for s in self.soldiers 
                          if not s.is_exceptional_output and not s.is_weekend_only_soldier_flag]
        if regular_soldiers:
            teams['Regular'] = regular_soldiers
        
        # Team 2: Exceptional soldiers
        exceptional_soldiers = [s for s in self.soldiers if s.is_exceptional_output]
        if exceptional_soldiers:
            teams['Exceptional'] = exceptional_soldiers
        
        # Team 3: Weekend soldiers
        weekend_soldiers = [s for s in self.soldiers if s.is_weekend_only_soldier_flag]
        if weekend_soldiers:
            teams['Weekend'] = weekend_soldiers
        
        return teams
    
    def add_custom_constraint(self, constraint_name: str, constraint_func) -> None:
        """
        Add a custom constraint function
        
        Args:
            constraint_name: Name of the constraint for logging
            constraint_func: Function that takes (model, variables, soldiers, calendar) and adds constraints
        """
        try:
            print(f"    🔧 Adding custom constraint: {constraint_name}")
            constraint_func(self.model, self.variables, self.soldiers, self.calendar)
            print(f"    ✅ Custom constraint '{constraint_name}' applied successfully")
        except Exception as e:
            print(f"    ❌ Error applying custom constraint '{constraint_name}': {e}")
    
    def validate_advanced_setup(self) -> bool:
        """
        Validates that advanced constraints are properly set up
        
        Returns:
            bool: True if setup is valid
        """
        # Check that we have the necessary variable types
        try:
            base_assignment, home_assignment = self.variables.get_assignment_variables()
            total_base_days, _, _ = self.variables.get_summary_variables()
            
            if not base_assignment or not home_assignment or not total_base_days:
                print("❌ Error: Required variables not available for advanced constraints")
                return False
            
            # Check that we have soldiers with different properties
            has_exceptional = any(s.is_exceptional_output for s in self.soldiers)
            has_weekend_only = any(s.is_weekend_only_soldier_flag for s in self.soldiers)
            
            if not has_exceptional and not has_weekend_only:
                print("⚠️ Warning: No special soldier types found, some advanced constraints may not apply")
            
            print("✅ Advanced constraints setup is valid")
            return True
            
        except Exception as e:
            print(f"❌ Error validating advanced constraints setup: {e}")
            return False


class CustomConstraintBuilder:
    """Helper class for building custom constraints"""
    
    @staticmethod
    def no_split_weekends(model, variables, soldiers, calendar):
        """
        Custom constraint: soldiers shouldn't have split weekends (Sat/Sun different status)
        """
        base_assignment, home_assignment = variables.get_assignment_variables()
        
        # Find all weekends in the calendar
        weekends = []
        for i, day in enumerate(calendar):
            if day.weekday() == 5:  # Saturday
                if i + 1 < len(calendar) and calendar[i + 1].weekday() == 6:  # Sunday follows
                    weekends.append((day, calendar[i + 1]))
        
        constraints_added = 0
        for soldier in soldiers:
            for saturday, sunday in weekends:
                sat_base = base_assignment[(soldier.name, saturday)]
                sun_base = base_assignment[(soldier.name, sunday)]
                
                # Both days should have the same status
                model.Add(sat_base == sun_base)
                constraints_added += 1
        
        print(f"        🏖️ No-split-weekend constraints added: {constraints_added}")
    
    @staticmethod
    def minimum_team_leaders(model, variables, soldiers, calendar):
        """
        Custom constraint: ensure at least one exceptional soldier (team leader) per day
        """
        base_assignment, _ = variables.get_assignment_variables()
        
        exceptional_soldiers = [s for s in soldiers if s.is_exceptional_output]
        if not exceptional_soldiers:
            print("        ⚠️ No exceptional soldiers found for team leader constraint")
            return
        
        for day in calendar:
            leaders_on_base = [
                base_assignment[(soldier.name, day)]
                for soldier in exceptional_soldiers
            ]
            model.Add(sum(leaders_on_base) >= 1)
        
        print(f"        👑 Team leader constraints added for {len(exceptional_soldiers)} leaders")
    
    @staticmethod
    def balanced_experience_levels(model, variables, soldiers, calendar):
        """
        Custom constraint: balance experienced and new soldiers each day
        """
        base_assignment, _ = variables.get_assignment_variables()
        
        # Assume exceptional soldiers are experienced
        experienced = [s for s in soldiers if s.is_exceptional_output]
        new_soldiers = [s for s in soldiers if not s.is_exceptional_output]
        
        if not experienced or not new_soldiers:
            print("        ⚠️ Cannot balance experience levels - need both experienced and new soldiers")
            return
        
        min_experienced_per_day = max(1, len(experienced) // 3)
        min_new_per_day = max(1, len(new_soldiers) // 3)
        
        for day in calendar:
            exp_on_base = [base_assignment[(s.name, day)] for s in experienced]
            new_on_base = [base_assignment[(s.name, day)] for s in new_soldiers]
            
            model.Add(sum(exp_on_base) >= min_experienced_per_day)
            model.Add(sum(new_on_base) >= min_new_per_day)
        
        print(f"        🎓 Experience balance constraints added")


# Example usage of custom constraints:
def apply_custom_constraints(advanced_constraints: AdvancedConstraints):
    """
    Example function showing how to apply custom constraints
    """
    builder = CustomConstraintBuilder()
    
    # Apply built-in custom constraints
    advanced_constraints.add_custom_constraint(
        "No Split Weekends", 
        builder.no_split_weekends
    )
    
    advanced_constraints.add_custom_constraint(
        "Minimum Team Leaders",
        builder.minimum_team_leaders
    )
    
    advanced_constraints.add_custom_constraint(
        "Balanced Experience Levels",
        builder.balanced_experience_levels
    )
    
    # Example of lambda custom constraint
    advanced_constraints.add_custom_constraint(
        "Maximum Two Consecutive Exceptional Soldiers",
        lambda model, variables, soldiers, calendar: _max_consecutive_exceptional(
            model, variables, soldiers, calendar, max_consecutive=2
        )
    )


def _max_consecutive_exceptional(model, variables, soldiers, calendar, max_consecutive=2):
    """Helper function for consecutive exceptional soldiers constraint"""
    base_assignment, _ = variables.get_assignment_variables()
    exceptional_soldiers = [s for s in soldiers if s.is_exceptional_output]
    
    if len(exceptional_soldiers) <= max_consecutive:
        return  # Constraint not applicable
    
    for i in range(len(calendar) - max_consecutive):
        for soldier in exceptional_soldiers:
            consecutive_days = [
                base_assignment[(soldier.name, calendar[i + j])]
                for j in range(max_consecutive + 1)
            ]
            # No more than max_consecutive consecutive days
            model.Add(sum(consecutive_days) <= max_consecutive)