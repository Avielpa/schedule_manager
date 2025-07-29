"""
🔧 General Utility Functions - V9.0
Contains useful functions for the entire algorithm
"""

from datetime import date, timedelta, datetime
from typing import List, Union, Dict, Any
import uuid
import json


def parse_date(date_input: Union[str, date]) -> date:
    """
    Helper function to convert a string or date to a date object
    
    Args:
        date_input: Date as a string (ISO format) or as a date object
        
    Returns:
        date: Date object
        
    Raises:
        ValueError: If the date is invalid
    """
    if isinstance(date_input, str):
        return date.fromisoformat(date_input)
    elif isinstance(date_input, date):
        return date_input
    else:
        raise ValueError(f"Invalid date: {date_input}")


def generate_calendar(start_date: Union[str, date], end_date: Union[str, date]) -> List[date]:
    """
    Generates a list of dates from start_date to end_date (inclusive)
    
    Args:
        start_date: Start date
        end_date: End date
        
    Returns:
        List[date]: List of dates
        
    Raises:
        ValueError: If start date is after end date
    """
    start = parse_date(start_date)
    end = parse_date(end_date)
    
    if start > end:
        raise ValueError(f"Start date ({start}) must be before end date ({end})")
    
    calendar = []
    current = start
    while current <= end:
        calendar.append(current)
        current += timedelta(days=1)
    
    return calendar


def is_weekend_day(day: date) -> bool:
    """
    Checks if a day is a weekend day (Friday or Saturday)
    
    Args:
        day: The date to check
        
    Returns:
        bool: True if it's a weekend
    """
    return day.weekday() in [4, 5]  # Friday (4) and Saturday (5)


def is_saturday(day: date) -> bool:
    """
    Checks if a day is Saturday
    
    Args:
        day: The date to check
        
    Returns:
        bool: True if it's Saturday
    """
    return day.weekday() == 5


def format_date_for_excel(day: date) -> str:
    """
    Formats a date for Excel display
    
    Args:
        day: The date to format
        
    Returns:
        str: The formatted date (e.g., "15/3 Sat")
    """
    day_str = f"{day.day}/{day.month}"
    if day.weekday() == 5:  # Saturday
        day_str += " Sat"
    elif day.weekday() == 4:  # Friday
        day_str += " Fri"
    return day_str


def calculate_constraints_ratio(soldier, total_days: int) -> float:
    """
    Calculates the soldier's constraint ratio
    
    Args:
        soldier: The soldier object
        total_days: Total days in the calendar
        
    Returns:
        float: Constraint ratio (0.0-1.0)
    """
    if total_days == 0:
        return 0.0
    return len(soldier.raw_constraints) / total_days


def calculate_available_days(soldier, total_days: int) -> int:
    """
    Calculates how many days are available for a soldier
    
    Args:
        soldier: The soldier object
        total_days: Total days in the calendar
        
    Returns:
        int: Number of available days
    """
    return total_days - len(soldier.raw_constraints)


def generate_shift_id(day: date, soldier_name: str) -> str:
    """
    Generates a unique ID for a shift
    
    Args:
        day: The date of the shift
        soldier_name: The soldier's name
        
    Returns:
        str: Unique shift ID
    """
    day_as_datetime = datetime.combine(day, datetime.min.time())
    timestamp = int(day_as_datetime.timestamp())
    unique_id = str(uuid.uuid4())[:9]
    return f"shift{timestamp}-{unique_id}"


def generate_employee_id(soldier) -> str:
    """
    Generates a suitable employee ID
    
    Args:
        soldier: The soldier object
        
    Returns:
        str: Employee ID
    """
    if hasattr(soldier, 'id') and soldier.id:
        return f"emp{soldier.id}"
    else:
        return f"emp{soldier.name.replace(' ', '')}"


def validate_config(config: Dict[str, Any]) -> None:
    """
    Ensures the configuration is valid
    
    Args:
        config: The configuration dictionary
        
    Raises:
        ValueError: If required fields are missing
    """
    required_fields = [
        'start_date', 'end_date', 'default_base_days_target', 
        'default_home_days_target', 'max_consecutive_base_days',
        'max_consecutive_home_days', 'min_base_block_days',
        'min_required_soldiers_per_day'
    ]
    
    for field in required_fields:
        if config.get(field) is None:
            raise ValueError(f"Missing required configuration field: {field}")


def print_solver_info(start_date: date, end_date: date, calendar_length: int, 
                     penalty_config: Dict[str, int], difficulty: str, 
                     min_required_soldiers: int) -> None:
    """
    Prints solver information
    
    Args:
        start_date: Start date
        end_date: End date
        calendar_length: Calendar length
        penalty_config: Penalty settings
        difficulty: Difficulty level
        min_required_soldiers: Minimum required soldiers
    """
    print(f"💎 DynamicBlockCrusher V9.0 Created:")
    print(f"    📅 Range: {start_date.isoformat()} to {end_date.isoformat()} ({calendar_length} days)")
    print(f"    💀 One-day block penalty: {penalty_config['one_day']:,}")
    print(f"    💀 Soldier shortage penalty: {penalty_config['shortage']:,}")
    print(f"    💀 Soldier no-work penalty: {penalty_config['no_work']:,}")
    print(f"    💀 Long block penalty (basic/critical): {penalty_config['long_block']:,}/{penalty_config['critical_long']:,}")
    print(f"    📊 Difficulty level: {difficulty}")
    print(f"    🎯 Daily requirement: {min_required_soldiers}")


def print_analysis_summary(analysis: Dict[str, Any]) -> None:
    """
    Prints problem analysis summary
    
    Args:
        analysis: Analysis results
    """
    print(f"🔍 Extreme Problem Analysis V9.0:")
    print(f"    💀 Extreme constrained soldiers (50%+ constraints): {analysis['extreme_constrained']}")
    print(f"    ⚠️ Heavily constrained soldiers: {analysis['heavily_constrained']}")
    print(f"    ✅ Soldiers with no constraints: {analysis['no_constraints']}")
    print(f"    🏖️ Extreme weekend soldiers: {analysis['extreme_weekend_soldiers']}")
    print(f"    📊 Availability ratio: {analysis['availability_ratio']:.2f}")
    print(f"    🔥 Difficulty level: {analysis['difficulty']}")


def print_soldiers_ranking(soldiers_with_score: List, max_display: int = 8) -> None:
    """
    Prints soldier ranking
    
    Args:
        soldiers_with_score: List of soldiers with scores
        max_display: Maximum number to display
    """
    print(f"🏆 Soldier Ranking by Availability V9.0:")
    for i, (soldier, score) in enumerate(soldiers_with_score[:max_display]):
        soldier_type = "🏖️" if soldier.is_weekend_only_soldier_flag else "👤"
        exceptional = "⚠️" if soldier.is_exceptional_output else ""
        print(f"    {i+1}. {soldier_type}{exceptional} {soldier.name}: {score:.2f}")


def print_difficulty_adaptation(difficulty: str, base_target: int, home_target: int, min_soldiers: int) -> None:
    """
    Prints difficulty adaptations
    
    Args:
        difficulty: Difficulty level
        base_target: Base days target
        home_target: Home days target
        min_soldiers: Minimum soldiers
    """
    difficulty_messages = {
        "APOCALYPTIC": "💀 Apocalyptic situation",
        "CATASTROPHIC": "🔥 Catastrophic situation",
        "EXTREME": "⚠️ Extreme situation",
        "VERY_HARD": "🔶 Very hard situation"
    }
    
    if difficulty in difficulty_messages:
        print(f"🎯 Adapting parameters for difficulty: {difficulty}")
        print(f"    {difficulty_messages[difficulty]}: Targets {base_target}/{home_target}, Requirement {min_soldiers}")


def save_to_json(data: Any, filename: str) -> None:
    """
    Saves data to a JSON file
    
    Args:
        data: The data to save
        filename: The filename
    """
    with open(filename, 'w', encoding='utf-8') as json_file:
        json.dump(data, json_file, indent=2, ensure_ascii=False)


def print_solution_summary(solution_data: Dict, exclude_keys: List[str] = None) -> None:
    """
    Prints solution summary
    
    Args:
        solution_data: Solution data
        exclude_keys: Keys to exclude from the report
    """
    if exclude_keys is None:
        exclude_keys = ['daily_soldiers_count']
    
    print("📊 General Summary:")
    for s_name, data in solution_data.items():
        if s_name not in exclude_keys:
            print(f"  👤 {s_name}: Base {data['total_base_days']} days, "
                  f"Home {data['total_home_days']} days, "
                  f"Weekend Base {data['total_weekend_base_days']} days")


def print_module_loaded(module_name: str, version: str = "9.0") -> None:
    """
    Prints module loaded message
    
    Args:
        module_name: Module name
        version: Version
    """
    print(f"✅ {module_name} loaded - Version {version}")


def validate_soldiers_list(soldiers: List) -> None:
    """
    Ensures the soldier list is valid
    
    Args:
        soldiers: List of soldiers
        
    Raises:
        ValueError: If the list is invalid
    """
    if not soldiers:
        raise ValueError("Soldier list is empty")
    
    if len(soldiers) < 3:
        raise ValueError("At least 3 soldiers are required for the system")
    
    # Check for duplicate names
    names = [s.name for s in soldiers]
    if len(names) != len(set(names)):
        raise ValueError("Duplicate soldier names exist")


def calculate_weekend_count(calendar: List[date]) -> int:
    """
    Calculates the number of weekends in the calendar
    
    Args:
        calendar: List of dates
        
    Returns:
        int: Number of weekends (Saturdays)
    """
    return len([d for d in calendar if is_saturday(d)])