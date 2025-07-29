"""
📄 JSON Exporter - V9.0
Exports scheduling results to JSON in various formats
"""

import json
import uuid
from datetime import datetime, date
from typing import List, Dict, Any, Optional

from ..utils import generate_shift_id, generate_employee_id, save_to_json


class JsonExporter:
    """Class for exporting results to JSON"""
    
    def __init__(self, calendar: List[date], soldiers: List):
        self.calendar = calendar
        self.soldiers = soldiers
    
    def export(self, solution_data: Dict[str, Any], output_filepath: str, 
              format_type: str = 'shifts') -> None:
        """
        Exports the solution to JSON
        
        Args:
            solution_data: The solution data
            output_filepath: The output file path
            format_type: The format type ('shifts', 'detailed', 'summary')
        """
        if not solution_data:
            print("❌ No solution data to export to JSON")
            return
        
        print(f"📄 Exporting schedule to JSON: {output_filepath}")
        
        try:
            if format_type == 'shifts':
                data = self._create_shifts_format(solution_data)
            elif format_type == 'detailed':
                data = self._create_detailed_format(solution_data)
            elif format_type == 'summary':
                data = self._create_summary_format(solution_data)
            else:
                raise ValueError(f"Unsupported format: {format_type}")
            
            save_to_json(data, output_filepath)
            
            shifts_count = len(data.get('shifts', []))
            print(f"✅ JSON export completed successfully - {shifts_count} shifts")
            
        except Exception as e:
            print(f"❌ Error exporting to JSON: {e}")
    
    def _create_shifts_format(self, solution_data: Dict) -> Dict[str, Any]:
        """
        Creates shifts format - suitable for integration with external systems
        
        Args:
            solution_data: The solution data
            
        Returns:
            Dict: Data in shifts format
        """
        shifts = []
        
        for day in self.calendar:
            soldiers_on_base = self._get_soldiers_on_base_for_day(day, solution_data)
            
            for soldier_name in soldiers_on_base:
                soldier_obj = self._find_soldier_by_name(soldier_name)
                
                if soldier_obj:
                    shift = {
                        "id": generate_shift_id(day, soldier_name),
                        "employeeId": generate_employee_id(soldier_obj),
                        "date": day.isoformat(),
                        "shift_type": "base",
                        "soldier_name": soldier_name
                    }
                    
                    # Additional information if available
                    if soldier_obj.is_weekend_only_soldier_flag:
                        shift["soldier_type"] = "weekend"
                    elif hasattr(soldier_obj, 'is_exceptional_output') and soldier_obj.is_exceptional_output:
                        shift["soldier_type"] = "exceptional"
                    else:
                        shift["soldier_type"] = "regular"
                    
                    shifts.append(shift)
        
        return {
            "shifts": shifts,
            "metadata": self._create_metadata(solution_data),
            "summary": self._create_basic_summary(solution_data)
        }
    
    def _create_detailed_format(self, solution_data: Dict) -> Dict[str, Any]:
        """
        Creates detailed format with all information
        
        Args:
            solution_data: The solution data
            
        Returns:
            Dict: Detailed data
        """
        soldiers_data = {}
        
        for soldier in self.soldiers:
            if soldier.name in solution_data:
                soldier_data = solution_data[soldier.name]
                
                soldiers_data[soldier.name] = {
                    "employee_id": generate_employee_id(soldier),
                    "soldier_type": self._get_soldier_type(soldier),
                    "schedule": soldier_data.get('schedule', []),
                    "summary": {
                        "total_base_days": soldier_data.get('total_base_days', 0),
                        "total_home_days": soldier_data.get('total_home_days', 0),
                        "total_weekend_base_days": soldier_data.get('total_weekend_base_days', 0)
                    },
                    "constraints": {
                        "total_constraints": len(soldier.raw_constraints),
                        "constraints_dates": [d.isoformat() for d in soldier.raw_constraints],
                        "constraints_ratio": len(soldier.raw_constraints) / len(self.calendar) # Corrected bug
                    }
                }
        
        return {
            "soldiers": soldiers_data,
            "daily_soldiers_count": solution_data.get('daily_soldiers_count', {}),
            "calendar": {
                "start_date": self.calendar[0].isoformat(),
                "end_date": self.calendar[-1].isoformat(),
                "total_days": len(self.calendar),
                "dates": [d.isoformat() for d in self.calendar]
            },
            "metadata": self._create_metadata(solution_data)
        }
    
    def _create_summary_format(self, solution_data: Dict) -> Dict[str, Any]:
        """
        Creates a concise summary format
        
        Args:
            solution_data: The solution data
            
        Returns:
            Dict: Concise summary
        """
        soldiers_summary = {}
        
        for soldier in self.soldiers:
            if soldier.name in solution_data:
                soldier_data = solution_data[soldier.name]
                soldiers_summary[soldier.name] = {
                    "base_days": soldier_data.get('total_base_days', 0),
                    "home_days": soldier_data.get('total_home_days', 0),
                    "weekend_base_days": soldier_data.get('total_weekend_base_days', 0),
                    "type": self._get_soldier_type(soldier)
                }
        
        return {
            "period": {
                "start_date": self.calendar[0].isoformat(),
                "end_date": self.calendar[-1].isoformat(),
                "total_days": len(self.calendar)
            },
            "soldiers_summary": soldiers_summary,
            "daily_counts": solution_data.get('daily_soldiers_count', {}),
            "statistics": self._calculate_statistics(solution_data)
        }
    
    def _get_soldiers_on_base_for_day(self, day: date, solution_data: Dict) -> List[str]:
        """
        Returns a list of soldiers on base for a specific day
        
        Args:
            day: The date
            solution_data: The solution data
            
        Returns:
            List[str]: Names of soldiers on base
        """
        soldiers_on_base = []
        
        for soldier in self.soldiers:
            if soldier.name in solution_data:
                schedule = solution_data[soldier.name].get('schedule', [])
                
                for day_data in schedule:
                    if (day_data['date'] == day.isoformat() and 
                        day_data['status'] == 'Base'): # Translated from Hebrew
                        soldiers_on_base.append(soldier.name)
                        break
        
        return soldiers_on_base
    
    def _find_soldier_by_name(self, soldier_name: str):
        """Finds a soldier by name"""
        return next((s for s in self.soldiers if s.name == soldier_name), None)
    
    def _get_soldier_type(self, soldier) -> str:
        """Returns the soldier type"""
        if soldier.is_weekend_only_soldier_flag:
            return "weekend"
        elif hasattr(soldier, 'is_exceptional_output') and soldier.is_exceptional_output:
            return "exceptional"
        else:
            return "regular"
    
    def _create_metadata(self, solution_data: Dict) -> Dict[str, Any]:
        """Creates metadata for the export operation"""
        return {
            "export_timestamp": datetime.now().isoformat(),
            "version": "9.0",
            "algorithm": "DynamicBlockCrusher",
            "total_soldiers": len(self.soldiers),
            "calendar_length": len(self.calendar),
            "format": "modular_v9"
        }
    
    def _create_basic_summary(self, solution_data: Dict) -> Dict[str, Any]:
        """Creates a basic summary"""
        total_base_days = 0
        total_home_days = 0
        total_weekend_base_days = 0
        
        for soldier_name, data in solution_data.items():
            if soldier_name != 'daily_soldiers_count':
                total_base_days += data.get('total_base_days', 0)
                total_home_days += data.get('total_home_days', 0)
                total_weekend_base_days += data.get('total_weekend_base_days', 0)
        
        return {
            "total_base_days": total_base_days,
            "total_home_days": total_home_days,
            "total_weekend_base_days": total_weekend_base_days,
            "avg_base_days_per_soldier": round(total_base_days / len(self.soldiers), 2) if self.soldiers else 0
        }
    
    def _calculate_statistics(self, solution_data: Dict) -> Dict[str, Any]:
        """
        Calculates advanced statistics
        """
        base_days_list = []
        home_days_list = []
        weekend_soldiers = 0
        exceptional_soldiers = 0
        
        for soldier in self.soldiers:
            if soldier.name in solution_data:
                data = solution_data[soldier.name]
                base_days_list.append(data.get('total_base_days', 0))
                home_days_list.append(data.get('total_home_days', 0))
                
                if soldier.is_weekend_only_soldier_flag:
                    weekend_soldiers += 1
                elif hasattr(soldier, 'is_exceptional_output') and soldier.is_exceptional_output:
                    exceptional_soldiers += 1
        
        return {
            "base_days_statistics": {
                "min": min(base_days_list) if base_days_list else 0,
                "max": max(base_days_list) if base_days_list else 0,
                "average": round(sum(base_days_list) / len(base_days_list), 2) if base_days_list else 0
            },
            "soldiers_by_type": {
                "regular": len(self.soldiers) - weekend_soldiers - exceptional_soldiers,
                "weekend": weekend_soldiers,
                "exceptional": exceptional_soldiers
            },
            "calendar_info": {
                "total_days": len(self.calendar),
                "weekends": len([d for d in self.calendar if d.weekday() == 5]),  # Saturdays
                "weekdays": len([d for d in self.calendar if d.weekday() < 5])
            }
        }
    
    def export_multiple_formats(self, solution_data: Dict, base_filename: str) -> None:
        """
        Exports the solution in multiple JSON formats
        
        Args:
            solution_data: The solution data
            base_filename: The base filename (without extension)
        """
        formats = {
            'shifts': 'shifts.json',
            'detailed': 'detailed.json', 
            'summary': 'summary.json'
        }
        
        print("📋 Exporting in multiple JSON formats...")
        
        for format_type, suffix in formats.items():
            filename = f"{base_filename}_{suffix}"
            self.export(solution_data, filename, format_type)
        
        print("✅ Export to all formats completed")
    
    def create_api_compatible_format(self, solution_data: Dict) -> Dict[str, Any]:
        """
        Creates an API-compatible format for external systems
        
        Args:
            solution_data: The solution data
            
        Returns:
            Dict: API-compatible data
        """
        shifts = []
        employees = []
        
        # Create employee list
        for soldier in self.soldiers:
            employee = {
                "id": generate_employee_id(soldier),
                "name": soldier.name,
                "type": self._get_soldier_type(soldier),
                "constraints_count": len(soldier.raw_constraints)
            }
            employees.append(employee)
        
        # Create shifts
        for day in self.calendar:
            soldiers_on_base = self._get_soldiers_on_base_for_day(day, solution_data)
            
            for soldier_name in soldiers_on_base:
                soldier_obj = self._find_soldier_by_name(soldier_name)
                
                if soldier_obj:
                    shift = {
                        "id": generate_shift_id(day, soldier_name),
                        "employee_id": generate_employee_id(soldier_obj),
                        "date": day.isoformat(),
                        "start_time": "08:00",  # Default start time
                        "end_time": "17:00",    # Default end time
                        "shift_type": "base_duty"
                    }
                    shifts.append(shift)
        
        return {
            "employees": employees,
            "shifts": shifts,
            "schedule_metadata": {
                "period_start": self.calendar[0].isoformat(),
                "period_end": self.calendar[-1].isoformat(),
                "created_at": datetime.now().isoformat(),
                "algorithm_version": "9.0"
            }
        }
    
    def validate_json_output(self, data: Dict) -> Dict[str, Any]:
        """
        Validates the correctness of the JSON output
        
        Args:
            data: The data to validate
            
        Returns:
            Dict: Validation results
        """
        errors = []
        warnings = []
        
        # Basic checks
        if not isinstance(data, dict):
            errors.append("Data is not a valid dictionary")
            return {"valid": False, "errors": errors, "warnings": warnings}
        
        # Check required fields
        required_fields = ["shifts"] if "shifts" in data else []
        for field in required_fields:
            if field not in data:
                errors.append(f"Missing required field: {field}")
        
        # Check shifts
        if "shifts" in data:
            shifts = data["shifts"]
            if not isinstance(shifts, list):
                errors.append("shifts must be a list")
            else:
                for i, shift in enumerate(shifts):
                    if not all(key in shift for key in ["id", "employeeId", "date"]):
                        errors.append(f"Shift {i} missing required fields")
        
        # Check dates
        try:
            if "calendar" in data and "dates" in data["calendar"]:
                for date_str in data["calendar"]["dates"][:5]:  # Check a subset of dates
                    date.fromisoformat(date_str)
        except ValueError:
            errors.append("Invalid date format")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "data_size": len(json.dumps(data).encode('utf-8')),
            "shifts_count": len(data.get("shifts", []))
        }