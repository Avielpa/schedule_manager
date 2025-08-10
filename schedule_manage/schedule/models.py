# schedule/models.py
# Simplified structure: Event -> Schedule -> Soldiers

from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from datetime import date


class Event(models.Model):
    """
    Dynamic event model - user configures all scheduling rules
    """
    EVENT_TYPE_CHOICES = [
        ('TRAINING', 'Training'),
        ('EXERCISE', 'Military Exercise'),
        ('HOLIDAY', 'Holiday'),
        ('MAINTENANCE', 'Equipment Maintenance'),
        ('INSPECTION', 'Inspection'),
        ('CEREMONY', 'Ceremony'),
        ('OTHER', 'Other'),
    ]
    
    # Basic event information
    name = models.CharField(max_length=200, verbose_name="Event Name")
    description = models.TextField(blank=True, null=True)
    event_type = models.CharField(max_length=20, choices=EVENT_TYPE_CHOICES, default='OTHER')
    start_date = models.DateField(verbose_name="Start Date")
    end_date = models.DateField(verbose_name="End Date")
    
    # Core scheduling parameters (user-configurable)
    min_required_soldiers_per_day = models.IntegerField(default=10, verbose_name="Min Required Soldiers Per Day")
    base_days_per_soldier = models.IntegerField(null=True, blank=True, verbose_name="Base Days Per Soldier")
    home_days_per_soldier = models.IntegerField(null=True, blank=True, verbose_name="Home Days Per Soldier")
    max_consecutive_base_days = models.IntegerField(default=7, verbose_name="Max Consecutive Base Days")
    max_consecutive_home_days = models.IntegerField(default=10, verbose_name="Max Consecutive Home Days")
    min_base_block_days = models.IntegerField(default=3, verbose_name="Min Base Block Days")
    
    # Advanced user-configurable algorithm parameters
    exceptional_constraint_threshold = models.IntegerField(default=10, verbose_name="Exceptional Constraint Threshold", 
                                                          help_text="Soldiers with more constraints than this are treated as exceptional")
    constraint_safety_margin_percent = models.IntegerField(default=25, verbose_name="Constraint Safety Margin (%)",
                                                           help_text="Extra home days percentage for exceptional soldiers")
    weekend_only_max_base_days = models.IntegerField(default=14, verbose_name="Weekend-Only Max Base Days",
                                                     help_text="Maximum consecutive base days for weekend-only soldiers")
    
    # Algorithm weight parameters (user-configurable)
    enable_home_balance_penalty = models.BooleanField(default=True, verbose_name="Enable Home Balance Penalty")
    enable_weekend_fairness_weight = models.BooleanField(default=True, verbose_name="Enable Weekend Fairness")
    home_balance_weight = models.FloatField(default=1.0, verbose_name="Home Balance Weight")
    weekend_fairness_weight = models.FloatField(default=1.0, verbose_name="Weekend Fairness Weight")
    
    # Flexibility settings
    allow_single_day_blocks = models.BooleanField(default=False, verbose_name="Allow Single Day Base Blocks")
    strict_consecutive_limits = models.BooleanField(default=True, verbose_name="Strict Consecutive Day Limits")
    auto_adjust_for_constraints = models.BooleanField(default=True, verbose_name="Auto-Adjust for High Constraints")
    
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        verbose_name = "Event"
        verbose_name_plural = "Events"
        ordering = ['start_date', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.start_date} to {self.end_date})"


class Soldier(models.Model):
    """
    Soldier model - now belongs to specific event
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
    
    # Event association - each soldier belongs to one event
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='soldiers', verbose_name="Event", null=True, blank=True)
    
    # Basic information
    name = models.CharField(max_length=100, verbose_name="Soldier Name")
    soldier_id = models.CharField(max_length=50, blank=True, null=True, verbose_name="Soldier ID")
    rank = models.CharField(max_length=20, choices=RANK_CHOICES, default='PRIVATE')
    
    # Soldier properties for scheduling
    is_exceptional_output = models.BooleanField(default=False, verbose_name="Leadership Role")
    is_weekend_only_soldier_flag = models.BooleanField(default=False, verbose_name="Weekend Only")
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Soldier"
        verbose_name_plural = "Soldiers"
        ordering = ['event', 'rank', 'name']
        unique_together = ('event', 'soldier_id')  # Soldier ID unique within event
    
    def __str__(self):
        return f"{self.rank} {self.name} ({self.event.name})"


class SoldierConstraint(models.Model):
    """
    Soldier constraints - unchanged as it's already simple
    """
    soldier = models.ForeignKey(Soldier, related_name='constraints', on_delete=models.CASCADE)
    constraint_date = models.DateField(verbose_name="Constraint Date")
    description = models.TextField(blank=True, null=True, verbose_name="Constraint Description")
    
    CONSTRAINT_TYPES = [
        ('PERSONAL', 'Personal Leave'),
        ('MEDICAL', 'Medical'),
        ('TRAINING', 'Training/Course'),
        ('FAMILY', 'Family Event'),
        ('OFFICIAL', 'Official Duty'),
        ('OTHER', 'Other'),
    ]
    
    constraint_type = models.CharField(max_length=20, choices=CONSTRAINT_TYPES, default='PERSONAL')
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
    Simplified scheduling run - linked to one event with soldiers
    """
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('IN_PROGRESS', 'In Progress'),
        ('SUCCESS', 'Successfully Completed'),
        ('FAILURE', 'Failed'),
        ('NO_SOLUTION', 'No Solution Found'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    # Link to event
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='scheduling_runs')
    
    # Soldiers for this schedule
    soldiers = models.ManyToManyField(Soldier, related_name='scheduling_runs', verbose_name="Soldiers")
    
    # Schedule info
    name = models.CharField(max_length=200, verbose_name="Schedule Name")
    description = models.TextField(blank=True, null=True)
    
    # Status and results
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    solution_details = models.TextField(blank=True, null=True)
    processing_time_seconds = models.IntegerField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        verbose_name = "Scheduling Run"
        verbose_name_plural = "Scheduling Runs"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} for {self.event.name} ({self.status})"
    
    def get_target_soldiers(self):
        """Get all soldiers for this scheduling run - automatically from the event"""
        if self.soldiers.exists():
            # If specific soldiers are selected, use them
            return self.soldiers.all()
        else:
            # Otherwise, use all soldiers from the event
            return self.event.soldiers.all()


class Assignment(models.Model):
    """
    Assignment model - unchanged as it's already simple
    """
    scheduling_run = models.ForeignKey(SchedulingRun, related_name='assignments', on_delete=models.CASCADE)
    soldier = models.ForeignKey(Soldier, on_delete=models.CASCADE)
    assignment_date = models.DateField(verbose_name="Assignment Date")
    is_on_base = models.BooleanField(verbose_name="Is on Base?")
    
    class Meta:
        unique_together = ('scheduling_run', 'soldier', 'assignment_date')
        verbose_name = "Assignment"
        verbose_name_plural = "Assignments"
        ordering = ['assignment_date', 'soldier__name']
    
    def __str__(self):
        status = "On Base" if self.is_on_base else "At Home"
        return f"{self.soldier.name} on {self.assignment_date}: {status}"