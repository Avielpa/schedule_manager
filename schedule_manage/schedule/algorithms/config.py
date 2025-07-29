"""
📊 מודול הגדרות ופרמטרים - V9.0
מכיל את כל הקונסטנטות, ערכי ברירת מחדל, וצבעים עבור האלגוריתם
"""

# הגדרת צבעים לשימוש באקסל
COLOR_BASE = "C6EFCE"        # ירוק בהיר - בבסיס
COLOR_HOME = "FFC7CE"        # אדום בהיר - בבית
COLOR_WEEKEND = "FFEB9C"     # צהוב בהיר - סופ"ש בבסיס
COLOR_HEADER = "DCE6F1"      # כחול בהיר - כותרות
COLOR_SUMMARY = "F2F2F2"     # אפור בהיר - סיכומים

# 🚨 עונשים - ערכי ברירת מחדל (ניתנים להתאמה)
DEFAULT_DEATH_PENALTY_ONE_DAY_BLOCK = 10_000_000    # עונש קטלני על בלוק יום אחד
DEFAULT_DEATH_PENALTY_SHORTAGE = 1_000_000          # עונש קטלני על מחסור חיילים
DEFAULT_DEATH_PENALTY_NO_WORK = 5_000_000           # עונש קטלני על חייל ללא עבודה
DEFAULT_HEAVY_PENALTY_CONSTRAINTS = 500_000         # עונש כבד על הפרת אילוצים
DEFAULT_PENALTY_LONG_BLOCK = 20_000                 # עונש בסיסי לבלוק ארוך (לכל יום חריג)
DEFAULT_CRITICAL_PENALTY_LONG_BLOCK = 2_000_000     # עונש קטלני לבלוק ארוך מדי באופן מוגזם

# 📊 ספי אחוזים לניתוח בעיה
CONSTRAINT_RATIO_EXTREME = 0.5          # חיילים עם 50%+ אילוצים
CONSTRAINT_RATIO_HEAVY = 0.3            # חיילים עם 30%+ אילוצים
CONSTRAINT_RATIO_MODERATE = 0.15        # חיילים עם 15%+ אילוצים
CONSTRAINT_RATIO_EXTREME_WEEKEND = 0.4  # חיילי סופשים עם 40%+ אילוצים

# 🎯 ספי דירוג חיילים
CONSTRAINTS_LIGHT = 0.1                 # אילוצים קלים
CONSTRAINTS_MODERATE_RANK = 0.3         # אילוצים בינוניים לדירוג
CONSTRAINTS_HEAVY_RANK = 0.5            # אילוצים כבדים לדירוג

# 🏆 בונוסים וקנסות בדירוג
BONUS_NO_CONSTRAINTS = 0.3              # בונוס לחיילים ללא אילוצים
BONUS_LIGHT_CONSTRAINTS = 0.2           # בונוס לחיילים עם אילוצים קלים
PENALTY_HEAVY_CONSTRAINTS = 0.3         # קנס לחיילים עם אילוצים כבדים
PENALTY_MODERATE_CONSTRAINTS = 0.6      # קנס לחיילים עם אילוצים בינוניים
BONUS_WEEKEND_REGULAR = 0.1             # בונוס לחיילי סופשים רגילים
PENALTY_WEEKEND_CONSTRAINED = 0.4       # קנס לחיילי סופשים עם אילוצים

# ⚖️ פרמטרי איזון והתאמה
MIN_ABSOLUTE_SOLDIERS_THRESHOLD = 3     # מינימום מוחלט חיילים ביום
BASE_MIN_REGULAR_DAYS_THRESHOLD = 5     # מינימום ימי עבודה לחיילים רגילים
BASE_MIN_WEEKEND_DAYS_THRESHOLD = 2     # מינימום סופשים לחיילי סופשים

# 🔧 פרמטרי התאמה דינמית לפי רמת קושי
DIFFICULTY_ADAPTATIONS = {
    "APOCALYPTIC": {
        "base_days_multiplier": 0.5,
        "home_days_multiplier": 1.5,
        "soldiers_reduction": 3,
        "flexibility_range": 3
    },
    "CATASTROPHIC": {
        "base_days_multiplier": 0.6,
        "home_days_multiplier": 1.4,
        "soldiers_reduction": 2,
        "flexibility_range": 3
    },
    "EXTREME": {
        "base_days_multiplier": 0.7,
        "home_days_multiplier": 1.3,
        "soldiers_reduction": 1,
        "flexibility_range": 2
    },
    "VERY_HARD": {
        "base_days_multiplier": 0.8,
        "home_days_multiplier": 1.2,
        "soldiers_reduction": 1,
        "flexibility_range": 1
    },
    "HARD": {
        "base_days_multiplier": 0.9,
        "home_days_multiplier": 1.1,
        "soldiers_reduction": 0,
        "flexibility_range": 1
    },
    "MEDIUM": {
        "base_days_multiplier": 1.0,
        "home_days_multiplier": 1.0,
        "soldiers_reduction": 0,
        "flexibility_range": 0
    },
    "EASY": {
        "base_days_multiplier": 1.0,
        "home_days_multiplier": 1.0,
        "soldiers_reduction": 0,
        "flexibility_range": 0
    }
}

# 🧮 פרמטרי מינימום לחיילים חריגים
HIGH_CONSTRAINT_RATIO = 0.65           # יחס אילוצים גבוה
MEDIUM_CONSTRAINT_RATIO = 0.5          # יחס אילוצים בינוני
LOW_CONSTRAINT_RATIO = 0.35            # יחס אילוצים נמוך

# 📈 פרמטרי מינימום דינמיים לחיילים חריגים
EXCEPTIONAL_MINIMUMS = {
    "weekend_high_constraint": {"min": 2, "max": 4, "ratio": 0.3},
    "weekend_medium_constraint": {"min": 3, "max": 6, "ratio": 0.5},
    "regular_high_constraint": {"min": 5, "max": 8, "ratio": 0.33},
    "regular_medium_constraint": {"min": 8, "max": 12, "ratio": 0.5},
    "regular_low_constraint": {"min": 10, "max": 15, "ratio": 0.6},
    "regular_safe": {"min": 12, "max": 18, "ratio": 0.7}
}

# 🎨 עיצוב אקסל - הגדרות נוספות
EXCEL_COLUMN_WIDTH_NAME = 15           # רוחב עמודת שמות
EXCEL_COLUMN_WIDTH_DATE = 10           # רוחב עמודות תאריכים
EXCEL_COLUMN_WIDTH_SUMMARY = 12        # רוחב עמודות סיכום

# 🎛️ הגדרות ברירת מחדל למחלקה הראשית
DEFAULT_MIN_BASE_BLOCK_DAYS = 3         # מינימום ימים בבלוק בסיס
DEFAULT_FLEXIBLE_DAILY_REQUIREMENT = False  # גמישות בדרישה יומית

# 📅 הגדרות יום בשבוע
FRIDAY_WEEKDAY = 4                      # יום שישי
SATURDAY_WEEKDAY = 5                    # יום שבת  
SUNDAY_WEEKDAY = 6                      # יום ראשון

# 🎯 משקלי עונשים נוספים
WEEKEND_SHORTAGE_PENALTY_MULTIPLIER = 0.5  # מכפיל עונש מחסור בסופ"ש
WEEKEND_BONUS_VALUE = -50000               # בונוס לחיילי סופשים בסופ"ש
FAIRNESS_PENALTY_BASE = 1000               # עונש בסיסי לאי הוגנות
FAIRNESS_PENALTY_HOME = 1000               # עונש לסטיות ימי בית
EXCESS_BASE_PENALTY_MULTIPLIER = 2         # מכפיל עונש על עודף ימי בסיס
SHORTAGE_BASE_PENALTY_DIVISOR = 4          # מחלק עונש על מחסור ימי בסיס

# 🔧 הגדרות גמישות לחיילים כבדי אילוצים
HEAVY_CONSTRAINTS_THRESHOLD = 0.4           # סף לחיילים כבדי אילוצים
HOME_FLEXIBILITY_MULTIPLIER = 0.2          # אחוז תוספת גמישות ימי בית
BASE_FLEXIBILITY_MULTIPLIER = 0.1          # אחוז תוספת גמישות ימי בסיס

# 📊 הגדרות לניתוח זמינות חיילים
AVAILABILITY_SCORING = {
    "no_constraints_bonus": 0.3,
    "light_constraints_bonus": 0.2,
    "heavy_constraints_penalty": 0.3,
    "moderate_constraints_penalty": 0.6,
    "weekend_regular_bonus": 0.1,
    "weekend_constrained_penalty": 0.4
}

# 🏁 הגדרות סוף פתרון
MAX_DISPLAY_SOLDIERS = 8               # מספר מקסימלי חיילים להצגה בדיווח