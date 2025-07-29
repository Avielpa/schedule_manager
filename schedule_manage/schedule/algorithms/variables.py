"""
📊 מודול יצירת משתני המודל - V9.0 משופר
אחראי על יצירת כל משתני ההחלטה עבור מודל ה-CP
עם הגנות מפני שמות חיילים בעייתיים
"""

from typing import List, Dict, Tuple, Any
from datetime import date
from ortools.sat.python import cp_model
import re


class ModelVariables:
    """מחלקה לניהול כל משתני המודל"""
    
    def __init__(self, model: cp_model.CpModel, soldiers: List, calendar: List[date]):
        self.model = model
        self.soldiers = soldiers
        self.calendar = calendar
        
        # משתני החלטה עיקריים
        self.base_assignment: Dict[Tuple[str, date], Any] = {}
        self.home_assignment: Dict[Tuple[str, date], Any] = {}
        self.is_start_base: Dict[Tuple[str, date], Any] = {}
        self.is_end_base: Dict[Tuple[str, date], Any] = {}
        
        # משתני סיכום
        self.total_soldier_base_days: Dict[str, Any] = {}
        self.total_soldier_home_days: Dict[str, Any] = {}
        self.total_soldier_weekend_base_days: Dict[str, Any] = {}
        self.daily_soldiers_count: Dict[date, Any] = {}
        
        # משתני עזר נוספים
        self.shortage_variables: Dict[date, Any] = {}
        self.excess_variables: Dict[str, Any] = {}
        self.block_variables: Dict[str, Dict] = {}
        self.fairness_variables: Dict[str, Dict] = {}
        
        # מיפוי שמות בטוחים
        self.safe_name_mapping: Dict[str, str] = {}
        
    def _create_safe_variable_name(self, soldier_name: str, suffix: str = "") -> str:
        """
        יוצר שם משתנה בטוח לOR-Tools
        
        Args:
            soldier_name: שם החייל המקורי
            suffix: סיומת נוספת למשתנה
            
        Returns:
            str: שם משתנה בטוח
        """
        if not soldier_name or not soldier_name.strip():
            soldier_name = "unknown_soldier"
        
        # שמירת המיפוי למטרות debug
        if soldier_name not in self.safe_name_mapping:
            # ניקוי תווים מיוחדים ותווים לא אמריקאיים
            safe_name = re.sub(r'[^\w\u0590-\u05FF]', '_', soldier_name.strip())
            
            # הסרת תווים כפולים
            safe_name = re.sub(r'_+', '_', safe_name)
            
            # הסרת תווי קו תחתון מהתחלה והסוף
            safe_name = safe_name.strip('_')
            
            # וידוא שהשם לא ריק
            if not safe_name:
                safe_name = f"soldier_{len(self.safe_name_mapping)}"
            
            # וידוא ייחודיות
            original_safe_name = safe_name
            counter = 1
            while safe_name in self.safe_name_mapping.values():
                safe_name = f"{original_safe_name}_{counter}"
                counter += 1
            
            self.safe_name_mapping[soldier_name] = safe_name
            
            if soldier_name != safe_name:
                print(f"🔧 שם חייל הומר למשתנה: '{soldier_name}' -> '{safe_name}'")
        
        safe_name = self.safe_name_mapping[soldier_name]
        return f"{safe_name}{suffix}" if suffix else safe_name
    
    def create_all_variables(self) -> None:
        """יוצר את כל משתני ההחלטה עבור המודל"""
        print("🔧 יוצר משתני מודל...")
        
        # בדיקת תקינות נתונים
        self._validate_input_data()
        
        self._create_assignment_variables()
        self._create_block_identification_variables()
        self._create_summary_variables()
        self._create_daily_count_variables()
        
        print(f"✅ נוצרו משתנים עבור {len(self.soldiers)} חיילים ו-{len(self.calendar)} ימים")
    
    def _validate_input_data(self) -> None:
        """מוודא שהנתונים הקלט תקינים"""
        if not self.soldiers:
            raise ValueError("❌ רשימת חיילים ריקה")
        
        if not self.calendar:
            raise ValueError("❌ לוח זמנים ריק")
        
        # בדיקת שמות חיילים
        for i, soldier in enumerate(self.soldiers):
            if not hasattr(soldier, 'name'):
                raise ValueError(f"❌ חייל במקום {i} אין לו שדה name")
            
            if not soldier.name or not soldier.name.strip():
                print(f"⚠️ חייל עם שם ריק נמצא במקום {i}, מגדיר שם ברירת מחדל")
                soldier.name = f"חייל_{i}"
        
        print(f"✅ נתוני קלט תקינים: {len(self.soldiers)} חיילים, {len(self.calendar)} ימים")
    
    def _create_assignment_variables(self) -> None:
        """יוצר משתני השמה בסיסיים (בסיס/בית)"""
        print("📋 יוצר משתני השמה...")
        variables_created = 0
        
        for soldier in self.soldiers:
            safe_soldier_name = self._create_safe_variable_name(soldier.name)
            
            for day in self.calendar:
                key = (soldier.name, day)  # המפתח נשאר עם השם המקורי
                
                try:
                    # משתנה נוכחות בבסיס
                    var_name_base = f'base_{safe_soldier_name}_{day.isoformat()}'
                    self.base_assignment[key] = self.model.NewBoolVar(var_name_base)
                    
                    # משתנה נוכחות בבית
                    var_name_home = f'home_{safe_soldier_name}_{day.isoformat()}'
                    self.home_assignment[key] = self.model.NewBoolVar(var_name_home)
                    
                    variables_created += 2
                    
                except Exception as e:
                    print(f"❌ שגיאה ביצירת משתנים עבור {soldier.name} ביום {day}: {e}")
                    raise
        
        print(f"✅ נוצרו {variables_created} משתני השמה")
    
    def _create_block_identification_variables(self) -> None:
        """יוצר משתני זיהוי בלוקים"""
        print("📋 יוצר משתני זיהוי בלוקים...")
        variables_created = 0
        
        for soldier in self.soldiers:
            self.block_variables[soldier.name] = {}
            safe_soldier_name = self._create_safe_variable_name(soldier.name)
            
            for day in self.calendar:
                key = (soldier.name, day)
                
                try:
                    # משתנה התחלת בלוק בסיס
                    var_name_start = f'start_base_{safe_soldier_name}_{day.isoformat()}'
                    self.is_start_base[key] = self.model.NewBoolVar(var_name_start)
                    
                    # משתנה סוף בלוק בסיס
                    var_name_end = f'end_base_{safe_soldier_name}_{day.isoformat()}'
                    self.is_end_base[key] = self.model.NewBoolVar(var_name_end)
                    
                    variables_created += 2
                    
                except Exception as e:
                    print(f"❌ שגיאה ביצירת משתני בלוק עבור {soldier.name} ביום {day}: {e}")
                    raise
        
        print(f"✅ נוצרו {variables_created} משתני זיהוי בלוקים")
    
    def _create_summary_variables(self) -> None:
        """יוצר משתני סיכום לכל חייל"""
        print("📋 יוצר משתני סיכום...")
        variables_created = 0
        
        for soldier in self.soldiers:
            safe_soldier_name = self._create_safe_variable_name(soldier.name)
            
            try:
                # סך ימי בסיס
                self.total_soldier_base_days[soldier.name] = self.model.NewIntVar(
                    0, len(self.calendar), f'total_base_days_{safe_soldier_name}'
                )
                
                # סך ימי בית
                self.total_soldier_home_days[soldier.name] = self.model.NewIntVar(
                    0, len(self.calendar), f'total_home_days_{safe_soldier_name}'
                )
                
                # סך ימי סופשים בבסיס
                self.total_soldier_weekend_base_days[soldier.name] = self.model.NewIntVar(
                    0, len(self.calendar), f'total_weekend_base_days_{safe_soldier_name}'
                )
                
                variables_created += 3
                
            except Exception as e:
                print(f"❌ שגיאה ביצירת משתני סיכום עבור {soldier.name}: {e}")
                raise
        
        print(f"✅ נוצרו {variables_created} משתני סיכום")
    
    def _create_daily_count_variables(self) -> None:
        """יוצר משתני ספירה יומית"""
        print("📋 יוצר משתני ספירה יומית...")
        max_soldiers = len(self.soldiers)
        
        for day in self.calendar:
            try:
                # ספירת חיילים ביום
                self.daily_soldiers_count[day] = self.model.NewIntVar(
                    0, max_soldiers, f'daily_count_{day.isoformat()}'
                )
            except Exception as e:
                print(f"❌ שגיאה ביצירת משתנה ספירה ליום {day}: {e}")
                raise
        
        print(f"✅ נוצרו {len(self.calendar)} משתני ספירה יומית")
    
    def create_shortage_variables(self, min_required_soldiers: int) -> None:
        """
        יוצר משתני מחסור חיילים
        
        Args:
            min_required_soldiers: מספר חיילים מינימלי נדרש
        """
        for day in self.calendar:
            try:
                self.shortage_variables[day] = self.model.NewIntVar(
                    0, min_required_soldiers, f'shortage_{day.isoformat()}'
                )
            except Exception as e:
                print(f"❌ שגיאה ביצירת משתנה מחסור ליום {day}: {e}")
                raise
    
    def create_excess_variables(self, soldiers_names: List[str]) -> None:
        """
        יוצר משתני עודף עבור חיילים
        
        Args:
            soldiers_names: רשימת שמות חיילים
        """
        for soldier_name in soldiers_names:
            safe_name = self._create_safe_variable_name(soldier_name)
            try:
                self.excess_variables[soldier_name] = self.model.NewIntVar(
                    0, len(self.calendar), f'excess_{safe_name}'
                )
            except Exception as e:
                print(f"❌ שגיאה ביצירת משתנה עודף עבור {soldier_name}: {e}")
                raise
    
    def create_one_day_block_variables(self, soldier_name: str) -> Dict[str, Any]:
        """
        יוצר משתנים לזיהוי בלוקי יום אחד עבור חייל ספציפי
        
        Args:
            soldier_name: שם החייל
            
        Returns:
            Dict: משתני בלוק יום אחד
        """
        one_day_vars = {}
        num_days = len(self.calendar)
        safe_name = self._create_safe_variable_name(soldier_name)
        
        try:
            # בלוק יום אחד באמצע
            for i in range(1, num_days - 1):
                var_name = f'one_day_block_{safe_name}_{i}'
                one_day_vars[f'middle_{i}'] = self.model.NewBoolVar(var_name)
            
            # בלוק יום אחד בהתחלה
            if num_days > 1:
                var_name = f'one_day_block_start_{safe_name}_0'
                one_day_vars['start_0'] = self.model.NewBoolVar(var_name)
            
            # בלוק יום אחד בסוף
            if num_days > 1:
                var_name = f'one_day_block_end_{safe_name}_{num_days-1}'
                one_day_vars[f'end_{num_days-1}'] = self.model.NewBoolVar(var_name)
                
        except Exception as e:
            print(f"❌ שגיאה ביצירת משתני בלוק יום אחד עבור {soldier_name}: {e}")
            raise
        
        return one_day_vars
    
    def create_two_day_block_variables(self, soldier_name: str) -> Dict[int, Any]:
        """
        יוצר משתנים לזיהוי בלוקי יומיים עבור חייל ספציפי
        
        Args:
            soldier_name: שם החייל
            
        Returns:
            Dict: משתני בלוק יומיים
        """
        two_day_vars = {}
        num_days = len(self.calendar)
        safe_name = self._create_safe_variable_name(soldier_name)
        
        try:
            for i in range(num_days - 2):
                var_name = f'two_day_block_{safe_name}_{i}'
                two_day_vars[i] = self.model.NewBoolVar(var_name)
        except Exception as e:
            print(f"❌ שגיאה ביצירת משתני בלוק יומיים עבור {soldier_name}: {e}")
            raise
        
        return two_day_vars
    
    def create_long_block_variables(self, soldier_name: str, max_preferred_length: int) -> Dict[str, Any]:
        """
        יוצר משתנים לזיהוי בלוקים ארוכים עבור חייל ספציפי
        
        Args:
            soldier_name: שם החייל
            max_preferred_length: אורך מקסימלי מועדף
            
        Returns:
            Dict: משתני בלוקים ארוכים
        """
        long_block_vars = {}
        num_days = len(self.calendar)
        safe_name = self._create_safe_variable_name(soldier_name)
        
        try:
            for i in range(num_days):
                for length in range(max_preferred_length + 1, num_days - i + 1):
                    if i + length <= num_days:
                        var_name = f'long_block_{safe_name}_{i}_{length}'
                        long_block_vars[f'{i}_{length}'] = self.model.NewBoolVar(var_name)
        except Exception as e:
            print(f"❌ שגיאה ביצירת משתני בלוק ארוך עבור {soldier_name}: {e}")
            raise
        
        return long_block_vars
    
    def create_weekend_shortage_variables(self, soldier_name: str) -> Dict[str, Any]:
        """
        יוצר משתני מחסור עבור חיילי סופשים
        
        Args:
            soldier_name: שם החייל
            
        Returns:
            Dict: משתני מחסור סופשים
        """
        weekend_vars = {}
        safe_name = self._create_safe_variable_name(soldier_name)
        
        try:
            # מחסור ימי סופשים כללי
            weekend_vars['shortage'] = self.model.NewIntVar(
                0, 10, f'weekend_shortage_{safe_name}'
            )
        except Exception as e:
            print(f"❌ שגיאה ביצירת משתני מחסור סופשים עבור {soldier_name}: {e}")
            raise
        
        return weekend_vars
    
    def create_regular_shortage_variables(self, soldier_name: str, minimum_base: int) -> Dict[str, Any]:
        """
        יוצר משתני מחסור עבור חיילים רגילים
        
        Args:
            soldier_name: שם החייל
            minimum_base: מינימום ימי בסיס
            
        Returns:
            Dict: משתני מחסור
        """
        regular_vars = {}
        safe_name = self._create_safe_variable_name(soldier_name)
        
        try:
            regular_vars['shortage'] = self.model.NewIntVar(
                0, minimum_base, f'regular_shortage_{safe_name}'
            )
        except Exception as e:
            print(f"❌ שגיאה ביצירת משתני מחסור רגילים עבור {soldier_name}: {e}")
            raise
        
        return regular_vars
    
    def create_exceptional_shortage_variables(self, soldier_name: str, minimum_required: int) -> Dict[str, Any]:
        """
        יוצר משתני מחסור עבור חיילים חריגים
        
        Args:
            soldier_name: שם החייל
            minimum_required: מינימום נדרש
            
        Returns:
            Dict: משתני מחסור חריגים
        """
        exceptional_vars = {}
        safe_name = self._create_safe_variable_name(soldier_name)
        
        try:
            exceptional_vars['shortage'] = self.model.NewIntVar(
                0, minimum_required, f'exceptional_shortage_{safe_name}'
            )
        except Exception as e:
            print(f"❌ שגיאה ביצירת משתני מחסור חריגים עבור {soldier_name}: {e}")
            raise
        
        return exceptional_vars
    
    def create_fairness_variables(self, soldiers_names: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        יוצר משתני הוגנות עבור כל החיילים
        
        Args:
            soldiers_names: רשימת שמות חיילים
            
        Returns:
            Dict: משתני הוגנות
        """
        fairness_vars = {}
        
        for soldier_name in soldiers_names:
            safe_name = self._create_safe_variable_name(soldier_name)
            fairness_vars[soldier_name] = {}
            
            try:
                # סטיות מימי בסיס
                fairness_vars[soldier_name]['diff_base'] = self.model.NewIntVar(
                    -len(self.calendar), len(self.calendar), f'diff_base_{safe_name}'
                )
                
                # עודף ימי בסיס
                fairness_vars[soldier_name]['excess_base'] = self.model.NewIntVar(
                    0, len(self.calendar), f'excess_base_{safe_name}'
                )
                
                # מחסור ימי בסיס
                fairness_vars[soldier_name]['shortage_base'] = self.model.NewIntVar(
                    0, len(self.calendar), f'shortage_base_{safe_name}'
                )
                
                # סטיות מימי בית
                fairness_vars[soldier_name]['diff_home'] = self.model.NewIntVar(
                    -len(self.calendar), len(self.calendar), f'diff_home_{safe_name}'
                )
                
                # ערך מוחלט של סטיות ימי בית
                fairness_vars[soldier_name]['abs_diff_home'] = self.model.NewIntVar(
                    0, len(self.calendar), f'abs_diff_home_{safe_name}'
                )
                
            except Exception as e:
                print(f"❌ שגיאה ביצירת משתני הוגנות עבור {soldier_name}: {e}")
                raise
        
        return fairness_vars
    
    def create_weekend_bonus_variables(self, weekend_soldiers_names: List[str]) -> Dict[date, Any]:
        """
        יוצר משתני בונוס עבור חיילי סופשים
        
        Args:
            weekend_soldiers_names: רשימת שמות חיילי סופשים
            
        Returns:
            Dict: משתני בונוס סופשים
        """
        weekend_bonus_vars = {}
        
        for day in self.calendar:
            if day.weekday() in [4, 5]:  # שישי ושבת
                try:
                    weekend_bonus_vars[day] = self.model.NewIntVar(
                        0, len(weekend_soldiers_names), f'weekend_bonus_{day.isoformat()}'
                    )
                except Exception as e:
                    print(f"❌ שגיאה ביצירת משתנה בונוס סופשים ליום {day}: {e}")
                    raise
        
        return weekend_bonus_vars
    
    def get_assignment_variables(self) -> Tuple[Dict, Dict]:
        """
        מחזיר את משתני ההשמה הבסיסיים
        
        Returns:
            Tuple: (base_assignment, home_assignment)
        """
        if not self.base_assignment or not self.home_assignment:
            raise ValueError("❌ משתני השמה לא נוצרו עדיין")
        return self.base_assignment, self.home_assignment
    
    def get_block_variables(self) -> Tuple[Dict, Dict]:
        """
        מחזיר את משתני הבלוקים
        
        Returns:
            Tuple: (is_start_base, is_end_base)
        """
        if not self.is_start_base or not self.is_end_base:
            raise ValueError("❌ משתני בלוקים לא נוצרו עדיין")
        return self.is_start_base, self.is_end_base
    
    def get_summary_variables(self) -> Tuple[Dict, Dict, Dict]:
        """
        מחזיר את משתני הסיכום
        
        Returns:
            Tuple: (total_base_days, total_home_days, total_weekend_base_days)
        """
        if not self.total_soldier_base_days:
            raise ValueError("❌ משתני סיכום לא נוצרו עדיין")
        return (
            self.total_soldier_base_days,
            self.total_soldier_home_days,
            self.total_soldier_weekend_base_days
        )
    
    def get_daily_count_variables(self) -> Dict[date, Any]:
        """
        מחזיר את משתני הספירה היומית
        
        Returns:
            Dict: משתני ספירה יומית
        """
        if not self.daily_soldiers_count:
            raise ValueError("❌ משתני ספירה יומית לא נוצרו עדיין")
        return self.daily_soldiers_count
    
    def debug_variables_info(self) -> Dict[str, Any]:
        """מחזיר מידע debug על המשתנים שנוצרו"""
        return {
            'total_assignment_variables': len(self.base_assignment) + len(self.home_assignment),
            'total_summary_variables': len(self.total_soldier_base_days) * 3,
            'total_daily_variables': len(self.daily_soldiers_count),
            'soldiers_count': len(self.soldiers),
            'calendar_days': len(self.calendar),
            'safe_name_mappings': self.safe_name_mapping.copy(),
            'shortage_variables': len(self.shortage_variables),
            'block_variables': sum(len(v) for v in self.block_variables.values())
        }