"""
🚀 Main Solution Engine - V9.0 Improved
The main class that manages the entire scheduling problem solving process
with error protection for variable creation
"""

from datetime import date
from typing import List, Dict, Optional, Union, Tuple, Any
from ortools.sat.python import cp_model

# Import local modules
from .config import (
    DEFAULT_DEATH_PENALTY_ONE_DAY_BLOCK, DEFAULT_DEATH_PENALTY_SHORTAGE,
    DEFAULT_DEATH_PENALTY_NO_WORK, DEFAULT_HEAVY_PENALTY_CONSTRAINTS,
    DEFAULT_PENALTY_LONG_BLOCK, DEFAULT_CRITICAL_PENALTY_LONG_BLOCK,
    COLOR_BASE, COLOR_HOME, COLOR_WEEKEND, COLOR_HEADER, COLOR_SUMMARY
)
from .utils import (
    parse_date, generate_calendar, validate_config, validate_soldiers_list,
    print_solver_info, print_solution_summary
)
from .analysis import (
    ProblemAnalyzer, ParameterAdapter, ExceptionalSoldiersAnalyzer,
    analyze_soldiers_specific_parameters
)
from .variables import ModelVariables
from .objective import ObjectiveManager
from .constraints import apply_all_constraints


class SmartScheduleSoldiers:
    """
    💎 Dynamic Block Killer - Version 9.0 Modular Improved
    
    The main class for solving soldier scheduling problems with:
    ✅ Full modularity
    ✅ Flexibility and dynamic adaptation
    ✅ Handling extreme problems
    ✅ Preventing one-day blocks
    ✅ Balance and fairness
    ✅ Error protection
    """

    def __init__(self,
                 soldiers: List,
                 start_date: Union[str, date],
                 end_date: Union[str, date],
                 default_base_days_target: int,
                 default_home_days_target: int,
                 max_consecutive_base_days: int,
                 max_consecutive_home_days: int,
                 min_base_block_days: int,
                 min_required_soldiers_per_day: int,
                 max_total_home_days: Optional[int] = None,
                 max_weekend_base_days_per_soldier: Optional[int] = None,
                 flexible_daily_requirement: bool = False,
                 # Penalty parameters
                 penalty_one_day_block: int = DEFAULT_DEATH_PENALTY_ONE_DAY_BLOCK,
                 penalty_shortage: int = DEFAULT_DEATH_PENALTY_SHORTAGE,
                 penalty_no_work: int = DEFAULT_DEATH_PENALTY_NO_WORK,
                 penalty_constraints: int = DEFAULT_HEAVY_PENALTY_CONSTRAINTS,
                 penalty_long_block: int = DEFAULT_PENALTY_LONG_BLOCK,
                 critical_penalty_long_block: int = DEFAULT_CRITICAL_PENALTY_LONG_BLOCK):

        print("🚀 Initializing scheduling engine V9.0...")
        
        # Basic input validation
        validate_soldiers_list(soldiers)
        
        # Validate and clean soldier names
        self.soldiers = self._validate_and_clean_soldiers(soldiers)
        
        # Basic parameters
        self.start_date = parse_date(start_date)
        self.end_date = parse_date(end_date)
        self.calendar = generate_calendar(self.start_date, self.end_date)
        
        # Store original parameters
        self.original_default_base_days_target = default_base_days_target
        self.original_default_home_days_target = default_home_days_target
        self.original_min_required_soldiers_per_day = min_required_soldiers_per_day
        
        # Constraint parameters
        self.max_consecutive_base_days = max_consecutive_base_days
        self.max_consecutive_home_days = max_consecutive_home_days
        self.min_base_block_days = max(3, min_base_block_days)
        self.max_total_home_days = max_total_home_days
        self.max_weekend_base_days_per_soldier = max_weekend_base_days_per_soldier
        self.flexible_daily_requirement = flexible_daily_requirement

        # Penalty parameters
        self.penalty_one_day_block = penalty_one_day_block
        self.penalty_shortage = penalty_shortage
        self.penalty_no_work = penalty_no_work
        self.penalty_constraints = penalty_constraints
        self.penalty_long_block = penalty_long_block
        self.critical_penalty_long_block = critical_penalty_long_block

        # Dynamic parameters (will be adapted based on analysis)
        self.default_base_days_target = default_base_days_target
        self.default_home_days_target = default_home_days_target
        self.min_required_soldiers_per_day = min_required_soldiers_per_day

        # Core objects
        self.model = cp_model.CpModel()
        self.solver = cp_model.CpSolver()
        self.variables: Optional[ModelVariables] = None
        self.objective_manager: Optional[ObjectiveManager] = None

        # Analysis and planning
        try:
            self._perform_analysis_and_adaptation()
        except Exception as e:
            print(f"❌ Error in problem analysis: {e}")
            raise
        
        # Create variable and objective managers
        try:
            self.variables = ModelVariables(self.model, self.soldiers, self.calendar)
            self.objective_manager = ObjectiveManager(self)
            print("✅ System managers created successfully")
        except Exception as e:
            print(f"❌ Error creating system managers: {e}")
            raise
        
        # List for collecting objective function variables (backward compatibility)
        self.objective_terms = []

        # Print initial information
        self._print_initialization_info()
        
        print("🎯 Initialization completed successfully")

    def _validate_and_clean_soldiers(self, soldiers: List) -> List:
        """Validates and cleans the list of soldiers"""
        cleaned_soldiers = []
        
        for i, soldier in enumerate(soldiers):
            # Check mandatory fields
            if not hasattr(soldier, 'name'):
                print(f"⚠️ Soldier at position {i} is missing name field, adding default name")
                soldier.name = f"Soldier_{i}"
            
            if not soldier.name or not soldier.name.strip():
                print(f"⚠️ Soldier with empty name at position {i}, adding default name")
                soldier.name = f"Soldier_{i}"
            
            # Clean soldier name
            original_name = soldier.name
            soldier.name = soldier.name.strip()
            
            if original_name != soldier.name:
                print(f"🔧 Soldier name cleaned: '{original_name}' -> '{soldier.name}'")
            
            # Check additional fields
            if not hasattr(soldier, 'raw_constraints'):
                print(f"⚠️ Soldier {soldier.name} is missing raw_constraints, adding empty set")
                soldier.raw_constraints = set()
            
            if not hasattr(soldier, 'is_exceptional_output'):
                soldier.is_exceptional_output = False
            
            if not hasattr(soldier, 'is_weekend_only_soldier_flag'):
                soldier.is_weekend_only_soldier_flag = False
            
            cleaned_soldiers.append(soldier)
        
        print(f"✅ {len(cleaned_soldiers)} soldiers cleaned")
        return cleaned_soldiers

    @classmethod
    def from_json_config(cls, soldiers: List, config: Dict):
        """Creates an instance from a JSON configuration"""
        validate_config(config)
        
        return cls(
            soldiers=soldiers,
            start_date=config['start_date'],
            end_date=config['end_date'],
            default_base_days_target=config['default_base_days_target'],
            default_home_days_target=config['default_home_days_target'],
            max_consecutive_base_days=config['max_consecutive_base_days'],
            max_consecutive_home_days=config['max_consecutive_home_days'],
            min_base_block_days=config['min_base_block_days'],
            min_required_soldiers_per_day=config['min_required_soldiers_per_day'],
            max_total_home_days=config.get('max_total_home_days'),
            max_weekend_base_days_per_soldier=config.get('max_weekend_base_days_per_soldier'),
            flexible_daily_requirement=config.get('flexible_daily_requirement', False)
        )

    def _perform_analysis_and_adaptation(self) -> None:
        """Performs problem analysis and parameter adaptation"""
        print("🔍 Performing advanced analysis...")
        
        # Problem analysis
        analyzer = ProblemAnalyzer(
            self.soldiers, self.calendar, self.original_min_required_soldiers_per_day
        )
        self.problem_analysis = analyzer.perform_extreme_analysis()
        self.soldiers_by_availability = analyzer.rank_soldiers_by_availability()
        
        # Parameter adaptation
        adapter = ParameterAdapter(self.problem_analysis, {
            'base_days_target': self.original_default_base_days_target,
            'home_days_target': self.original_default_home_days_target,
            'min_required_soldiers': self.original_min_required_soldiers_per_day
        })
        adapted_params = adapter.adapt_parameters_for_difficulty()
        
        # Update parameters
        self.default_base_days_target = adapted_params['base_days_target']
        self.default_home_days_target = adapted_params['home_days_target']
        self.min_required_soldiers_per_day = adapted_params['min_required_soldiers']
        if 'flexible_daily_requirement' in adapted_params:
            self.flexible_daily_requirement = adapted_params['flexible_daily_requirement']
        
        # Calculate minimums for exceptional soldiers
        exceptional_analyzer = ExceptionalSoldiersAnalyzer(self.soldiers, self.calendar)
        self.exceptional_minimums = exceptional_analyzer.calculate_exceptional_minimums()
        
        # Analyze specific parameters for soldiers
        analyze_soldiers_specific_parameters(
            self.soldiers, self.max_consecutive_home_days,
            self.default_home_days_target, len(self.calendar)
        )
        
        print("✅ Analysis completed successfully")

    def _print_initialization_info(self) -> None:
        """Prints initial solver information"""
        penalty_config = {
            'one_day': self.penalty_one_day_block,
            'shortage': self.penalty_shortage,
            'no_work': self.penalty_no_work,
            'long_block': self.penalty_long_block,
            'critical_long': self.critical_penalty_long_block
        }
        
        print_solver_info(
            self.start_date, self.end_date, len(self.calendar),
            penalty_config, self.problem_analysis['difficulty'],
            self.min_required_soldiers_per_day
        )

    def solve(self) -> Optional[Tuple[Optional[Dict], int]]:
        """Runs the CP solver and returns the solution and status"""
        try:
            print("🔧 Preparing the model for solving...")
            
            # 🟢 Create all variables first - very important!
            if not self.variables:
                raise ValueError("❌ Variable manager not created")
            
            try:
                self.variables.create_all_variables()
                print("✅ All variables created successfully")
            except Exception as var_error:
                print(f"❌ Error creating variables: {var_error}")
                raise
            
            # Apply all constraints and objectives
            try:
                apply_all_constraints(self)
                print("✅ All constraints applied successfully")
            except Exception as constraints_error:
                print(f"❌ Error applying constraints: {constraints_error}")
                raise
            
            # Define objective function
            try:
                if hasattr(self, 'objective_terms') and self.objective_terms:
                    # Backward compatibility - if there is an old list
                    if self.objective_manager:
                        for term in self.objective_terms:
                            self.objective_manager.add_term(term)
                    self.objective_manager.set_objective()
                else:
                    self.objective_manager.set_objective()
                print("✅ Objective function defined successfully")
            except Exception as objective_error:
                print(f"❌ Error defining objective function: {objective_error}")
                raise
            
            # Validation before solving
            if not self._validate_before_solving():
                return None, cp_model.UNKNOWN
            
            print("🚀 Running the solver...")
            
            # Set solver parameters
            self.solver.parameters.max_time_in_seconds = 300
            
            # Run the solution
            status = self.solver.Solve(self.model)
            
            return self._process_solution(status)
            
        except Exception as e:
            print(f"❌ Error in solution: {e}")
            import traceback
            traceback.print_exc()
            return None, cp_model.UNKNOWN

    def _validate_before_solving(self) -> bool:
        """Ensures the model is valid before solving"""
        if not self.variables:
            print("❌ Error: Variables not created")
            return False
        
        if not self.objective_manager:
            print("❌ Error: Objective manager not created")
            return False
        
        if not self.objective_manager.validate_objective():
            return False
        
        # Check basic variable creation
        try:
            base_assignment, home_assignment = self.variables.get_assignment_variables()
            if not base_assignment or not home_assignment:
                print("❌ Error: Basic assignment variables not created")
                return False
        except Exception as e:
            print(f"❌ Error checking variables: {e}")
            return False
        
        # Print debug information
        try:
            debug_info = self.variables.debug_variables_info()
            print(f"🔍 Debug: {debug_info['total_assignment_variables']} assignment variables, "
                  f"{debug_info['soldiers_count']} soldiers, {debug_info['calendar_days']} days")
        except Exception as debug_error:
            print(f"⚠️ Could not get debug information: {debug_error}")
        
        return True

    def _process_solution(self, status: int) -> Tuple[Optional[Dict], int]:
        """Processes the solution and returns the results"""
        if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
            print(f"✅ Solution found! Status: {self.solver.StatusName(status)}")
            print(f"💰 Total cost: {self.solver.ObjectiveValue():,.0f}")
            
            solution_data = self._extract_solution_data()
            print_solution_summary(solution_data)
            
            return solution_data, status
        else:
            print(f"❌ No solution found. Status: {self.solver.StatusName(status)}")
            if status == cp_model.INFEASIBLE:
                print("💡 Reason: Constraints are contradictory. Further relaxation of constraints may be needed.")
            return None, status

    def _extract_solution_data(self) -> Dict:
        """Extracts solution data from the model"""
        solution_data = {}
        
        try:
            base_assignment, home_assignment = self.variables.get_assignment_variables()
            total_base_days, total_home_days, total_weekend_base_days = self.variables.get_summary_variables()
            daily_soldiers_count = self.variables.get_daily_count_variables()
            
            # Soldier data
            for soldier in self.soldiers:
                solution_data[soldier.name] = {
                    'schedule': [],
                    'total_base_days': self.solver.Value(total_base_days[soldier.name]),
                    'total_home_days': self.solver.Value(total_home_days[soldier.name]),
                    'total_weekend_base_days': self.solver.Value(total_weekend_base_days[soldier.name])
                }
                
                # Daily schedule
                for day in self.calendar:
                    key = (soldier.name, day)
                    
                    if key in base_assignment:
                        if self.solver.Value(base_assignment[key]):
                            status = 'Base'
                        else:
                            status = 'Home'
                    else:
                        print(f"⚠️ Warning: Key {key} not found in assignment variables")
                        status = 'Home'  # Default
                    
                    solution_data[soldier.name]['schedule'].append({
                        'date': day.isoformat(),
                        'status': status
                    })
            
            # Daily count
            daily_counts = {}
            for day in self.calendar:
                if day in daily_soldiers_count:
                    daily_counts[day.isoformat()] = self.solver.Value(daily_soldiers_count[day])
                else:
                    print(f"⚠️ Warning: Day {day} not found in daily count variables")
                    daily_counts[day.isoformat()] = 0
            
            solution_data['daily_soldiers_count'] = daily_counts
            
        except Exception as e:
            print(f"❌ Error extracting solution data: {e}")
            raise
        
        return solution_data

    def export_to_excel(self, solution_data: Dict, output_filepath: str = "schedule.xlsx") -> None:
        """Exports the solution to Excel"""
        from .exporters.excel import ExcelExporter
        
        exporter = ExcelExporter(self.calendar, self.soldiers)
        exporter.export(solution_data, output_filepath)

    def export_to_json(self, solution_data: Dict, output_filepath: str = "schedule.json") -> None:
        """Exports the solution to JSON"""
        from .exporters.json import JsonExporter
        
        exporter = JsonExporter(self.calendar, self.soldiers)
        exporter.export(solution_data, output_filepath)

    def run_solver_and_export(self, excel_path: str = "schedule.xlsx", 
                             json_path: str = "schedule.json") -> Optional[Dict]:
        """Runs the solver and exports to various formats"""
        solution, status = self.solve()
        
        if solution:
            print("📋 Exporting results...")
            self.export_to_excel(solution, excel_path)
            self.export_to_json(solution, json_path)
            print("✅ Export completed successfully")
        else:
            print("❌ Cannot export - no solution found")
        
        return solution

    def get_solver_statistics(self) -> Dict[str, Any]:
        """Returns detailed solver statistics"""
        stats = {
            'problem_info': {
                'total_days': len(self.calendar),
                'total_soldiers': len(self.soldiers),
                'difficulty': self.problem_analysis['difficulty'],
                'availability_ratio': self.problem_analysis['availability_ratio']
            },
            'parameters': {
                'target_base_days': self.default_base_days_target,
                'target_home_days': self.default_home_days_target,
                'min_required_soldiers': self.min_required_soldiers_per_day,
                'max_consecutive_base': self.max_consecutive_base_days,
                'max_consecutive_home': self.max_consecutive_home_days,
                'min_base_block': self.min_base_block_days
            },
            'penalties': {
                'one_day_block': self.penalty_one_day_block,
                'shortage': self.penalty_shortage,
                'no_work': self.penalty_no_work,
                'long_block': self.penalty_long_block,
                'critical_long_block': self.critical_penalty_long_block
            },
            'analysis': self.problem_analysis,
            'exceptional_minimums': self.exceptional_minimums,
            'objective_summary': self.objective_manager.get_objective_summary() if self.objective_manager else {}
        }
        
        # Add variable information if available
        if self.variables:
            try:
                stats['variables_info'] = self.variables.debug_variables_info()
            except Exception as e:
                stats['variables_error'] = str(e)
        
        return stats

    def validate_solution(self, solution_data: Dict) -> Dict[str, Any]:
        """Validates the correctness of the solution"""
        if not solution_data:
            return {'valid': False, 'errors': ['No solution data']}
        
        errors = []
        warnings = []
        
        # Check soldiers
        for soldier in self.soldiers:
            if soldier.name not in solution_data:
                errors.append(f"Soldier missing from solution: {soldier.name}")
                continue
            
            soldier_data = solution_data[soldier.name]
            
            # Check schedule length
            if len(soldier_data['schedule']) != len(self.calendar):
                errors.append(f"Incorrect schedule length for {soldier.name}")
            
            # Check personal constraints
            for day_data in soldier_data['schedule']:
                day = parse_date(day_data['date'])
                if day in soldier.raw_constraints and day_data['status'] == 'Base':
                    errors.append(f"Personal constraint violation: {soldier.name} on {day.isoformat()}")
        
        # Check daily requirements
        if 'daily_soldiers_count' in solution_data:
            for day_str, count in solution_data['daily_soldiers_count'].items():
                if count < self.min_required_soldiers_per_day:
                    warnings.append(f"Soldier shortage on {day_str}: {count} instead of {self.min_required_soldiers_per_day}")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }