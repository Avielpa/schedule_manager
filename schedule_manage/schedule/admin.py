# schedule/admin.py

from django.contrib import admin
from .models import Soldier, SoldierConstraint, SchedulingRun, Assignment,Event
from django.urls import reverse
from django.utils.html import format_html


# ממשק אדמין מותאם אישית עבור Soldier
@admin.register(Soldier)
class SoldierAdmin(admin.ModelAdmin):
    list_display = ('name', 'get_num_constraints')
    search_fields = ('name',)
    list_display_links = ('name',)

    def get_num_constraints(self, obj):
        return obj.constraints.count()
    get_num_constraints.short_description = "מס' אילוצים"


# ממשק אדמין מותאם אישית עבור SoldierConstraint
@admin.register(SoldierConstraint)
class SoldierConstraintAdmin(admin.ModelAdmin):
    list_display = ('soldier', 'constraint_date', 'description')
    list_filter = ('constraint_date', 'soldier__name')
    search_fields = ('soldier__name', 'description')
    list_editable = ('constraint_date', 'description')
    raw_id_fields = ('soldier',)


# ממשק אדמין מותאם אישית עבור Assignment
@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ('soldier', 'assignment_date', 'is_on_base', 'scheduling_run_link')
    list_filter = ('assignment_date', 'is_on_base', 'soldier__name', 'scheduling_run')
    search_fields = ('soldier__name', 'assignment_date',)
    list_display_links = ('soldier', 'assignment_date',)
    list_per_page = 25

    def scheduling_run_link(self, obj):
        if obj.scheduling_run:
            # **התיקון כאן: שינוי ל-'schedule'_schedulingrun_change**
            link = reverse("admin:schedule_schedulingrun_change", args=[obj.scheduling_run.id])
            return format_html('<a href="{}">{}</a>', link, obj.scheduling_run.id)
        return "N/A"
    scheduling_run_link.short_description = "הרצת שיבוץ"


# Inline עבור Assignments בתוך SchedulingRun
class AssignmentInline(admin.TabularInline):
    model = Assignment
    extra = 0
    fields = ('soldier', 'assignment_date', 'is_on_base')
    readonly_fields = ('soldier', 'assignment_date', 'is_on_base')
    can_delete = False
    show_change_link = True


# @admin.register(SchedulingRun)
# class SchedulingRunAdmin(admin.ModelAdmin):
#     list_display = ('id',
#         'run_date', 'start_date', 'end_date', 'status', 
#         'default_base_days_target', 'min_required_soldiers_per_day', 
#         'get_num_assignments'
#     )
#     list_filter = ('status', 'run_date', 'start_date', 'end_date')
#     search_fields = ('solution_details',)
#     readonly_fields = (
#         'run_date', 'start_date', 'end_date', 'default_base_days_target',
#         'default_home_days_target', 'max_consecutive_base_days',
#         'max_consecutive_home_days', 'min_base_block_days',
#         'min_required_soldiers_per_day', 'max_total_home_days',
#         'status', 'solution_details'
#     )
#     inlines = [AssignmentInline]

#     def get_num_assignments(self, obj):
#         return obj.assignments.count()
#     get_num_assignments.short_description = "מס' שיבוצים"


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = (
        'name', 
        'event_type', 
        'start_date', 
        'end_date', 
        'min_required_soldiers',  # הוספה לתצוגה
        'soldier_constraint_display'
    )
    list_filter = (
        'event_type', 
        'start_date', 
        'end_date'
    )
    search_fields = (
        'name', 
        'description'
    )
    date_hierarchy = 'start_date'
    ordering = ('start_date',)
    
    # עדכון fieldsets כדי לכלול את השדות החדשים
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'event_type')
        }),
        ('פרטי תאריך', {
            'fields': ('start_date', 'end_date'),
            'classes': ('collapse',),
        }),
        ('פרמטרים לאירוע (אופציונלי)', { # קבוצה חדשה לשדות החדשים
            'fields': (
                'min_required_soldiers', 
                'max_home_days_per_soldier', 
                'base_days_per_soldier', 
                'home_days_per_soldier'
            ),
            'description': 'ניתן להגדיר פרמטרים נוספים לאירועים כמו אימונים.',
        }),
        ('קישור לאילוץ חייל', {
            'fields': ('soldier_constraint',),
            'description': 'יש לבחור אילוץ חייל רק אם סוג האירוע הוא "אילוץ חייל".',
        }),
    )

    def soldier_constraint_display(self, obj):
        if obj.soldier_constraint:
            return f"אילוץ של: {obj.soldier_constraint.soldier.name} ב-{obj.soldier_constraint.constraint_date}"
        return "אין"
    soldier_constraint_display.short_description = "אילוץ חייל מקושר"
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # עדכון הלוגיקה כדי לטפל בשדה soldier_constraint בלבד
        if obj and obj.event_type != 'CONSTRAINT':
            if 'soldier_constraint' in form.base_fields:
                form.base_fields['soldier_constraint'].required = False
                form.base_fields['soldier_constraint'].widget.attrs['disabled'] = True
                form.base_fields['soldier_constraint'].help_text = 'שדה זה רלוונטי רק לאירועים מסוג "אילוץ חייל".'
            
        # *** אופציונלי: לוגיקה להסתרה/הצגה של השדות החדשים בהתאם לסוג האירוע ***
        # אם תרצה שהשדות החדשים יוצגו רק לסוגי אירועים מסוימים (למשל TRAINING)
        # נצטרך לכתוב כאן לוגיקה מורכבת יותר, אולי באמצעות JavaScript מותאם אישית
        # או על ידי יצירת טופס אדמין מותאם אישית לחלוטין.
        # בשלב זה, הם יהיו תמיד גלויים וניתנים לעריכה.
        
        return form

    def save_model(self, request, obj, form, change):
        if obj.event_type != 'CONSTRAINT':
            obj.soldier_constraint = None
        super().save_model(request, obj, form, change)




@admin.register(SchedulingRun)
class SchedulingRunAdmin(admin.ModelAdmin):
    """
    מחלקה לניהול מודל SchedulingRun באתר האדמין של Django.
    """
    list_display = (
        'id',                   # מזהה
        'start_date',           # תאריך התחלה
        'end_date',             # תאריך סיום
        'min_required_soldiers_per_day', # מספר חיילים מינימלי
        'max_total_home_days',  # מקסימום ימי בית כוללים
        'status',               # סטטוס הרצה
        'run_date',             # תאריך הרצה
    )
    list_filter = (
        'status', 
        'start_date', 
        'end_date'
    )
    search_fields = (
        'solution_details', 
        'run_date'
    )
    date_hierarchy = 'run_date' # ניווט לפי תאריך יצירת ההרצה
    ordering = ('-run_date',) # מיון מההרצה האחרונה

    # הגדרות עבור טופס העריכה
    fieldsets = (
        (None, {
            'fields': (
                'start_date', 
                'end_date',
                'min_required_soldiers_per_day',
                'max_total_home_days',
            ),
            'description': 'פרמטרים עיקריים של טווח התאריכים ודרישות השיבוץ.'
        }),
        ('פרמטרי ימי בסיס/בית', {
            'fields': (
                'default_base_days_target',
                'default_home_days_target',
                'max_consecutive_base_days',
                'max_consecutive_home_days',
                'min_base_block_days',
            ),
            'classes': ('collapse',), # אופציונלי: יקרוס את הקטע כברירת מחדל
            'description': 'הגדרות מתקדמות לימי בסיס ובית.'
        }),
        ('סטטוס ותוצאות (קריאה בלבד)', {
            'fields': (
                'run_date', 
                'status', 
                'solution_details'
            ),
            'classes': ('collapse',),
        }),
    )

    # השדות האלה הם לקריאה בלבד ולא ניתנים לעריכה דרך טופס האדמין
    readonly_fields = ('run_date', 'status', 'solution_details',)