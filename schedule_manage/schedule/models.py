# schedule/models.py

from django.db import models
from django.utils import timezone
import datetime

class Soldier(models.Model):
    """
    Model representing a soldier in the scheduling system.
    """
    name = models.CharField(max_length=100, unique=True, verbose_name="Soldier Name")
    # New fields according to the Soldier class of the algorithm
    is_exceptional_output = models.BooleanField(default=False, verbose_name="Exceptional Output/Sequence?")
    is_weekend_only_soldier_flag = models.BooleanField(default=False, verbose_name="Weekend Only Soldier?")
    
    # No need to store base_dates and home_dates here, they will be stored in the Assignment model

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Soldier"
        verbose_name_plural = "Soldiers"

class SoldierConstraint(models.Model):
    """
    Model representing a date constraint for a specific soldier (e.g., days off).
    """
    soldier = models.ForeignKey(Soldier, related_name='constraints', on_delete=models.CASCADE, verbose_name="Soldier")
    constraint_date = models.DateField(verbose_name="Constraint Date")
    description = models.TextField(blank=True, null=True, verbose_name="Constraint Description")

    def __str__(self):
        return f"{self.soldier.name} - Constraint on {self.constraint_date}"

    class Meta:
        unique_together = ('soldier', 'constraint_date') # One constraint per soldier per day
        verbose_name = "Soldier Constraint"
        verbose_name_plural = "Soldier Constraints"
        ordering = ['constraint_date']

    def save(self, *args, **kwargs):
        is_new = self._state.adding # Check if this is a new object
        super().save(*args, **kwargs) # Save the SoldierConstraint object first

        if is_new:
            # If this is a new constraint, create a linked event
            event = Event.objects.create(
                event_type='CONSTRAINT',
                name=f"Constraint for Soldier {self.soldier.name}",
                description=self.description,
                start_date=self.constraint_date,
                end_date=self.constraint_date,
                soldier_constraint=self
            )
            event.soldiers.add(self.soldier)
        else:
            # If this is an existing constraint that was updated, update the linked event
            if hasattr(self, 'event_link') and self.event_link:
                event = self.event_link # Get the linked event
                event.name = f"Constraint for Soldier {self.soldier.name}"
                event.description = self.description
                event.start_date = self.constraint_date
                event.end_date = self.constraint_date
                event.save()
                # Ensure the soldier is associated with the event
                event.soldiers.add(self.soldier)
            else:
                # If for some reason there is no existing link, create a new one
                event = Event.objects.create(
                    event_type='CONSTRAINT',
                    name=f"Constraint for Soldier {self.soldier.name}",
                    description=self.description,
                    start_date=self.constraint_date,
                    end_date=self.constraint_date,
                    soldier_constraint=self
                )
                event.soldiers.add(self.soldier)

class SchedulingRun(models.Model):
    """
    Model representing a specific scheduling run, including its parameters and results.
    """
    run_date = models.DateTimeField(auto_now_add=True, verbose_name="Run Date")
    start_date = models.DateField(verbose_name="Start Date")
    end_date = models.DateField(verbose_name="End Date")
    default_base_days_target = models.IntegerField(verbose_name="Default Base Days Target")
    default_home_days_target = models.IntegerField(verbose_name="Default Home Days Target")
    max_consecutive_base_days = models.IntegerField(verbose_name="Max Consecutive Base Days")
    max_consecutive_home_days = models.IntegerField(verbose_name="Max Consecutive Home Days")
    min_base_block_days = models.IntegerField(verbose_name="Min Base Block Days")
    min_required_soldiers_per_day = models.IntegerField(verbose_name="Min Required Soldiers Per Day")
    max_total_home_days = models.IntegerField(null=True, blank=True, verbose_name="Max Total Home Days")
    # New: Field for maximum weekend base days per soldier
    max_weekend_base_days_per_soldier = models.IntegerField(null=True, blank=True, verbose_name="Max Weekend Base Days Per Soldier")
    
    # Run status (whether a solution was found, failed, etc.)
    STATUS_CHOICES = [
        ('SUCCESS', 'Successfully Completed'),
        ('FAILURE', 'Failed'),
        ('IN_PROGRESS', 'In Progress'),
        ('NO_SOLUTION', 'No Solution Found'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='IN_PROGRESS',
        verbose_name="Run Status"
    )
    solution_details = models.TextField(blank=True, null=True, verbose_name="Solution/Error Details")

    def __str__(self):
        return f"Schedule from {self.start_date} to {self.end_date} ({self.status})"

    class Meta:
        verbose_name = "Scheduling Run"
        verbose_name_plural = "Scheduling Runs"
        ordering = ['-run_date']

class Assignment(models.Model):
    """
    Model representing a soldier's assignment on a specific day (base/home), as part of a scheduling run.
    """
    scheduling_run = models.ForeignKey(SchedulingRun, related_name='assignments', on_delete=models.CASCADE, verbose_name="Scheduling Run")
    soldier = models.ForeignKey(Soldier, on_delete=models.CASCADE, verbose_name="Soldier")
    assignment_date = models.DateField(verbose_name="Assignment Date")
    is_on_base = models.BooleanField(verbose_name="Is on Base?")

    def __str__(self):
        status = "On Base" if self.is_on_base else "At Home"
        return f"{self.soldier.name} on {self.assignment_date}: {status}"

    class Meta:
        unique_together = ('scheduling_run', 'soldier', 'assignment_date') # One assignment per soldier per day
        verbose_name = "Assignment"
        verbose_name_plural = "Assignments"
        ordering = ['assignment_date', 'soldier__name']


class Event(models.Model):
    """
    Model representing a general event in the system.
    Can be a day off, training, or any other event affecting the schedule.
    """
    EVENT_TYPE_CHOICES = [
        ('CONSTRAINT', 'Soldier Constraint'),
        ('TRAINING', 'Training'),
        ('HOLIDAY', 'Holiday'),
        ('OTHER', 'Other'),
    ]
    
    event_type = models.CharField(
        max_length=20,
        choices=EVENT_TYPE_CHOICES,
        default='OTHER',
        verbose_name="Event Type"
    )
    name = models.CharField(max_length=200, verbose_name="Event Name")
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    start_date = models.DateField(verbose_name="Start Date")
    end_date = models.DateField(verbose_name="End Date")
    
    # New fields added
    min_required_soldiers = models.IntegerField(
        null=True, blank=True, 
        verbose_name="Min Required Soldiers for Event",
        help_text="Minimum number of soldiers required for this event per day."
    )
    max_home_days_per_soldier = models.IntegerField(
        null=True, blank=True, 
        verbose_name="Max Home Days Per Soldier (for this event)",
        help_text="Maximum home days limit per soldier during this event."
    )
    base_days_per_soldier = models.IntegerField(
        null=True, blank=True, 
        verbose_name="Base Days Per Soldier (for this event)",
        help_text="Target base days per soldier during this event."
    )
    home_days_per_soldier = models.IntegerField(
        null=True, blank=True, 
        verbose_name="Home Days Per Soldier (for this event)",
        help_text="Target home days per soldier during this event."
    )
    # End of new fields 

    # Soldiers associated with this specific event
    soldiers = models.ManyToManyField(Soldier, related_name='events', blank=True, verbose_name="Associated Soldiers")

    # Optional link to a specific soldier constraint (if event type is CONSTRAINT)
    soldier_constraint = models.OneToOneField(
        'SoldierConstraint', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='event_link',
        verbose_name="Linked Soldier Constraint"
    )

    def __str__(self):
        return f"{self.name} ({self.event_type}) from {self.start_date} to {self.end_date}"

    class Meta:
        verbose_name = "Event"
        verbose_name_plural = "Events"
        ordering = ['start_date']
