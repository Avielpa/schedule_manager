"""
📋 מודול ייצוא תוצאות - V9.0
מרכז את כל מייצאי התוצאות לפורמטים שונים
"""

from .excel import ExcelExporter
from .json import JsonExporter

__all__ = [
    'ExcelExporter',
    'JsonExporter'
]

# פורמטים נתמכים
SUPPORTED_FORMATS = {
    'excel': {
        'exporter': ExcelExporter,
        'extensions': ['.xlsx', '.xls'],
        'description': 'Microsoft Excel format with formatting and colors'
    },
    'json': {
        'exporter': JsonExporter, 
        'extensions': ['.json'],
        'description': 'JSON format for API integration and data exchange'
    }
}

def get_exporter(format_type: str):
    """
    מחזיר מייצא לפי סוג הפורמט
    
    Args:
        format_type: סוג הפורמט ('excel', 'json')
        
    Returns:
        class: מחלקת המייצא המתאימה
        
    Raises:
        ValueError: אם הפורמט לא נתמך
    """
    if format_type not in SUPPORTED_FORMATS:
        supported = ', '.join(SUPPORTED_FORMATS.keys())
        raise ValueError(f"פורמט לא נתמך: {format_type}. פורמטים נתמכים: {supported}")
    
    return SUPPORTED_FORMATS[format_type]['exporter']

def export_to_format(solution_data, calendar, soldiers, format_type: str, filename: str):
    """
    מייצא לפורמט ספציפי
    
    Args:
        solution_data: נתוני הפתרון
        calendar: לוח זמנים
        soldiers: רשימת חיילים
        format_type: סוג הפורמט
        filename: שם הקובץ
    """
    exporter_class = get_exporter(format_type)
    exporter = exporter_class(calendar, soldiers)
    exporter.export(solution_data, filename)

def get_supported_formats() -> dict:
    """מחזיר רשימת פורמטים נתמכים"""
    return SUPPORTED_FORMATS.copy()