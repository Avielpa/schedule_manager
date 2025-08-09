# schedule/admin.py
# Simplified admin interface for Event -> Schedule -> Soldiers flow

from django.contrib import admin
from django.db import models
from django.forms import Textarea

from .models import Event, Soldier, SoldierConstraint, SchedulingRun, Assignment

# =============================================================================
# INLINE ADMIN CLASSES
# =============================================================================

class SoldierConstraintInline(admin.TabularInline):
    model = SoldierConstraint
    fields = ('constraint_date', 'constraint_type', 'description')
    extra = 0


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
    list_display = ('name', 'event_type', 'start_date', 'end_date', 'min_required_soldiers_per_day')
    list_filter = ('event_type', 'start_date', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'event_type', 'description', 'start_date', 'end_date')
        }),
        ('Scheduling Parameters', {
            'fields': (
                'min_required_soldiers_per_day',
                ('base_days_per_soldier', 'home_days_per_soldier'),
                ('max_consecutive_base_days', 'max_consecutive_home_days'),
                'min_base_block_days'
            )
        }),
        ('System Information', {
            'fields': ('created_by', 'created_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(Soldier)
class SoldierAdmin(admin.ModelAdmin):
    list_display = ('name', 'soldier_id', 'rank', 'is_exceptional_output', 'is_weekend_only_soldier_flag')
    list_filter = ('rank', 'is_exceptional_output', 'is_weekend_only_soldier_flag')
    search_fields = ('name', 'soldier_id')
    readonly_fields = ('created_at',)
    inlines = [SoldierConstraintInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'soldier_id', 'rank')
        }),
        ('Soldier Properties', {
            'fields': ('is_exceptional_output', 'is_weekend_only_soldier_flag')
        }),
        ('System Information', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )


@admin.register(SchedulingRun)
class SchedulingRunAdmin(admin.ModelAdmin):
    list_display = ('name', 'event', 'status', 'get_soldiers_count', 'created_at')
    list_filter = ('status', 'event', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'processing_time_seconds')
    filter_horizontal = ('soldiers',)
    inlines = [AssignmentInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'event')
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