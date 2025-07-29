"""
💎 Algorithms Module - DynamicBlockCrusher V9.0 Modular
Advanced solution engine for soldier scheduling problems with a modular architecture

🚀 Key Capabilities:
✅ Solving complex scheduling problems
✅ Handling exceptional and weekend-only soldiers
✅ Preventing one-day blocks
✅ Balance and fairness in work distribution
✅ Dynamic adaptation to difficulty level
✅ Export to Excel and JSON
✅ Modular and flexible architecture

📦 Components:
- solver: The main engine
- constraints: Constraint modules
- analysis: Problem and dynamic parameter analysis
- variables: Model variable management
- objective: Objective function
- exporters: Result export
- utils: Utility functions
- config: Settings and parameters
"""

from .solver import SmartScheduleSoldiers
from .utils import parse_date, generate_calendar, validate_config, validate_soldiers_list
from .analysis import ProblemAnalyzer, ParameterAdapter, ExceptionalSoldiersAnalyzer
from .variables import ModelVariables
from .objective import ObjectiveManager
from .exporters import ExcelExporter, JsonExporter, get_exporter, export_to_format

# Version and information
__version__ = "9.0.0"
__algorithm_name__ = "DynamicBlockCrusher"
__architecture__ = "Modular"

# Main import for external use
__all__ = [
    # Main class
    'SmartScheduleSoldiers',
    
    # Core classes
    'ProblemAnalyzer',
    'ParameterAdapter', 
    'ExceptionalSoldiersAnalyzer',
    'ModelVariables',
    'ObjectiveManager',
    
    # Exporters
    'ExcelExporter',
    'JsonExporter',
    'get_exporter',
    'export_to_format',
    
    # Utility functions
    'parse_date',
    'generate_calendar',
    'validate_config',
    'validate_soldiers_list',
    
    # Shortcut functions
    'create_solver',
    'solve_schedule_problem',
    'quick_solve_and_export',
    
    # System information
    '__version__',
    '__algorithm_name__',
    '__architecture__'
]

print(f"ALGORITHMS_MODULE_LOADED - VERSION {__version__} - {__algorithm_name__.upper()}_{__architecture__.upper()}")


def create_solver(soldiers, start_date, end_date, **kwargs) -> solver.SmartScheduleSoldiers:
    """
    Shortcut function to create a solver with default settings
    
    Args:
        soldiers: List of soldiers
        start_date: Start date
        end_date: End date
        **kwargs: Additional parameters
        
    Returns:
        SmartScheduleSoldiers: Solver instance
        
    Example:
        >>> solver = create_solver(soldiers, "2025-01-01", "2025-01-31",
        ...                       default_base_days_target=15,
        ...                       min_required_soldiers_per_day=8)
    """
    # Default parameters
    default_params = {
        'default_base_days_target': 15,
        'default_home_days_target': 15, 
        'max_consecutive_base_days': 10,
        'max_consecutive_home_days': 7,
        'min_base_block_days': 3,
        'min_required_soldiers_per_day': 6
    }
    
    # Update with passed parameters
    default_params.update(kwargs)
    
    return solver.SmartScheduleSoldiers(
        soldiers=soldiers,
        start_date=start_date,
        end_date=end_date,
        **default_params
    )


def solve_schedule_problem(soldiers, start_date, end_date, **kwargs) -> tuple:
    """
    Solves the scheduling problem with default settings
    
    Args:
        soldiers: List of soldiers
        start_date: Start date  
        end_date: End date
        **kwargs: Additional parameters
        
    Returns:
        tuple: (solution_data, status, solver_instance)
        
    Example:
        >>> solution, status, solver = solve_schedule_problem(
        ...     soldiers, "2025-01-01", "2025-01-31",
        ...     min_required_soldiers_per_day=8
        ... )
    """
    solver = create_solver(soldiers, start_date, end_date, **kwargs)
    solution, status = solver.solve()
    return solution, status, solver


def quick_solve_and_export(soldiers, start_date, end_date, 
                          excel_path="schedule.xlsx", json_path="schedule.json",
                          **kwargs) -> dict:
    """
    Solves and exports in one operation
    
    Args:
        soldiers: List of soldiers
        start_date: Start date
        end_date: End date
        excel_path: Excel export path
        json_path: JSON export path
        **kwargs: Additional parameters
        
    Returns:
        dict: Solution and export results
        
    Example:
        >>> result = quick_solve_and_export(
        ...     soldiers, "2025-01-01", "2025-01-31",
        ...     excel_path="my_schedule.xlsx",
        ...     min_required_soldiers_per_day=8
        ... )
    """
    print(f"🚀 Running quick solution with export...")
    
    try:
        # Solution
        solution, status, solver = solve_schedule_problem(soldiers, start_date, end_date, **kwargs)
        
        result = {
            'success': solution is not None,
            'status': status,
            'solution': solution,
            'exported_files': []
        }
        
        if solution:
            # Export
            if excel_path:
                solver.export_to_excel(solution, excel_path)
                result['exported_files'].append(excel_path)
            
            if json_path:
                solver.export_to_json(solution, json_path)
                result['exported_files'].append(json_path)
            
            # Statistics
            result['statistics'] = solver.get_solver_statistics()
            
            print(f"✅ Solution completed successfully - {len(result['exported_files'])} files created")
        else:
            print(f"❌ Solution failed")
            
        return result
        
    except Exception as e:
        print(f"❌ Error in quick solution: {e}")
        return {
            'success': False,
            'error': str(e),
            'solution': None,
            'exported_files': []
        }


def create_from_config_file(soldiers, config_file_path: str) -> solver.SmartScheduleSoldiers:
    """
    Creates a solver from a JSON configuration file
    
    Args:
        soldiers: List of soldiers
        config_file_path: Path to the configuration file
        
    Returns:
        SmartScheduleSoldiers: Solver instance
        
    Example:
        >>> solver = create_from_config_file(soldiers, "config.json")
    """
    import json
    
    try:
        with open(config_file_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        return solver.SmartScheduleSoldiers.from_json_config(soldiers, config)
        
    except Exception as e:
        print(f"❌ Error loading configuration file: {e}")
        raise


def get_default_config() -> dict:
    """
    Returns default configuration
    
    Returns:
        dict: Default configuration
    """
    return {
        'start_date': '2025-01-01',
        'end_date': '2025-01-31', 
        'default_base_days_target': 15,
        'default_home_days_target': 15, 
        'max_consecutive_base_days': 10,
        'max_consecutive_home_days': 7,
        'min_base_block_days': 3,
        'min_required_soldiers_per_day': 6,
        'max_total_home_days': None,
        'max_weekend_base_days_per_soldier': None,
        'flexible_daily_requirement': False
    }


def get_algorithm_info() -> dict:
    """
    Returns information about the algorithm
    
    Returns:
        dict: Information about the algorithm
    """
    return {
        'name': __algorithm_name__,
        'version': __version__,
        'architecture': __architecture__,
        'description': 'Advanced solution engine for soldier scheduling problems',
        'features': [
            'Handling extreme problems',
            'Preventing one-day blocks', 
            'Balance and fairness',
            'Dynamic adaptation',
            'Modular architecture',
            'Advanced export'
        ],
        'supported_exports': ['Excel', 'JSON'],
        'constraint_types': [
            'Basic constraints',
            'Daily requirements',
            'Minimum work',
            'Block constraints',
            'Consecutive days',
            'Balance and fairness'
        ]
    }


def validate_system_requirements() -> dict:
    """
    Checks system requirements
    
    Returns:
        dict: Requirements check results
    """
    requirements = {
        'valid': True,
        'errors': [],
        'warnings': [],
        'modules_status': {}
    }
    
    # Check required modules
    required_modules = {
        'ortools': 'OR-Tools',
        'openpyxl': 'OpenPyXL', 
        'datetime': 'DateTime',
        'typing': 'Typing'
    }
    
    for module_name, display_name in required_modules.items():
        try:
            __import__(module_name)
            requirements['modules_status'][display_name] = 'OK'
        except ImportError:
            requirements['modules_status'][display_name] = 'MISSING'
            requirements['errors'].append(f'Missing module: {display_name}')
            requirements['valid'] = False
    
    # Additional checks
    try:
        from ortools.sat.python import cp_model
        # Basic OR-Tools check
        model = cp_model.CpModel()
        requirements['modules_status']['OR-Tools CP-SAT'] = 'OK'
    except Exception as e:
        requirements['errors'].append(f'Error in OR-Tools: {e}')
        requirements['valid'] = False
    
    return requirements


def print_module_info():
    """Prints module information"""
    info = get_algorithm_info()
    
    print("="*60)
    print(f"💎 {info['name']} v{info['version']}")
    print(f"🏗️ Architecture: {info['architecture']}")
    print(f"📝 Description: {info['description']}")
    print()
    print("🚀 Key Features:")
    for feature in info['features']:
        print(f"  ✅ {feature}")
    print()
    print("📋 Supported Constraint Types:")
    for constraint in info['constraint_types']:
        print(f"  🔒 {constraint}")
    print()
    print("📤 Export Formats:")
    for export_format in info['supported_exports']:
        print(f"  📊 {export_format}")
    print("="*60)


# Optional: Print info on load
if __name__ == "__main__":
    print_module_info()