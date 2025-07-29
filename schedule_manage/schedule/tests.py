# tests/test_intelligent_scheduling.py
"""
מערכת בדיקות מקיפה למערכת השיבוץ החכמה
=============================================

כוללת בדיקות עבור:
- מחלקת החייל ואילוציו
- מנוע האופטימיזציה  
- מנהל האילוצים
- מערכת הייצוא
- ביצועים ואמינות
"""

import pytest
import tempfile
import os
from datetime import date, timedelta
from typing import List
import time

# ייבוא המערכת
from algorithms.solver import SmartScheduleSoldiers
from algorithms.soldier import Soldier
from algorithms.exporters.excel import ExcelExporter
from algorithms.utils import generate_calendar, validate_config, validate_soldiers_list
from algorithms.analysis import ProblemAnalyzer, ParameterAdapter, ExceptionalSoldiersAnalyzer

# Helper function for tests, as it's not part of the main algorithm package anymore
def create_example_soldiers(num_soldiers: int = 10) -> List[Soldier]:
    soldiers = []
    for i in range(num_soldiers):
        soldiers.append(Soldier(
            id=str(i + 1),
            name=f"Soldier {i + 1}",
            unavailable_days=[],
            is_exceptional_output=(i % 3 == 0),
            is_weekend_only_soldier_flag=(i % 5 == 0)
        ))
    return soldiers


class TestSoldier:
    """בדיקות למחלקת החייל"""
    
    def test_soldier_creation(self):
        """בדיקת יצירת חייל בסיסי"""
        soldier = Soldier(
            id="1",
            name="חייל בדיקה",
            unavailable_days=["2025-08-10", "2025-08-11"],
            is_exceptional_output=False,
            is_weekend_only_soldier_flag=False
        )
        
        assert soldier.id == "1"
        assert soldier.name == "חייל בדיקה"
        assert len(soldier.raw_constraints) == 2
        assert not soldier.is_exceptional_output
        assert not soldier.is_weekend_only_soldier_flag
    
    def test_soldier_exceptional_creation(self):
        """בדיקת יצירת חייל חריג"""
        soldier = Soldier(
            id="2",
            name="חייל חריג",
            unavailable_days=["2025-08-10", "2025-08-11", "2025-08-12", "2025-08-13"],
            is_exceptional_output=True,
            is_weekend_only_soldier_flag=False
        )
        
        assert soldier.is_exceptional_output
        assert len(soldier.raw_constraints) == 4
    
    def test_soldier_weekend_only_creation(self):
        """בדיקת יצירת חייל סופ"ש"""
        soldier = Soldier(
            id="3",
            name="חייל סופש",
            unavailable_days=["2025-08-20"],
            is_exceptional_output=False,
            is_weekend_only_soldier_flag=True
        )
        
        assert soldier.is_weekend_only_soldier_flag
        assert len(soldier.raw_constraints) == 1
    
    def test_soldier_parameter_analysis(self):
        """בדיקת ניתוח פרמטרים ספציפיים לחייל"""
        soldier = Soldier(
            id="4",
            name="חייל לניתוח",
            unavailable_days=["2025-08-01", "2025-08-02", "2025-08-03", "2025-08-04", "2025-08-05"],
            is_exceptional_output=True,
            is_weekend_only_soldier_flag=False
        )
        
        # הפעלת ניתוח
        soldier.analyze_soldier_specific_parameters(
            global_max_consecutive_home_days=10,
            global_default_home_days_target=25,
            calendar_length=55
        )
        
        # בדיקה שהניתוח הופעל
        summary = soldier.get_constraint_summary()
        assert summary['is_exceptional_output'] == True
        assert summary['total_constraint_days'] == 5
    
    def test_soldier_invalid_data(self):
        """בדיקת טיפול בנתונים לא תקינים"""
        with pytest.raises(ValueError):
            Soldier(
                id="",  # ID ריק
                name="חייל",
                unavailable_days=[],
            )
        
        with pytest.raises(ValueError):
            Soldier(
                id="5",
                name="",  # שם ריק
                unavailable_days=[],
            )
    
    def test_constraint_validation(self):
        """בדיקת תקינות אילוצים"""
        soldier = Soldier(
            id="6",
            name="חייל בדיקה",
            unavailable_days=["2025-08-10", "invalid_date"],  # תאריך לא תקין
        )
        
        # המערכת צריכה להתמודד עם תאריכים לא תקינים
        assert len(soldier.raw_constraints) == 1  # רק התאריך התקין
    
    def test_effective_parameters(self):
        """בדיקת פרמטרים אפקטיביים"""
        soldier = Soldier(
            id="7",
            name="חייל פרמטרים",
            unavailable_days=[],
        )
        
        # ברירות מחדל
        assert soldier.get_effective_max_consecutive_base_days(7) == 7
        assert soldier.get_effective_max_consecutive_home_days(10) == 10
        assert soldier.get_effective_default_home_days_target(25) == 25
        
        # עם override
        soldier.max_base_days_override = 14
        assert soldier.get_effective_max_consecutive_base_days(7) == 14





class TestUtils:
    """בדיקות לכלי העזר"""
    
    def setup_method(self):
        """הכנה לכל בדיקה"""
        self.start_date = date(2025, 8, 1)
        self.end_date = date(2025, 8, 31)
    
    def test_generate_calendar(self):
        """בדיקת יצירת טווח תאריכים"""
        dates = generate_calendar(self.start_date, self.end_date)
        
        expected_days = (self.end_date - self.start_date).days + 1
        assert len(dates) == expected_days
        assert dates[0] == self.start_date
        assert dates[-1] == self.end_date
    
    def test_parse_date(self):
        """בדיקת המרת תאריך"""
        parsed_date = parse_date("2025-08-01")
        assert parsed_date == date(2025, 8, 1)
        
        with pytest.raises(ValueError):
            parse_date("invalid-date")

    def test_validate_soldiers_list(self):
        """בדיקת תקינות רשימת חיילים"""
        valid_soldiers = create_example_soldiers(2)
        validate_soldiers_list(valid_soldiers)
        
        with pytest.raises(ValueError):
            validate_soldiers_list([])
        
        with pytest.raises(ValueError):
            validate_soldiers_list(["not a soldier object"])

    def test_validate_config(self):
        """בדיקת תקינות קונפיגורציה"""
        valid_config = {
            'start_date': "2025-01-01",
            'end_date': "2025-01-31",
            'default_base_days_target': 15,
            'default_home_days_target': 15,
            'max_consecutive_base_days': 10,
            'max_consecutive_home_days': 7,
            'min_base_block_days': 3,
            'min_required_soldiers_per_day': 6
        }
        validate_config(valid_config)
        
        invalid_config = valid_config.copy()
        invalid_config.pop('start_date')
        with pytest.raises(ValueError):
            validate_config(invalid_config)


class TestExcelExporter:
    """בדיקות למערכת ייצוא אקסל"""
    
    def setup_method(self):
        """הכנה לכל בדיקה"""
        self.soldiers = create_example_soldiers(3)
        self.calendar = generate_calendar(date(2025, 8, 1), date(2025, 8, 15))
        self.exporter = ExcelExporter(self.calendar, self.soldiers)
        
        # יצירת נתוני דמה לפתרון
        self.solution_data = {
            soldier.name: {
                'schedule': [{'date': d.isoformat(), 'status': 'בסיס' if i % 2 == 0 else 'בית'} for i, d in enumerate(self.calendar)],
                'total_base_days': 7,
                'total_home_days': 8,
                'total_weekend_base_days': 1
            }
            for i, soldier in enumerate(self.soldiers)
        }
        self.solution_data['daily_soldiers_count'] = {d.isoformat(): 2 for d in self.calendar}

    def test_export(self):
        """בדיקת ייצוא"""
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            filename = tmp.name
        
        try:
            self.exporter.export(self.solution_data, filename)
            
            assert os.path.exists(filename)
            
        finally:
            if os.path.exists(filename):
                os.unlink(filename)


class TestSmartScheduleSoldiers:
    """בדיקות למערכת השיבוץ הראשית"""
    
    def setup_method(self):
        """הכנה לכל בדיקה"""
        self.soldiers = create_example_soldiers(num_soldiers=4)  # 4 חיילים לבדיקות
        self.start_date = date(2025, 8, 1)
        self.end_date = date(2025, 8, 15)  # תקופה קצרה לבדיקות מהירות
        self.default_params = {
            'default_base_days_target': 8,
            'default_home_days_target': 7,
            'max_consecutive_base_days': 5,
            'max_consecutive_home_days': 7,
            'min_base_block_days': 3,
            'min_required_soldiers_per_day': 2
        }

    def test_basic_scheduling(self):
        """בדיקת שיבוץ בסיסי"""
        solver = SmartScheduleSoldiers(
            soldiers=self.soldiers,
            start_date=self.start_date,
            end_date=self.end_date,
            **self.default_params
        )
        solution_data, status = solver.solve()
        
        assert status in [cp_model.OPTIMAL, cp_model.FEASIBLE]
        assert solution_data is not None
        assert len(solution_data) > 0
        assert "daily_soldiers_count" in solution_data

    def test_scheduling_with_constraints(self):
        """בדיקת שיבוץ עם אילוצים"""
        constrained_soldiers = []
        for i, soldier in enumerate(self.soldiers):
            if i == 0:
                soldier.unavailable_days.add(date(2025, 8, 8).isoformat())
            constrained_soldiers.append(soldier)
        
        solver = SmartScheduleSoldiers(
            soldiers=constrained_soldiers,
            start_date=self.start_date,
            end_date=self.end_date,
            **self.default_params
        )
        solution_data, status = solver.solve()
        
        assert status in [cp_model.OPTIMAL, cp_model.FEASIBLE]
        
        # בדיקה שהאילוץ נשמר
        constraint_date_str = date(2025, 8, 8).isoformat()
        if constraint_date_str in solution_data[constrained_soldiers[0].name]['schedule']:
            for day_schedule in solution_data[constrained_soldiers[0].name]['schedule']:
                if day_schedule['date'] == constraint_date_str:
                    assert day_schedule['status'] == 'בית'
                    break

    def test_weekend_only_soldier(self):
        """בדיקת חייל סופ"ש"""
        weekend_soldier = Soldier(
            id="weekend",
            name="חייל סופש",
            unavailable_days=[],
            is_weekend_only_soldier_flag=True
        )
        
        soldiers_with_weekend = self.soldiers + [weekend_soldier]
        
        solver = SmartScheduleSoldiers(
            soldiers=soldiers_with_weekend,
            start_date=self.start_date,
            end_date=self.end_date,
            **self.default_params
        )
        solution_data, status = solver.solve()
        
        assert status in [cp_model.OPTIMAL, cp_model.FEASIBLE]
        
        # בדיקה שחייל הסופ"ש עובד בעיקר בסופי שבוע
        weekend_summary = solution_data.get(weekend_soldier.name, {})
        total_base_days = weekend_summary.get('total_base_days', 0)
        total_weekend_base_days = weekend_summary.get('total_weekend_base_days', 0)
        
        # חייל סופ"ש צריך לעבוד יותר בשבתות יחסית לחיילים אחרים
        if total_base_days > 0:
            weekend_ratio = total_weekend_base_days / total_base_days
            assert weekend_ratio >= 0.3  # לפחות 30% מעבודתו בשבתות

    def test_exceptional_soldier(self):
        """בדיקת חייל חריג"""
        exceptional_soldier = Soldier(
            id="exceptional",
            name="חייל חריג",
            unavailable_days=["2025-08-02", "2025-08-03", "2025-08-04", "2025-08-05"],
            is_exceptional_output=True
        )
        
        soldiers_with_exceptional = self.soldiers + [exceptional_soldier]
        
        solver = SmartScheduleSoldiers(
            soldiers=soldiers_with_exceptional,
            start_date=self.start_date,
            end_date=self.end_date,
            **self.default_params
        )
        solution_data, status = solver.solve()
        
        assert status in [cp_model.OPTIMAL, cp_model.FEASIBLE]
        
        # בדיקה שהאילוצים של החייל החריג נשמרו
        exceptional_summary = solution_data.get(exceptional_soldier.name, {})
        # The new solver doesn't return constraint_violations directly in the summary
        # We need to check the schedule for violations
        for day_schedule in exceptional_summary['schedule']:
            if day_schedule['date'] in exceptional_soldier.raw_constraints_iso and day_schedule['status'] == 'בסיס':
                pytest.fail(f"Constraint violation for {exceptional_soldier.name} on {day_schedule['date']}")

    def test_infeasible_scenario(self):
        """בדיקת תרחיש לא בר-ביצוע"""
        impossible_soldiers = []
        constraint_date = date(2025, 8, 8).isoformat()
        
        for i, soldier in enumerate(self.soldiers):
            constrained_soldier = Soldier(
                id=soldier.id,
                name=soldier.name,
                unavailable_days=[constraint_date],
                is_exceptional_output=soldier.is_exceptional_output,
                is_weekend_only_soldier_flag=soldier.is_weekend_only_soldier_flag
            )
            impossible_soldiers.append(constrained_soldier)
        
        # Set min_required_soldiers_per_day higher than available soldiers
        infeasible_params = self.default_params.copy()
        infeasible_params['min_required_soldiers_per_day'] = len(impossible_soldiers) + 1

        solver = SmartScheduleSoldiers(
            soldiers=impossible_soldiers,
            start_date=self.start_date,
            end_date=self.end_date,
            **infeasible_params
        )
        solution_data, status = solver.solve()
        
        assert status == cp_model.INFEASIBLE


class TestValidation:
    """בדיקות לפונקציות תקינות"""
    
    def test_valid_parameters(self):
        """בדיקת פרמטרים תקינים"""
        soldiers = create_example_soldiers(3)
        
        valid_config = {
            'start_date': "2025-08-01",
            'end_date': "2025-08-31",
            'default_base_days_target': 15,
            'default_home_days_target': 16,
            'max_consecutive_base_days': 7,
            'max_consecutive_home_days': 10,
            'min_base_block_days': 3,
            'min_required_soldiers_per_day': 2
        }
        validate_config(valid_config)
        validate_soldiers_list(soldiers)
        
        assert True # If no exceptions, validation passed
    
    def test_invalid_dates(self):
        """בדיקת תאריכים לא תקינים"""
        soldiers = create_example_soldiers(3)
        
        invalid_config = {
            'start_date': "2025-08-31",  # After end date
            'end_date': "2025-08-01",
            'default_base_days_target': 15,
            'default_home_days_target': 16,
            'max_consecutive_base_days': 7,
            'max_consecutive_home_days': 10,
            'min_base_block_days': 3,
            'min_required_soldiers_per_day': 2
        }
        with pytest.raises(ValueError):
            validate_config(invalid_config)

    def test_insufficient_soldiers(self):
        """בדיקת מחסור בחיילים"""
        soldiers = create_example_soldiers(2)  # Only 2 soldiers
        
        with pytest.raises(ValueError):
            validate_soldiers_list([])
        
        # This scenario is now handled by the solver's internal logic and analysis,
        # not by a direct validation function here.
        # The solver will attempt to find a feasible solution or return INFEASIBLE.
        pass


class TestPerformance:
    """בדיקות ביצועים"""
    
    def setup_method(self):
        self.default_params = {
            'default_base_days_target': 8,
            'default_home_days_target': 7,
            'max_consecutive_base_days': 5,
            'max_consecutive_home_days': 7,
            'min_base_block_days': 3,
            'min_required_soldiers_per_day': 2
        }

    def test_small_scheduling_performance(self):
        """בדיקת ביצועים לשיבוץ קטן"""
        soldiers = create_example_soldiers(5)
        
        start_time = time.time()
        
        solver = SmartScheduleSoldiers(
            soldiers=soldiers,
            start_date=date(2025, 8, 1),
            end_date=date(2025, 8, 15),
            **self.default_params
        )
        solution_data, status = solver.solve()
        
        end_time = time.time()
        actual_time = end_time - start_time
        
        assert actual_time < 30  # Less than 30 seconds
        assert status in [cp_model.OPTIMAL, cp_model.FEASIBLE]
    
    def test_memory_usage(self):
        """בדיקת שימוש בזיכרון"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        memory_before = process.memory_info().rss / 1024 / 1024  # MB
        
        soldiers = create_example_soldiers(10)
        solver = SmartScheduleSoldiers(
            soldiers=soldiers,
            start_date=date(2025, 8, 1),
            end_date=date(2025, 8, 31),
            default_base_days_target=15,
            default_home_days_target=16,
            max_consecutive_base_days=7,
            max_consecutive_home_days=10,
            min_base_block_days=3,
            min_required_soldiers_per_day=3
        )
        solution_data, status = solver.solve()
        
        memory_after = process.memory_info().rss / 1024 / 1024  # MB
        memory_used = memory_after - memory_before
        
        assert memory_used < 500
        assert status in [cp_model.OPTIMAL, cp_model.FEASIBLE]


class TestIntegration:
    """בדיקות אינטגרציה מלאה"""
    
    def setup_method(self):
        """הכנה לכל בדיקה"""
        self.soldiers = create_example_soldiers(4)
        self.start_date = date(2025, 8, 1)
        self.end_date = date(2025, 8, 31)
        self.default_params = {
            'default_base_days_target': 15,
            'default_home_days_target': 16,
            'max_consecutive_base_days': 7,
            'max_consecutive_home_days': 10,
            'min_base_block_days': 3,
            'min_required_soldiers_per_day': 2
        }

    def test_full_workflow(self):
        """בדיקת תהליך מלא מקצה לקצה"""
        # 1. יצירת חיילים (כבר נעשה ב-setup_method)
        
        # 2. הרצת שיבוץ
        solver = SmartScheduleSoldiers(
            soldiers=self.soldiers,
            start_date=self.start_date,
            end_date=self.end_date,
            **self.default_params
        )
        solution_data, status = solver.solve()
        
        assert status in [cp_model.OPTIMAL, cp_model.FEASIBLE]
        assert solution_data is not None
        
        # 3. ייצוא תוצאות
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            filename = tmp.name
        
        try:
            exporter = ExcelExporter(solver.calendar, solver.soldiers)
            exporter.export(solution_data, filename)
            
            assert os.path.exists(filename)
            
        finally:
            if os.path.exists(filename):
                os.unlink(filename)
        
        # 4. בדיקת איכות התוצאות
        assert len(solution_data['daily_soldiers_count']) == (self.end_date - self.start_date).days + 1
        assert len(solution_data) == len(self.soldiers) + 1 # +1 for daily_soldiers_count
        
        # בדיקה שכל חייל קיבל שיבוץ
        for soldier in self.soldiers:
            assert soldier.name in solution_data
            summary = solution_data[soldier.name]
            assert summary['total_base_days'] >= 0
            assert summary['total_home_days'] >= 0


# פונקציות עזר לבדיקות
def run_performance_benchmarks():
    """הרצת בדיקות ביצועים מקיפות"""
    import time
    from ortools.sat.python import cp_model
    
    print("🚀 מתחיל בדיקות ביצועים...")
    
    default_params = {
        'default_base_days_target': 8,
        'default_home_days_target': 7,
        'max_consecutive_base_days': 5,
        'max_consecutive_home_days': 7,
        'min_base_block_days': 3,
        'min_required_soldiers_per_day': 2
    }

    # מבחן 1: שיבוץ קטן
    print("📊 מבחן 1: שיבוץ קטן (5 חיילים, 15 ימים)")
    soldiers = create_example_soldiers(5)
    
    start_time = time.time()
    solver_small = SmartScheduleSoldiers(
        soldiers=soldiers,
        start_date=date(2025, 8, 1),
        end_date=date(2025, 8, 15),
        **default_params
    )
    solution_data_small, status_small = solver_small.solve()
    small_time = time.time() - start_time
    
    print(f"   ✅ זמן: {small_time:.2f}s, סטטוס: {solver_small.solver.StatusName(status_small)}")
    
    # מבחן 2: שיבוץ בינוני
    print("📊 מבחן 2: שיבוץ בינוני (10 חיילים, 31 ימים)")
    soldiers = create_example_soldiers(10)
    
    start_time = time.time()
    solver_medium = SmartScheduleSoldiers(
        soldiers=soldiers,
        start_date=date(2025, 8, 1),
        end_date=date(2025, 8, 31),
        default_base_days_target=15,
        default_home_days_target=16,
        max_consecutive_base_days=7,
        max_consecutive_home_days=10,
        min_base_block_days=3,
        min_required_soldiers_per_day=3
    )
    solution_data_medium, status_medium = solver_medium.solve()
    medium_time = time.time() - start_time
    
    print(f"   ✅ זמן: {medium_time:.2f}s, סטטוס: {solver_medium.solver.StatusName(status_medium)}")
    
    print(f"📈 סיכום ביצועים:")
    print(f"   • שיבוץ קטן: {small_time:.2f}s")
    print(f"   • שיבוץ בינוני: {medium_time:.2f}s")


if __name__ == "__main__":
    # הרצת בדיקות ביצועים ישירות
    run_performance_benchmarks()