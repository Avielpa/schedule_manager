"""
💀 אילוצי בלוקים - V9.0
מטפל בבלוקי יום אחד, זיהוי בלוקים, ובלוקים ארוכים מדי
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..solver import SmartScheduleSoldiers


class BlockConstraints:
    """מחלקה לניהול אילוצי בלוקים"""
    
    def __init__(self, solver_instance: 'SmartScheduleSoldiers'):
        self.solver = solver_instance
        self.model = solver_instance.model
        self.soldiers = solver_instance.soldiers
        self.calendar = solver_instance.calendar
        self.variables = solver_instance.variables
        self.penalty_one_day_block = solver_instance.penalty_one_day_block
        self.penalty_long_block = solver_instance.penalty_long_block
        self.critical_penalty_long_block = solver_instance.critical_penalty_long_block
        self.min_base_block_days = solver_instance.min_base_block_days
        self.max_consecutive_base_days = solver_instance.max_consecutive_base_days
        
    def apply(self) -> None:
        """מיישם את כל אילוצי הבלוקים"""
        print("💀 מוסיף אילוצי בלוקים...")
        
        for soldier in self.soldiers:
            print(f"    🔧 {soldier.name}: מגדיר אילוצי בלוקים")
            self._add_block_identification_constraints(soldier)
            self._add_absolute_death_penalty_one_day_blocks(soldier)
            self._add_enhanced_block_constraints(soldier)
        
        print("✅ אילוצי בלוקים הושמו בהצלחה")
    
    def _add_block_identification_constraints(self, soldier) -> None:
        """
        מוסיף אילוצים לזיהוי התחלה וסוף של בלוקי בסיס
        
        Args:
            soldier: אובייקט החייל
        """
        base_assignment, home_assignment = self.variables.get_assignment_variables()
        is_start_base, is_end_base = self.variables.get_block_variables()
        num_days = len(self.calendar)
        
        for i in range(num_days):
            current_day = self.calendar[i]
            key_current = (soldier.name, current_day)
            
            # זיהוי התחלת בלוק בסיס
            if i == 0:
                # יום ראשון: התחלת בלוק אם בבסיס
                self.model.Add(is_start_base[key_current] == base_assignment[key_current])
            else:
                prev_day = self.calendar[i-1]
                key_prev = (soldier.name, prev_day)
                
                # התחלת בלוק: בבסיס היום ובבית אתמול
                self.model.AddBoolAnd([
                    base_assignment[key_current], 
                    home_assignment[key_prev]
                ]).OnlyEnforceIf(is_start_base[key_current])
                
                self.model.AddBoolOr([
                    base_assignment[key_current].Not(), 
                    home_assignment[key_prev].Not()
                ]).OnlyEnforceIf(is_start_base[key_current].Not())
            
            # זיהוי סוף בלוק בסיס
            if i == num_days - 1:
                # יום אחרון: סוף בלוק אם בבסיס
                self.model.Add(is_end_base[key_current] == base_assignment[key_current])
            else:
                next_day = self.calendar[i+1]
                key_next = (soldier.name, next_day)
                
                # סוף בלוק: בבסיס היום ובבית מחר
                self.model.AddBoolAnd([
                    base_assignment[key_current], 
                    home_assignment[key_next]
                ]).OnlyEnforceIf(is_end_base[key_current])
                
                self.model.AddBoolOr([
                    base_assignment[key_current].Not(), 
                    home_assignment[key_next].Not()
                ]).OnlyEnforceIf(is_end_base[key_current].Not())
    
    def _add_absolute_death_penalty_one_day_blocks(self, soldier) -> None:
        """
        💀 עונש קטלני מוחלט על בלוק יום אחד - מחמיר מאוד!
        
        Args:
            soldier: אובייקט החייל
        """
        base_assignment, home_assignment = self.variables.get_assignment_variables()
        num_days = len(self.calendar)
        
        print(f"        💀 איסור מוחלט בלוק יום אחד עבור {soldier.name}")
        
        # 🚨 איסור מוחלט בלוק יום אחד - אילוץ קשיח!
        for i in range(num_days - 1):
            current_day = self.calendar[i]
            next_day = self.calendar[i + 1]
            
            current_key = (soldier.name, current_day)
            next_key = (soldier.name, next_day)
            
            # אילוץ קשיח: אם בבסיס היום, אסור בבסיס מחר
            # זה מונע לחלוטין רצפים של יום בסיס בודד
            one_day_block_var = self.model.NewBoolVar(f'forbidden_consecutive_{soldier.name}_{i}')
            
            # אם בבסיס היום ובבית מחר ואחרי מחר בבסיס - זה אסור
            if i < num_days - 2:
                day_after_next = self.calendar[i + 2]
                day_after_next_key = (soldier.name, day_after_next)
                
                # בלוק יום אחד: בסיס -> בית -> בסיס (אסור!)
                self.model.AddBoolAnd([
                    base_assignment[current_key],
                    home_assignment[next_key],
                    base_assignment[day_after_next_key]
                ]).OnlyEnforceIf(one_day_block_var)
                
                # עונש קטלני על בלוק יום אחד
                self.solver.objective_terms.append(one_day_block_var * self.penalty_one_day_block)
            
            # גם בודק בלוק יום אחד בהתחלה ובסוף
            if i == 0:  # התחלה
                is_start_single = self.model.NewBoolVar(f'start_single_{soldier.name}')
                self.model.AddBoolAnd([
                    base_assignment[current_key],
                    home_assignment[next_key]
                ]).OnlyEnforceIf(is_start_single)
                
                if num_days > 2:
                    day2 = self.calendar[2]
                    day2_key = (soldier.name, day2)
                    # אם גם ביום השלישי בבסיס - זה בלוק יום אחד
                    start_single_block = self.model.NewBoolVar(f'start_single_block_{soldier.name}')
                    self.model.AddBoolAnd([
                        is_start_single,
                        base_assignment[day2_key]
                    ]).OnlyEnforceIf(start_single_block)
                    self.solver.objective_terms.append(start_single_block * self.penalty_one_day_block)
            
            if i == num_days - 2:  # סוף
                is_end_single = self.model.NewBoolVar(f'end_single_{soldier.name}')
                self.model.AddBoolAnd([
                    home_assignment[current_key],
                    base_assignment[next_key]
                ]).OnlyEnforceIf(is_end_single)
                
                if num_days > 2:
                    prev_day = self.calendar[i - 1]
                    prev_key = (soldier.name, prev_day)
                    # אם גם ביום הקודם בבסיס - זה בלוק יום אחד
                    end_single_block = self.model.NewBoolVar(f'end_single_block_{soldier.name}')
                    self.model.AddBoolAnd([
                        base_assignment[prev_key],
                        is_end_single
                    ]).OnlyEnforceIf(end_single_block)
                    self.solver.objective_terms.append(end_single_block * self.penalty_one_day_block)
    
    def _add_two_day_block_penalties(self, soldier, base_assignment, home_assignment) -> None:
        """
        מוסיף עונש על בלוקי יומיים
        
        Args:
            soldier: אובייקט החייל
            base_assignment: משתני השמה לבסיס
            home_assignment: משתני השמה לבית
        """
        num_days = len(self.calendar)
        two_day_vars = self.variables.create_two_day_block_variables(soldier.name)
        
        print(f"        💀 עונש קטלני נוסף על בלוקי יומיים")
        
        for i in range(num_days - 2):
            if i in two_day_vars and i + 3 < num_days:
                day1 = self.calendar[i]
                day2 = self.calendar[i+1]
                day3 = self.calendar[i+2]
                day4 = self.calendar[i+3]
                
                is_two_day_block = two_day_vars[i]
                
                # מקרה: X בבית, יום1 בבסיס, יום2 בבסיס, יום3 בבית
                self.model.AddBoolAnd([
                    home_assignment[(soldier.name, day1)],
                    base_assignment[(soldier.name, day2)],
                    base_assignment[(soldier.name, day3)],
                    home_assignment[(soldier.name, day4)]
                ]).OnlyEnforceIf(is_two_day_block)
                
                self.solver.objective_terms.append(is_two_day_block * self.penalty_one_day_block)
    
    def _add_enhanced_block_constraints(self, soldier) -> None:
        """
        💡 מוסיף אילוצי בלוק משופרים - טיפול בבלוקים ארוכים מדי
        
        Args:
            soldier: אובייקט החייל
        """
        base_assignment, _ = self.variables.get_assignment_variables()
        is_start_base, _ = self.variables.get_block_variables()
        num_days = len(self.calendar)
        
        # אילוץ קשיח: אם מתחיל בלוק, חייב להמשיך לפחות min_base_block_days
        self._add_minimum_block_length_constraints(soldier, is_start_base, base_assignment)
        
        # טיפול משופר בבלוקים ארוכים מדי: עונשים פרופורציונליים וקטלניים
        self._add_long_block_penalties(soldier, base_assignment)
    
    def _add_minimum_block_length_constraints(self, soldier, is_start_base, base_assignment) -> None:
        """
        מוסיף אילוץ קשיח על אורך מינימלי של בלוק
        
        Args:
            soldier: אובייקט החייל
            is_start_base: משתני התחלת בלוק
            base_assignment: משתני השמה לבסיס
        """
        num_days = len(self.calendar)
        
        for i in range(num_days - self.min_base_block_days + 1):
            start_day = self.calendar[i]
            start_key = (soldier.name, start_day)
            
            for j in range(1, self.min_base_block_days):
                if i + j < num_days:
                    continue_day = self.calendar[i + j]
                    continue_key = (soldier.name, continue_day)
                    
                    self.model.AddImplication(
                        is_start_base[start_key], 
                        base_assignment[continue_key]
                    )
    
    def _add_long_block_penalties(self, soldier, base_assignment) -> None:
        """
        מוסיף עונשים פרופורציונליים לבלוקים ארוכים
        
        Args:
            soldier: אובייקט החייל
            base_assignment: משתני השמה לבסיס
        """
        num_days = len(self.calendar)
        max_preferred_block_length = self.max_consecutive_base_days
        critical_long_block_threshold = int(max_preferred_block_length * 1.5)
        
        # יצירת משתני בלוקים ארוכים
        long_block_vars = self.variables.create_long_block_variables(
            soldier.name, max_preferred_block_length
        )
        
        penalties_added = 0
        critical_penalties_added = 0
        
        # עובר על כל יום אפשרי כנקודת התחלה לבלוק
        for i in range(num_days):
            # עבור כל אורך אפשרי מעבר למקסימום המועדף
            for length in range(max_preferred_block_length + 1, num_days - i + 1):
                if i + length <= num_days:
                    var_key = f'{i}_{length}'
                    
                    if var_key in long_block_vars:
                        is_current_block_long = long_block_vars[var_key]
                        
                        # אילוץ המקשר את המשתנה הבוליאני לקיום הבלוק
                        self.model.AddBoolAnd([
                            base_assignment[(soldier.name, self.calendar[j])]
                            for j in range(i, i + length)
                        ]).OnlyEnforceIf(is_current_block_long)
                        
                        # הוסף עונש פרופורציונלי לאורך החריגה
                        excess_length = length - max_preferred_block_length
                        penalty_for_this_block = excess_length * self.penalty_long_block
                        self.solver.objective_terms.append(is_current_block_long * penalty_for_this_block)
                        penalties_added += 1
                        
                        # עונש קטלני אם הבלוק ארוך באופן מוגזם
                        if length >= critical_long_block_threshold:
                            self.solver.objective_terms.append(
                                is_current_block_long * self.critical_penalty_long_block
                            )
                            critical_penalties_added += 1
                            print(f"            💀 עונש קטלני על בלוק באורך {length} מיום {self.calendar[i].isoformat()}")
        
        if penalties_added > 0:
            print(f"        📏 הוספו {penalties_added} עונשי בלוקים ארוכים ({critical_penalties_added} קטלניים)")
    
    def validate_block_constraints(self) -> bool:
        """
        מוודא שאילוצי הבלוקים הגיוניים
        
        Returns:
            bool: True אם האילוצים תקינים
        """
        if self.min_base_block_days < 1:
            print(f"❌ שגיאה: מינימום ימי בלוק לא תקין: {self.min_base_block_days}")
            return False
        
        if self.max_consecutive_base_days < self.min_base_block_days:
            print(f"❌ שגיאה: מקסימום ימי בסיס ({self.max_consecutive_base_days}) קטן ממינימום בלוק ({self.min_base_block_days})")
            return False
        
        if len(self.calendar) < self.min_base_block_days:
            print(f"❌ שגיאה: לוח זמנים קצר מדי ({len(self.calendar)}) למינימום בלוק ({self.min_base_block_days})")
            return False
        
        print("✅ אילוצי בלוקים תקינים")
        return True
    
    def get_block_constraints_summary(self) -> dict:
        """
        מחזיר סיכום אילוצי הבלוקים
        
        Returns:
            dict: סיכום האילוצים
        """
        return {
            'min_base_block_days': self.min_base_block_days,
            'max_consecutive_base_days': self.max_consecutive_base_days,
            'penalty_one_day_block': self.penalty_one_day_block,
            'penalty_long_block': self.penalty_long_block,
            'critical_penalty_long_block': self.critical_penalty_long_block,
            'critical_threshold': int(self.max_consecutive_base_days * 1.5)
        }