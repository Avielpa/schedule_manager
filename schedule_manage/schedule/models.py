# schedule/models.py
# Hierarchical organizational structure for separate events and soldier lists

from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from datetime import date


class Organization(models.Model):
    """
    Top-level organization (e.g., Military Base, Company, Hospital)
    """
    name = models.CharField(max_length=200, unique=True, verbose_name="Organization Name")
    code = models.CharField(max_length=20, unique=True, verbose_name="Organization Code")
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Contact information
    contact_email = models.EmailField(blank=True, null=True)
    contact_phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    
    class Meta:
        verbose_name = "Organization"
        verbose_name_plural = "Organizations"
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.code})"


class Unit(models.Model):
    """
    Hierarchical unit structure (Battalion → Company → Platoon → Squad)
    """
    UNIT_TYPES = [
        ('ORGANIZATION', 'Organization'),
        ('BATTALION', 'Battalion'),
        ('COMPANY', 'Company'),
        ('PLATOON', 'Platoon'),
        ('SQUAD', 'Squad'),
        ('TEAM', 'Team'),
        ('DEPARTMENT', 'Department'),
        ('DIVISION', 'Division'),
        ('CUSTOM', 'Custom'),
    ]
    
    name = models.CharField(max_length=200, verbose_name="Unit Name")
    code = models.CharField(max_length=50, verbose_name="Unit Code")
    unit_type = models.CharField(max_length=20, choices=UNIT_TYPES, verbose_name="Unit Type")
    
    # Hierarchical structure
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='units')
    parent_unit = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, 
                                   related_name='sub_units', verbose_name="Parent Unit")
    
    # Unit details
    description = models.TextField(blank=True, null=True)
    commander = models.CharField(max_length=100, blank=True, null=True, verbose_name="Unit Commander")
    location = models.CharField(max_length=200, blank=True, null=True)
    
    # Scheduling parameters (can override organization defaults)
    default_min_soldiers_per_day = models.IntegerField(null=True, blank=True, 
                                                       verbose_name="Default Min Soldiers Per Day")
    working_days = models.CharField(max_length=20, default='1,2,3,4,5,6,7', 
                                   verbose_name="Working Days (1=Mon, 7=Sun)")
    
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Unit"
        verbose_name_plural = "Units"
        unique_together = ('organization', 'code')
        ordering = ['organization', 'unit_type', 'name']
    
    def __str__(self):
        return f"{self.organization.code} - {self.name} ({self.unit_type})"
    
    def get_full_hierarchy(self):
        """Return full hierarchy path (e.g., 'Org > Battalion > Company')"""
        path = [self.name]
        current = self.parent_unit
        while current:
            path.append(current.name)
            current = current.parent_unit
        path.append(self.organization.name)
        return ' > '.join(reversed(path))
    
    def get_all_soldiers(self):
        """Get all soldiers in this unit and all sub-units"""
        from django.db.models import Q
        
        # Get direct soldiers
        soldier_ids = set(self.soldiers.values_list('id', flat=True))
        
        # Get soldiers from all sub-units recursively
        def get_subunit_soldiers(unit):
            for sub_unit in unit.sub_units.all():
                soldier_ids.update(sub_unit.soldiers.values_list('id', flat=True))
                get_subunit_soldiers(sub_unit)
        
        get_subunit_soldiers(self)
        
        return Soldier.objects.filter(id__in=soldier_ids)
    
    def get_hierarchy_level(self):
        """Get the depth level in hierarchy (0 = top level)"""
        level = 0
        current = self.parent_unit
        while current:
            level += 1
            current = current.parent_unit
        return level


class ImportBatch(models.Model):
    """
    Track soldier imports from different sources/files
    """
    name = models.CharField(max_length=200, verbose_name="Import Name")
    source_file = models.CharField(max_length=500, blank=True, null=True, verbose_name="Source File")
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='import_batches')
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, null=True, blank=True, 
                            related_name='import_batches', verbose_name="Target Unit")
    
    imported_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    import_date = models.DateTimeField(auto_now_add=True)
    
    # Import statistics
    total_soldiers = models.IntegerField(default=0)
    successful_imports = models.IntegerField(default=0)
    failed_imports = models.IntegerField(default=0)
    
    # Import settings used
    import_settings = models.JSONField(default=dict, blank=True)
    
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        verbose_name = "Import Batch"
        verbose_name_plural = "Import Batches"
        ordering = ['-import_date']
    
    def __str__(self):
        return f"{self.name} - {self.organization.code} ({self.import_date.strftime('%Y-%m-%d')})"


class Soldier(models.Model):
    """
    Enhanced Soldier model with organizational structure
    """
    RANK_CHOICES = [
        ('PRIVATE', 'Private'),
        ('CORPORAL', 'Corporal'),
        ('SERGEANT', 'Sergeant'),
        ('LIEUTENANT', 'Lieutenant'),
        ('CAPTAIN', 'Captain'),
        ('MAJOR', 'Major'),
        ('COLONEL', 'Colonel'),
        ('GENERAL', 'General'),
        ('CIVILIAN', 'Civilian'),
    ]
    
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('INACTIVE', 'Inactive'),
        ('ON_LEAVE', 'On Leave'),
        ('TRANSFERRED', 'Transferred'),
        ('DISCHARGED', 'Discharged'),
    ]
    
    # Basic information
    name = models.CharField(max_length=100, verbose_name="Soldier Name")
    soldier_id = models.CharField(max_length=50, unique=True, verbose_name="Soldier ID")
    rank = models.CharField(max_length=20, choices=RANK_CHOICES, default='PRIVATE')
    
    # Organizational structure
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='soldiers')
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name='soldiers')
    import_batch = models.ForeignKey(ImportBatch, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='soldiers', verbose_name="Import Batch")
    
    # Contact information
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    
    # Soldier properties (from original model)
    is_exceptional_output = models.BooleanField(default=False, verbose_name="Exceptional/Leadership Role")
    is_weekend_only_soldier_flag = models.BooleanField(default=False, verbose_name="Weekend Only")
    
    # Additional properties
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    hire_date = models.DateField(null=True, blank=True)
    specialty = models.CharField(max_length=100, blank=True, null=True, verbose_name="Military Specialty")
    security_clearance = models.CharField(max_length=50, blank=True, null=True)
    
    # Scheduling preferences
    preferred_shift = models.CharField(max_length=20, blank=True, null=True)
    max_consecutive_days = models.IntegerField(null=True, blank=True, 
                                              verbose_name="Personal Max Consecutive Days")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Soldier"
        verbose_name_plural = "Soldiers"
        unique_together = ('organization', 'name')  # Names unique within organization
        ordering = ['organization', 'unit', 'rank', 'name']
    
    def __str__(self):
        return f"{self.rank} {self.name} ({self.unit.code})"
    
    def get_full_designation(self):
        """Get full designation including unit hierarchy"""
        return f"{self.rank} {self.name} - {self.unit.get_full_hierarchy()}"


class SoldierConstraint(models.Model):
    """
    Enhanced constraint model (unchanged from original but with better relationships)
    """
    soldier = models.ForeignKey(Soldier, related_name='constraints', on_delete=models.CASCADE)
    constraint_date = models.DateField(verbose_name="Constraint Date")
    description = models.TextField(blank=True, null=True, verbose_name="Constraint Description")
    
    # Additional constraint properties
    CONSTRAINT_TYPES = [
        ('PERSONAL', 'Personal Leave'),
        ('MEDICAL', 'Medical'),
        ('TRAINING', 'Training/Course'),
        ('FAMILY', 'Family Event'),
        ('OFFICIAL', 'Official Duty'),
        ('OTHER', 'Other'),
    ]
    
    constraint_type = models.CharField(max_length=20, choices=CONSTRAINT_TYPES, default='PERSONAL')
    is_recurring = models.BooleanField(default=False, verbose_name="Recurring Constraint")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('soldier', 'constraint_date')
        verbose_name = "Soldier Constraint"
        verbose_name_plural = "Soldier Constraints"
        ordering = ['constraint_date']
    
    def __str__(self):
        return f"{self.soldier.name} - {self.constraint_type} on {self.constraint_date}"


class SchedulingRun(models.Model):
    """
    Enhanced scheduling run with organizational scope
    """
    STATUS_CHOICES = [
        ('SUCCESS', 'Successfully Completed'),
        ('FAILURE', 'Failed'),
        ('IN_PROGRESS', 'In Progress'),
        ('NO_SOLUTION', 'No Solution Found'),
        ('CANCELLED', 'Cancelled'),
        ('PENDING', 'Pending'),
    ]
    
    # Organizational scope
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='scheduling_runs')
    target_units = models.ManyToManyField(Unit, related_name='scheduling_runs', 
                                         verbose_name="Target Units")
    
    # Basic scheduling parameters (from original)
    run_date = models.DateTimeField(auto_now_add=True)
    start_date = models.DateField(verbose_name="Start Date")
    end_date = models.DateField(verbose_name="End Date")
    
    default_base_days_target = models.IntegerField(verbose_name="Default Base Days Target")
    default_home_days_target = models.IntegerField(verbose_name="Default Home Days Target")
    max_consecutive_base_days = models.IntegerField(verbose_name="Max Consecutive Base Days")
    max_consecutive_home_days = models.IntegerField(verbose_name="Max Consecutive Home Days")
    min_base_block_days = models.IntegerField(verbose_name="Min Base Block Days")
    min_required_soldiers_per_day = models.IntegerField(verbose_name="Min Required Soldiers Per Day")
    max_total_home_days = models.IntegerField(null=True, blank=True, verbose_name="Max Total Home Days")
    max_weekend_base_days_per_soldier = models.IntegerField(null=True, blank=True, 
                                                            verbose_name="Max Weekend Base Days Per Soldier")
    
    # Enhanced features
    name = models.CharField(max_length=200, verbose_name="Schedule Name")
    description = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Advanced scheduling options
    priority_soldiers = models.ManyToManyField(Soldier, blank=True, 
                                              related_name='priority_schedules',
                                              verbose_name="Priority Soldiers")
    exclude_soldiers = models.ManyToManyField(Soldier, blank=True,
                                             related_name='excluded_schedules', 
                                             verbose_name="Excluded Soldiers")
    
    # Status and results
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    solution_details = models.TextField(blank=True, null=True)
    algorithm_version = models.CharField(max_length=50, blank=True, null=True)
    processing_time_seconds = models.IntegerField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Scheduling Run"
        verbose_name_plural = "Scheduling Runs"
        ordering = ['-run_date']
    
    def __str__(self):
        units_str = ", ".join([u.code for u in self.target_units.all()[:3]])
        if self.target_units.count() > 3:
            units_str += f" (+{self.target_units.count() - 3} more)"
        return f"{self.name} - {units_str} ({self.status})"
    
    def get_target_soldiers(self):
        """Get all soldiers from target units"""
        from django.db.models import Q
        
        # Get all soldiers from target units
        soldier_ids = set()
        for unit in self.target_units.all():
            soldier_ids.update(unit.get_all_soldiers().values_list('id', flat=True))
        
        # Apply exclusions and inclusions
        target_soldiers = Soldier.objects.filter(id__in=soldier_ids, status='ACTIVE')
        
        # Exclude specifically excluded soldiers
        if self.exclude_soldiers.exists():
            target_soldiers = target_soldiers.exclude(id__in=self.exclude_soldiers.values_list('id', flat=True))
        
        return target_soldiers


class Assignment(models.Model):
    """
    Enhanced assignment model (mostly unchanged)
    """
    scheduling_run = models.ForeignKey(SchedulingRun, related_name='assignments', on_delete=models.CASCADE)
    soldier = models.ForeignKey(Soldier, on_delete=models.CASCADE)
    assignment_date = models.DateField(verbose_name="Assignment Date")
    is_on_base = models.BooleanField(verbose_name="Is on Base?")
    
    # Enhanced features
    shift_type = models.CharField(max_length=20, blank=True, null=True, verbose_name="Shift Type")
    location = models.CharField(max_length=100, blank=True, null=True, verbose_name="Assignment Location")
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        unique_together = ('scheduling_run', 'soldier', 'assignment_date')
        verbose_name = "Assignment"
        verbose_name_plural = "Assignments"
        ordering = ['assignment_date', 'soldier__unit', 'soldier__name']
    
    def __str__(self):
        status = "On Base" if self.is_on_base else "At Home"
        return f"{self.soldier.rank} {self.soldier.name} on {self.assignment_date}: {status}"


class Event(models.Model):
    """
    Enhanced event model with better unit targeting
    """
    EVENT_TYPE_CHOICES = [
        ('CONSTRAINT', 'Soldier Constraint'),
        ('TRAINING', 'Training'),
        ('EXERCISE', 'Military Exercise'),
        ('HOLIDAY', 'Holiday'),
        ('MAINTENANCE', 'Equipment Maintenance'),
        ('INSPECTION', 'Inspection'),
        ('CEREMONY', 'Ceremony'),
        ('OTHER', 'Other'),
    ]
    
    # Basic event information
    event_type = models.CharField(max_length=20, choices=EVENT_TYPE_CHOICES, default='OTHER')
    name = models.CharField(max_length=200, verbose_name="Event Name")
    description = models.TextField(blank=True, null=True)
    start_date = models.DateField(verbose_name="Start Date")
    end_date = models.DateField(verbose_name="End Date")
    
    # Organizational scope
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='events')
    target_units = models.ManyToManyField(Unit, blank=True, related_name='events',
                                         verbose_name="Target Units")
    
    # Specific soldier targeting
    specific_soldiers = models.ManyToManyField(Soldier, blank=True, related_name='specific_events',
                                              verbose_name="Specific Soldiers")
    
    # Event-specific scheduling parameters (restored from original)
    min_required_soldiers = models.IntegerField(null=True, blank=True, 
                                               verbose_name="Min Required Soldiers")
    
    # Base/Home day requirements for this event
    base_days_per_soldier = models.IntegerField(null=True, blank=True, 
                                               verbose_name="Base Days Per Soldier for Event")
    home_days_per_soldier = models.IntegerField(null=True, blank=True,
                                               verbose_name="Home Days Per Soldier for Event")
    max_home_days_per_soldier = models.IntegerField(null=True, blank=True,
                                                   verbose_name="Max Home Days Per Soldier")
    max_base_days_per_soldier = models.IntegerField(null=True, blank=True,
                                                   verbose_name="Max Base Days Per Soldier")
    
    # Consecutive work/leave limits for this event
    max_consecutive_base_days = models.IntegerField(null=True, blank=True,
                                                   verbose_name="Max Consecutive Base Days")
    max_consecutive_home_days = models.IntegerField(null=True, blank=True,
                                                   verbose_name="Max Consecutive Home Days")
    min_consecutive_base_days = models.IntegerField(null=True, blank=True,
                                                   verbose_name="Min Consecutive Base Days")
    min_consecutive_home_days = models.IntegerField(null=True, blank=True,
                                                   verbose_name="Min Consecutive Home Days")
    
    # Block and pattern requirements
    min_base_block_days = models.IntegerField(null=True, blank=True,
                                             verbose_name="Min Base Block Days")
    max_base_block_days = models.IntegerField(null=True, blank=True,
                                             verbose_name="Max Base Block Days")
    
    # Weekend and special day handling
    max_weekend_base_days_per_soldier = models.IntegerField(null=True, blank=True,
                                                           verbose_name="Max Weekend Base Days Per Soldier")
    require_weekend_coverage = models.BooleanField(default=True,
                                                  verbose_name="Require Weekend Coverage")
    weekend_min_soldiers = models.IntegerField(null=True, blank=True,
                                              verbose_name="Min Soldiers Required on Weekends")
    
    # Advanced constraints
    force_rotation_days = models.IntegerField(null=True, blank=True,
                                             verbose_name="Force Rotation Every X Days")
    exceptional_soldier_distribution = models.BooleanField(default=True,
                                                          verbose_name="Distribute Exceptional Soldiers Evenly")
    
    # Workload balancing
    balance_workload = models.BooleanField(default=True,
                                         verbose_name="Balance Workload Across Soldiers")
    workload_variance_tolerance = models.FloatField(null=True, blank=True, default=0.1,
                                                   verbose_name="Workload Variance Tolerance (0.0-1.0)")
    
    # Override global settings flag
    override_global_settings = models.BooleanField(default=False,
                                                  verbose_name="Override Global Scheduling Settings")
    
    # Enhanced features
    priority_level = models.IntegerField(default=5, verbose_name="Priority (1-10)")
    is_mandatory = models.BooleanField(default=False, verbose_name="Mandatory Participation")
    location = models.CharField(max_length=200, blank=True, null=True)
    
    # Optional link to soldier constraint
    soldier_constraint = models.OneToOneField(SoldierConstraint, on_delete=models.SET_NULL, 
                                             null=True, blank=True, related_name='event_link')
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Event"
        verbose_name_plural = "Events"
        ordering = ['start_date', 'priority_level']
    
    def __str__(self):
        return f"{self.name} ({self.event_type}) - {self.organization.code}"
    
    def get_target_soldiers(self):
        """Get all soldiers affected by this event"""
        soldiers = set()
        
        # Add soldiers from specific selection
        soldiers.update(self.specific_soldiers.all())
        
        # Add soldiers from target units
        for unit in self.target_units.all():
            soldiers.update(unit.get_all_soldiers())
        
        return list(soldiers)
    
    def get_scheduling_parameters(self):
        """
        Get scheduling parameters for this event.
        Returns event-specific parameters if override_global_settings is True,
        otherwise returns None (uses global defaults).
        """
        if not self.override_global_settings:
            return None
            
        return {
            'base_days_per_soldier': self.base_days_per_soldier,
            'home_days_per_soldier': self.home_days_per_soldier,
            'max_home_days_per_soldier': self.max_home_days_per_soldier,
            'max_base_days_per_soldier': self.max_base_days_per_soldier,
            'max_consecutive_base_days': self.max_consecutive_base_days,
            'max_consecutive_home_days': self.max_consecutive_home_days,
            'min_consecutive_base_days': self.min_consecutive_base_days,
            'min_consecutive_home_days': self.min_consecutive_home_days,
            'min_base_block_days': self.min_base_block_days,
            'max_base_block_days': self.max_base_block_days,
            'max_weekend_base_days_per_soldier': self.max_weekend_base_days_per_soldier,
            'require_weekend_coverage': self.require_weekend_coverage,
            'weekend_min_soldiers': self.weekend_min_soldiers,
            'force_rotation_days': self.force_rotation_days,
            'exceptional_soldier_distribution': self.exceptional_soldier_distribution,
            'balance_workload': self.balance_workload,
            'workload_variance_tolerance': self.workload_variance_tolerance,
            'min_required_soldiers_per_day': self.min_required_soldiers,
        }
    
    def uses_custom_parameters(self):
        """Check if this event uses custom scheduling parameters"""
        if not self.override_global_settings:
            return False
            
        # Check if any event-specific parameter is set
        custom_params = [
            self.base_days_per_soldier,
            self.home_days_per_soldier,
            self.max_home_days_per_soldier,
            self.max_base_days_per_soldier,
            self.max_consecutive_base_days,
            self.max_consecutive_home_days,
            self.min_consecutive_base_days,
            self.min_consecutive_home_days,
            self.min_base_block_days,
            self.max_base_block_days,
            self.max_weekend_base_days_per_soldier,
            self.weekend_min_soldiers,
            self.force_rotation_days,
        ]
        
        return any(param is not None for param in custom_params)


# User permissions and access control
class UserOrganizationRole(models.Model):
    """
    Define user roles within organizations
    """
    ROLE_CHOICES = [
        ('ADMIN', 'Organization Administrator'),
        ('SCHEDULER', 'Scheduler'),
        ('UNIT_MANAGER', 'Unit Manager'),
        ('VIEWER', 'View Only'),
        ('SOLDIER', 'Soldier (Self Service)'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='organization_roles')
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='user_roles')
    units = models.ManyToManyField(Unit, blank=True, verbose_name="Managed Units")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ('user', 'organization')
        verbose_name = "User Organization Role"
        verbose_name_plural = "User Organization Roles"
    
    def __str__(self):
        return f"{self.user.username} - {self.role} in {self.organization.code}"