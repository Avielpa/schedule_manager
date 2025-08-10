# schedule/admin.py
# Simplified admin interface for Event -> Schedule -> Soldiers flow

from django.contrib import admin
from django.db import models
from django.forms import Textarea

from .models import Event, Soldier, SoldierConstraint, SchedulingRun, Assignment

# =============================================================================
# INLINE ADMIN CLASSES
# =============================================================================

class SoldierInline(admin.TabularInline):
    model = Soldier
    fields = ('name', 'soldier_id', 'rank', 'is_exceptional_output', 'is_weekend_only_soldier_flag')
    extra = 0
    readonly_fields = ('name', 'soldier_id', 'rank', 'is_exceptional_output', 'is_weekend_only_soldier_flag')
    can_delete = False
    max_num = 0  # Don't allow adding soldiers through event admin
    show_change_link = True

class SoldierConstraintInline(admin.TabularInline):
    model = SoldierConstraint
    fields = ('constraint_date', 'constraint_type', 'description')
    extra = 1

class AssignmentInline(admin.TabularInline):
    model = Assignment
    fields = ('soldier', 'assignment_date', 'is_on_base')
    extra = 0
    readonly_fields = ('soldier', 'assignment_date', 'is_on_base')


# =============================================================================
# MAIN ADMIN CLASSES
# =============================================================================

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'event_type', 'start_date', 'end_date', 'get_soldiers_count', 'min_required_soldiers_per_day')
    list_filter = ('event_type', 'start_date', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('id', 'created_at', 'get_soldiers_count')
    inlines = [SoldierInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'name', 'event_type', 'description', 'start_date', 'end_date')
        }),
        ('Core Scheduling Rules', {
            'fields': (
                'min_required_soldiers_per_day',
                ('base_days_per_soldier', 'home_days_per_soldier'),
                ('max_consecutive_base_days', 'max_consecutive_home_days'),
                'min_base_block_days'
            ),
            'description': 'Basic scheduling parameters that define work patterns'
        }),
        ('Advanced Algorithm Settings', {
            'fields': (
                'exceptional_constraint_threshold',
                'constraint_safety_margin_percent', 
                'weekend_only_max_base_days'
            ),
            'classes': ('collapse',),
            'description': 'Advanced settings for handling exceptional soldiers and constraints'
        }),
        ('Algorithm Weights', {
            'fields': (
                ('enable_home_balance_penalty', 'home_balance_weight'),
                ('enable_weekend_fairness_weight', 'weekend_fairness_weight')
            ),
            'classes': ('collapse',),
            'description': 'Control algorithm behavior and fairness calculations'
        }),
        ('Flexibility Options', {
            'fields': (
                'allow_single_day_blocks',
                'strict_consecutive_limits', 
                'auto_adjust_for_constraints'
            ),
            'classes': ('collapse',),
            'description': 'System flexibility and constraint handling options'
        }),
        ('System Information', {
            'fields': ('created_by', 'created_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_soldiers_count(self, obj):
        return obj.soldiers.count()
    get_soldiers_count.short_description = 'Soldiers Count'


@admin.register(Soldier)
class SoldierAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'soldier_id', 'rank', 'get_event_info', 'get_constraints_count', 'is_exceptional_output', 'is_weekend_only_soldier_flag')
    list_filter = ('event', 'rank', 'is_exceptional_output', 'is_weekend_only_soldier_flag')
    search_fields = ('name', 'soldier_id', 'event__name')
    readonly_fields = ('id', 'created_at', 'get_constraints_count')
    inlines = [SoldierConstraintInline]
    
    fieldsets = (
        ('Event Assignment', {
            'fields': ('event',)
        }),
        ('Basic Information', {
            'fields': ('id', 'name', 'soldier_id', 'rank')
        }),
        ('Soldier Properties', {
            'fields': ('is_exceptional_output', 'is_weekend_only_soldier_flag')
        }),
        ('System Information', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )
    
    def get_constraints_count(self, obj):
        return obj.constraints.count()
    get_constraints_count.short_description = 'Constraints'
    
    def get_event_info(self, obj):
        return f"{obj.event.name} (ID: {obj.event.id})"
    get_event_info.short_description = 'Event'


@admin.register(SchedulingRun)
class SchedulingRunAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'get_event_info', 'status', 'get_soldiers_count', 'created_at')
    list_filter = ('status', 'event', 'created_at')
    search_fields = ('name', 'description', 'event__name')
    readonly_fields = ('id', 'created_at', 'processing_time_seconds')
    filter_horizontal = ('soldiers',)
    inlines = [AssignmentInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'name', 'description', 'event')
        }),
        ('Soldiers', {
            'fields': ('soldiers',)
        }),
        ('Results', {
            'fields': ('status', 'solution_details', 'processing_time_seconds'),
            'classes': ('collapse',)
        }),
        ('System Information', {
            'fields': ('created_by', 'created_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_soldiers_count(self, obj):
        return obj.soldiers.count()
    get_soldiers_count.short_description = 'Soldiers'
    
    def get_event_info(self, obj):
        return f"{obj.event.name} (ID: {obj.event.id})"
    get_event_info.short_description = 'Event'


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ('soldier', 'assignment_date', 'is_on_base', 'get_scheduling_run')
    list_filter = ('is_on_base', 'assignment_date')
    search_fields = ('soldier__name', 'soldier__soldier_id')
    readonly_fields = ('soldier', 'scheduling_run', 'assignment_date', 'is_on_base')
    date_hierarchy = 'assignment_date'
    
    def get_scheduling_run(self, obj):
        return str(obj.scheduling_run)
    get_scheduling_run.short_description = 'Scheduling Run'


@admin.register(SoldierConstraint)
class SoldierConstraintAdmin(admin.ModelAdmin):
    list_display = ('soldier', 'constraint_date', 'constraint_type')
    list_filter = ('constraint_type', 'constraint_date')
    search_fields = ('soldier__name', 'soldier__soldier_id', 'description')
    date_hierarchy = 'constraint_date'
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('Constraint Information', {
            'fields': ('soldier', 'constraint_date', 'constraint_type')
        }),
        ('Details', {
            'fields': ('description',)
        }),
        ('System Information', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )