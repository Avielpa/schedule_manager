# schedule/admin.py
# Enhanced admin interface for hierarchical organizational system

from django.contrib import admin
from django.db import models
from django.forms import Textarea

from .models import (
    Organization, Unit, ImportBatch, Soldier, SoldierConstraint, 
    SchedulingRun, Assignment, Event, UserOrganizationRole
)

# =============================================================================
# INLINE ADMIN CLASSES
# =============================================================================

class UnitInline(admin.TabularInline):
    model = Unit
    fields = ('name', 'code', 'unit_type', 'parent_unit', 'is_active')
    extra = 0


class SoldierInline(admin.TabularInline):
    model = Soldier
    fields = ('name', 'soldier_id', 'rank', 'status')
    extra = 0
    show_change_link = True


class SoldierConstraintInline(admin.TabularInline):
    model = SoldierConstraint
    fields = ('constraint_date', 'constraint_type', 'description')
    extra = 0


class AssignmentInline(admin.TabularInline):
    model = Assignment
    fields = ('soldier', 'assignment_date', 'is_on_base', 'shift_type')
    extra = 0
    readonly_fields = ('soldier', 'assignment_date', 'is_on_base')


# =============================================================================
# MAIN ADMIN CLASSES
# =============================================================================

@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'get_units_count', 'get_soldiers_count', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'code', 'description')
    readonly_fields = ('created_at',)
    inlines = [UnitInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'code', 'description')
        }),
        ('Contact Information', {
            'fields': ('contact_email', 'contact_phone', 'address'),
            'classes': ('collapse',)
        }),
        ('System Information', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )
    
    def get_units_count(self, obj):
        return obj.units.count()
    get_units_count.short_description = 'Units'
    
    def get_soldiers_count(self, obj):
        return obj.soldiers.filter(status='ACTIVE').count()
    get_soldiers_count.short_description = 'Active Soldiers'


@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'unit_type', 'organization', 'parent_unit', 'get_soldiers_count', 'is_active')
    list_filter = ('unit_type', 'organization', 'is_active', 'created_at')
    search_fields = ('name', 'code', 'commander', 'description')
    readonly_fields = ('created_at',)
    inlines = [SoldierInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'code', 'unit_type', 'organization', 'parent_unit')
        }),
        ('Unit Details', {
            'fields': ('description', 'commander', 'location', 'is_active')
        }),
        ('Scheduling Parameters', {
            'fields': ('default_min_soldiers_per_day', 'working_days'),
            'classes': ('collapse',)
        }),
        ('System Information', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )
    
    def get_soldiers_count(self, obj):
        return obj.soldiers.filter(status='ACTIVE').count()
    get_soldiers_count.short_description = 'Soldiers'


@admin.register(Soldier)
class SoldierAdmin(admin.ModelAdmin):
    list_display = ('name', 'soldier_id', 'rank', 'unit', 'organization', 'status', 'is_exceptional_output')
    list_filter = ('rank', 'status', 'organization', 'unit', 'is_exceptional_output', 'is_weekend_only_soldier_flag')
    search_fields = ('name', 'soldier_id', 'email', 'phone')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [SoldierConstraintInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'soldier_id', 'rank', 'status')
        }),
        ('Organizational Assignment', {
            'fields': ('organization', 'unit', 'import_batch')
        }),
        ('Contact Information', {
            'fields': ('email', 'phone'),
            'classes': ('collapse',)
        }),
        ('Soldier Properties', {
            'fields': ('is_exceptional_output', 'is_weekend_only_soldier_flag', 'specialty', 'security_clearance')
        }),
        ('Scheduling Preferences', {
            'fields': ('preferred_shift', 'max_consecutive_days'),
            'classes': ('collapse',)
        }),
        ('System Information', {
            'fields': ('hire_date', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('organization', 'unit', 'import_batch')


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('name', 'event_type', 'organization', 'start_date', 'end_date', 'priority_level', 'override_global_settings')
    list_filter = ('event_type', 'organization', 'priority_level', 'is_mandatory', 'override_global_settings', 'created_at')
    search_fields = ('name', 'description', 'location')
    readonly_fields = ('created_at',)
    filter_horizontal = ('target_units', 'specific_soldiers')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'event_type', 'description', 'start_date', 'end_date')
        }),
        ('Organizational Scope', {
            'fields': ('organization', 'target_units', 'specific_soldiers')
        }),
        ('Event Settings', {
            'fields': ('priority_level', 'is_mandatory', 'location')
        }),
        ('Custom Scheduling Parameters', {
            'fields': (
                'override_global_settings',
                ('base_days_per_soldier', 'home_days_per_soldier'),
                ('max_base_days_per_soldier', 'max_home_days_per_soldier'),
                ('max_consecutive_base_days', 'max_consecutive_home_days'),
                ('min_consecutive_base_days', 'min_consecutive_home_days'),
                ('min_base_block_days', 'max_base_block_days'),
                ('max_weekend_base_days_per_soldier', 'weekend_min_soldiers'),
                'require_weekend_coverage',
                'force_rotation_days',
                'exceptional_soldier_distribution',
                'balance_workload',
                'workload_variance_tolerance'
            ),
            'classes': ('collapse',)
        }),
        ('System Information', {
            'fields': ('created_by', 'created_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('organization', 'created_by')


@admin.register(SchedulingRun)
class SchedulingRunAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization', 'start_date', 'end_date', 'status', 'get_target_units_count')
    list_filter = ('status', 'organization', 'created_by', 'run_date')
    search_fields = ('name', 'description')
    readonly_fields = ('run_date', 'processing_time_seconds', 'algorithm_version')
    filter_horizontal = ('target_units', 'priority_soldiers', 'exclude_soldiers')
    inlines = [AssignmentInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'organization', 'target_units')
        }),
        ('Schedule Period', {
            'fields': ('start_date', 'end_date')
        }),
        ('Basic Parameters', {
            'fields': (
                ('default_base_days_target', 'default_home_days_target'),
                ('max_consecutive_base_days', 'max_consecutive_home_days'),
                ('min_base_block_days', 'min_required_soldiers_per_day'),
                ('max_total_home_days', 'max_weekend_base_days_per_soldier')
            )
        }),
        ('Soldier Selection', {
            'fields': ('priority_soldiers', 'exclude_soldiers'),
            'classes': ('collapse',)
        }),
        ('Results', {
            'fields': ('status', 'solution_details', 'processing_time_seconds', 'algorithm_version'),
            'classes': ('collapse',)
        }),
        ('System Information', {
            'fields': ('created_by', 'run_date'),
            'classes': ('collapse',)
        })
    )
    
    def get_target_units_count(self, obj):
        return obj.target_units.count()
    get_target_units_count.short_description = 'Target Units'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('organization', 'created_by').prefetch_related('target_units')


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ('soldier', 'assignment_date', 'is_on_base', 'shift_type', 'get_scheduling_run')
    list_filter = ('is_on_base', 'shift_type', 'assignment_date', 'soldier__organization')
    search_fields = ('soldier__name', 'soldier__soldier_id', 'location', 'notes')
    readonly_fields = ('soldier', 'scheduling_run', 'assignment_date', 'is_on_base')
    date_hierarchy = 'assignment_date'
    
    fieldsets = (
        ('Assignment Details', {
            'fields': ('scheduling_run', 'soldier', 'assignment_date', 'is_on_base')
        }),
        ('Additional Information', {
            'fields': ('shift_type', 'location', 'notes'),
            'classes': ('collapse',)
        })
    )
    
    def get_scheduling_run(self, obj):
        return str(obj.scheduling_run)
    get_scheduling_run.short_description = 'Scheduling Run'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('soldier', 'scheduling_run', 'soldier__organization')


@admin.register(SoldierConstraint)
class SoldierConstraintAdmin(admin.ModelAdmin):
    list_display = ('soldier', 'constraint_date', 'constraint_type', 'is_recurring')
    list_filter = ('constraint_type', 'is_recurring', 'constraint_date', 'soldier__organization')
    search_fields = ('soldier__name', 'soldier__soldier_id', 'description')
    date_hierarchy = 'constraint_date'
    
    fieldsets = (
        ('Constraint Information', {
            'fields': ('soldier', 'constraint_date', 'constraint_type', 'is_recurring')
        }),
        ('Details', {
            'fields': ('description',)
        }),
        ('System Information', {
            'fields': ('created_by', 'created_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('soldier', 'created_by', 'soldier__organization')


@admin.register(ImportBatch)
class ImportBatchAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization', 'unit', 'total_soldiers', 'successful_imports', 'failed_imports', 'import_date')
    list_filter = ('organization', 'unit', 'import_date', 'imported_by')
    search_fields = ('name', 'source_file', 'notes')
    readonly_fields = ('import_date', 'total_soldiers', 'successful_imports', 'failed_imports')
    
    fieldsets = (
        ('Import Information', {
            'fields': ('name', 'source_file', 'organization', 'unit')
        }),
        ('Import Statistics', {
            'fields': ('total_soldiers', 'successful_imports', 'failed_imports'),
            'classes': ('collapse',)
        }),
        ('Import Settings', {
            'fields': ('import_settings', 'notes'),
            'classes': ('collapse',)
        }),
        ('System Information', {
            'fields': ('imported_by', 'import_date'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('organization', 'unit', 'imported_by')


@admin.register(UserOrganizationRole)
class UserOrganizationRoleAdmin(admin.ModelAdmin):
    list_display = ('user', 'organization', 'role', 'is_active', 'get_managed_units_count')
    list_filter = ('role', 'organization', 'is_active', 'created_at')
    search_fields = ('user__username', 'user__email', 'organization__name')
    filter_horizontal = ('units',)
    
    fieldsets = (
        ('Role Assignment', {
            'fields': ('user', 'organization', 'role', 'is_active')
        }),
        ('Managed Units', {
            'fields': ('units',),
            'classes': ('collapse',)
        }),
        ('System Information', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )
    
    def get_managed_units_count(self, obj):
        return obj.units.count()
    get_managed_units_count.short_description = 'Managed Units'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'organization').prefetch_related('units')