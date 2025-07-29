"""
🧠 מודול ניתוח בעיה ופרמטרים דינמיים - V9.0
מכיל את כל הלוגיקה החכמה לניתוח הבעיה והתאמת פרמטרים
"""

from typing import List, Dict, Any, Tuple
from datetime import date

from .config import (
    CONSTRAINT_RATIO_EXTREME, CONSTRAINT_RATIO_HEAVY, CONSTRAINT_RATIO_MODERATE,
    CONSTRAINT_RATIO_EXTREME_WEEKEND, AVAILABILITY_SCORING, DIFFICULTY_ADAPTATIONS,
    HIGH_CONSTRAINT_RATIO, MEDIUM_CONSTRAINT_RATIO, LOW_CONSTRAINT_RATIO,
    EXCEPTIONAL_MINIMUMS, MAX_DISPLAY_SOLDIERS
)
from .utils import (
    calculate_constraints_ratio, calculate_available_days, 
    print_analysis_summary, print_soldiers_ranking, print_difficulty_adaptation,
    calculate_weekend_count
)


class ProblemAnalyzer:
    """מחלקה לניתוח בעיות ותכנון אסטרטגיה"""
    
    def __init__(self, soldiers: List, calendar: List[date], min_required_soldiers: int):
        self.soldiers = soldiers
        self.calendar = calendar
        self.total_days = len(calendar)
        self.min_required_soldiers = min_required_soldiers
        
    def perform_extreme_analysis(self) -> Dict[str, Any]:
        """
        ניתוח מתקדם של בעיות קיצוניות - V9.0
        
        Returns:
            Dict: תוצאות הניתוח המפורטות
        """
        total_constraints = sum(len(s.raw_constraints) for s in self.soldiers)
        
        # סיווג חיילים לפי רמת אילוצים
        extreme_constrained = [
            s for s in self.soldiers 
            if len(s.raw_constraints) > self.total_days * CONSTRAINT_RATIO_EXTREME
        ]
        heavily_constrained = [
            s for s in self.soldiers 
            if self.total_days * CONSTRAINT_RATIO_HEAVY < len(s.raw_constraints) <= self.total_days * CONSTRAINT_RATIO_EXTREME
        ]
        moderately_constrained = [
            s for s in self.soldiers 
            if self.total_days * CONSTRAINT_RATIO_MODERATE < len(s.raw_constraints) <= self.total_days * CONSTRAINT_RATIO_HEAVY
        ]
        lightly_constrained = [
            s for s in self.soldiers 
            if 0 < len(s.raw_constraints) <= self.total_days * CONSTRAINT_RATIO_MODERATE
        ]
        no_constraints = [
            s for s in self.soldiers 
            if len(s.raw_constraints) == 0
        ]
        
        # ניתוח חיילי סופשים
        weekend_soldiers = [s for s in self.soldiers if s.is_weekend_only_soldier_flag]
        extreme_weekend_soldiers = [
            s for s in weekend_soldiers 
            if len(s.raw_constraints) > self.total_days * CONSTRAINT_RATIO_EXTREME_WEEKEND
        ]
        
        # חישוב יחס זמינות
        total_available_days = sum(
            calculate_available_days(s, self.total_days) for s in self.soldiers
        )
        required_base_days = self.total_days * self.min_required_soldiers
        availability_ratio = total_available_days / required_base_days if required_base_days > 0 else 1.0
        
        # קביעת רמת קושי משופרת
        difficulty = self._determine_difficulty(
            extreme_constrained, heavily_constrained, availability_ratio
        )
        
        analysis = {
            'total_days': self.total_days,
            'total_constraints': total_constraints,
            'extreme_constrained': len(extreme_constrained),
            'heavily_constrained': len(heavily_constrained),
            'moderately_constrained': len(moderately_constrained),
            'lightly_constrained': len(lightly_constrained),
            'no_constraints': len(no_constraints),
            'weekend_soldiers': len(weekend_soldiers),
            'extreme_weekend_soldiers': len(extreme_weekend_soldiers),
            'availability_ratio': availability_ratio,
            'difficulty': difficulty,
            'extreme_constrained_soldiers': extreme_constrained,
            'heavily_constrained_soldiers': heavily_constrained,
            'no_constraints_soldiers': no_constraints,
            'weekend_soldiers_list': weekend_soldiers,
            'extreme_weekend_soldiers_list': extreme_weekend_soldiers
        }
        
        print_analysis_summary(analysis)
        return analysis
    
    def _determine_difficulty(self, extreme_constrained: List, heavily_constrained: List, 
                            availability_ratio: float) -> str:
        """
        קובע את רמת הקושי של הבעיה
        
        Args:
            extreme_constrained: חיילים עם אילוצים קיצוניים
            heavily_constrained: חיילים עם אילוצים כבדים
            availability_ratio: יחס הזמינות
            
        Returns:
            str: רמת הקושי
        """
        if len(extreme_constrained) >= 3:
            return "APOCALYPTIC"
        elif len(extreme_constrained) >= 2:
            return "CATASTROPHIC"
        elif len(extreme_constrained) >= 1:
            return "EXTREME"
        elif len(heavily_constrained) >= len(self.soldiers) * 0.3:
            return "VERY_HARD"
        elif len(heavily_constrained) >= len(self.soldiers) * 0.2:
            return "HARD"
        elif availability_ratio < 1.2:
            return "MEDIUM"
        else:
            return "EASY"
    
    def rank_soldiers_by_availability(self) -> List[Tuple]:
        """
        מדרג חיילים לפי זמינותם - גרסה מתקדמת V9.0
        
        Returns:
            List[Tuple]: רשימת חיילים עם ציונים ממוינת
        """
        soldiers_with_score = []
        
        for soldier in self.soldiers:
            constraints_ratio = calculate_constraints_ratio(soldier, self.total_days)
            available_days = calculate_available_days(soldier, self.total_days)
            
            availability_score = available_days / self.total_days
            
            # יישום בונוסים וקנסות
            availability_score = self._apply_availability_bonuses_penalties(
                availability_score, constraints_ratio, soldier
            )
            
            soldiers_with_score.append((soldier, availability_score))
        
        soldiers_with_score.sort(key=lambda x: x[1], reverse=True)
        print_soldiers_ranking(soldiers_with_score, MAX_DISPLAY_SOLDIERS)
        
        return soldiers_with_score
    
    def _apply_availability_bonuses_penalties(self, base_score: float, 
                                            constraints_ratio: float, soldier) -> float:
        """
        מיישם בונוסים וקנסות על ציון הזמינות
        
        Args:
            base_score: ציון בסיסי
            constraints_ratio: יחס אילוצים
            soldier: אובייקט החייל
            
        Returns:
            float: ציון מעודכן
        """
        score = base_score
        
        # בונוסים וקנסות לפי רמת אילוצים
        if len(soldier.raw_constraints) == 0:
            score += AVAILABILITY_SCORING["no_constraints_bonus"]
        elif constraints_ratio <= 0.1:
            score += AVAILABILITY_SCORING["light_constraints_bonus"]
        elif constraints_ratio >= 0.5:
            score *= AVAILABILITY_SCORING["heavy_constraints_penalty"]
        elif constraints_ratio >= 0.3:
            score *= AVAILABILITY_SCORING["moderate_constraints_penalty"]
        
        # התאמות לחיילי סופשים
        if soldier.is_weekend_only_soldier_flag:
            if constraints_ratio <= 0.3:
                score += AVAILABILITY_SCORING["weekend_regular_bonus"]
            else:
                score *= AVAILABILITY_SCORING["weekend_constrained_penalty"]
        
        return score


class ParameterAdapter:
    """מחלקה להתאמת פרמטרים דינמית"""
    
    def __init__(self, analysis: Dict[str, Any], original_params: Dict[str, Any]):
        self.analysis = analysis
        self.original_params = original_params
        
    def adapt_parameters_for_difficulty(self) -> Dict[str, Any]:
        """
        מתאים את הפרמטרים לבעיות קיצוניות - V9.0
        
        Returns:
            Dict: פרמטרים מותאמים
        """
        difficulty = self.analysis['difficulty']
        adapted_params = self.original_params.copy()
        
        if difficulty in DIFFICULTY_ADAPTATIONS:
            adaptation = DIFFICULTY_ADAPTATIONS[difficulty]
            
            # התאמת יעדי ימי בסיס ובית
            adapted_params['base_days_target'] = max(
                10, 
                int(self.original_params['base_days_target'] * adaptation['base_days_multiplier'])
            )
            adapted_params['home_days_target'] = min(
                45, 
                int(self.original_params['home_days_target'] * adaptation['home_days_multiplier'])
            )
            
            # התאמת דרישה יומית
            adapted_params['min_required_soldiers'] = max(
                4, 
                self.original_params['min_required_soldiers'] - adaptation['soldiers_reduction']
            )
            
            # הפעלת גמישות
            adapted_params['flexible_daily_requirement'] = True
            adapted_params['flexibility_range'] = adaptation['flexibility_range']
            
            print_difficulty_adaptation(
                difficulty,
                adapted_params['base_days_target'],
                adapted_params['home_days_target'],
                adapted_params['min_required_soldiers']
            )
        
        return adapted_params


class ExceptionalSoldiersAnalyzer:
    """מחלקה לניתוח וחישוב מינימום לחיילים חריגים"""
    
    def __init__(self, soldiers: List, calendar: List[date]):
        self.soldiers = soldiers
        self.calendar = calendar
        self.total_days = len(calendar)
        
    def calculate_exceptional_minimums(self) -> Dict[str, int]:
        """
        🚨 מחשב מינימום קשיח לחיילים חריגים - V9.0
        
        Returns:
            Dict[str, int]: מינימום לכל חייל חריג
        """
        minimums = {}
        
        print(f"🚨 מחשב מינימום קשיח לחיילים חריגים:")
        
        for soldier in self.soldiers:
            available_days = calculate_available_days(soldier, self.total_days)
            constraints_ratio = calculate_constraints_ratio(soldier, self.total_days)
            
            if soldier.is_exceptional_output or constraints_ratio >= MEDIUM_CONSTRAINT_RATIO:
                minimum = self._calculate_soldier_minimum(
                    soldier, available_days, constraints_ratio
                )
                if minimum > 0:
                    minimums[soldier.name] = minimum
        
        print(f"    📊 סה\"כ {len(minimums)} חיילים עם מינימום קשיח")
        return minimums
    
    def _calculate_soldier_minimum(self, soldier, available_days: int, constraints_ratio: float) -> int:
        """
        מחשב מינימום עבור חייל ספציפי
        
        Args:
            soldier: אובייקט החייל
            available_days: ימים זמינים
            constraints_ratio: יחס אילוצים
            
        Returns:
            int: מינימום ימי עבודה
        """
        if soldier.is_weekend_only_soldier_flag:
            return self._calculate_weekend_soldier_minimum(constraints_ratio)
        else:
            return self._calculate_regular_soldier_minimum(available_days, constraints_ratio)
    
    def _calculate_weekend_soldier_minimum(self, constraints_ratio: float) -> int:
        """
        מחשב מינימום עבור חייל סופשים
        
        Args:
            constraints_ratio: יחס אילוצים
            
        Returns:
            int: מינימום סופשים
        """
        max_possible_weekends = calculate_weekend_count(self.calendar)
        weekend_blocks = max_possible_weekends // 3  # סופשים אפשריים
        
        if constraints_ratio >= HIGH_CONSTRAINT_RATIO:
            config = EXCEPTIONAL_MINIMUMS["weekend_high_constraint"]
        else:
            config = EXCEPTIONAL_MINIMUMS["weekend_medium_constraint"]
        
        minimum = max(
            config["min"], 
            min(config["max"], int(weekend_blocks * config["ratio"]))
        )
        
        print(f"    🏖️ {getattr(self.soldiers[0], 'name', 'Unknown')}: מינימום {minimum} סופשים (מתוך {weekend_blocks} אפשריים)")
        return minimum
    
    def _calculate_regular_soldier_minimum(self, available_days: int, constraints_ratio: float) -> int:
        """
        מחשב מינימום עבור חייל רגיל - גרסה מחמירה למקרים קיצוניים
        
        Args:
            available_days: ימים זמינים
            constraints_ratio: יחס אילוצים
            
        Returns:
            int: מינימום ימי בסיס
        """
        # 🚨 לחיילים עם אילוצים רבים - מינימום חמור יותר
        if constraints_ratio >= HIGH_CONSTRAINT_RATIO:
            config = EXCEPTIONAL_MINIMUMS["regular_high_constraint"]
            # חמור יותר: מינימום 10 במקום 5
            minimum = max(10, min(config["max"], int(available_days * config["ratio"])))
        elif constraints_ratio >= MEDIUM_CONSTRAINT_RATIO:
            config = EXCEPTIONAL_MINIMUMS["regular_medium_constraint"] 
            # חמור יותר: מינימום 12 במקום 8
            minimum = max(12, min(config["max"], int(available_days * config["ratio"])))
        elif constraints_ratio >= LOW_CONSTRAINT_RATIO:
            config = EXCEPTIONAL_MINIMUMS["regular_low_constraint"]
            # חמור יותר: מינימום 15 במקום 10
            minimum = max(15, min(config["max"], int(available_days * config["ratio"])))
        else:
            config = EXCEPTIONAL_MINIMUMS["regular_safe"]
            # חמור יותר: מינימום 18 במקום 12
            minimum = max(18, min(config["max"], int(available_days * config["ratio"])))
        
        print(f"    ⚠️ חייל רגיל: מינימום {minimum} ימי בסיס (זמין {available_days}, יחס אילוצים {constraints_ratio:.2f})")
        return minimum


def analyze_soldiers_specific_parameters(soldiers: List, max_consecutive_home_days: int,
                                       default_home_days_target: int, calendar_length: int) -> None:
    """
    מפעילה את פונקציית הניתוח הספציפית של כל חייל
    
    Args:
        soldiers: רשימת החיילים
        max_consecutive_home_days: מקסימום ימי בית רצופים
        default_home_days_target: יעד ימי בית ברירת מחדל
        calendar_length: אורך לוח הזמנים
    """
    for soldier in soldiers:
        if hasattr(soldier, 'analyze_soldier_specific_parameters'):
            soldier.analyze_soldier_specific_parameters(
                global_max_consecutive_home_days=max_consecutive_home_days,
                global_default_home_days_target=default_home_days_target,
                calendar_length=calendar_length
            )