#!/usr/bin/env python
"""
Create comprehensive test data to verify admin site functionality
This creates realistic test scenarios with proper soldier-event associations
"""

import os
import django
from datetime import date, timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schedule_manage.settings')
django.setup()

from schedule.models import Event, Soldier, SoldierConstraint, SchedulingRun

def create_comprehensive_test_data():
    """Create realistic test data for admin site verification"""
    
    print("Creating comprehensive test data...")
    print("=" * 50)
    
    # 1. Create multiple events with different configurations
    print("\n1. Creating events with different rule configurations...")
    
    # Event 1: Standard Training - Basic settings
    event1 = Event.objects.create(
        name="Basic Training Exercise",
        event_type="TRAINING", 
        description="Standard military training with basic scheduling rules",
        start_date=date.today(),
        end_date=date.today() + timedelta(days=30),
        
        # Core settings
        min_required_soldiers_per_day=8,
        base_days_per_soldier=15,
        home_days_per_soldier=15,
        max_consecutive_base_days=7,
        max_consecutive_home_days=10,
        min_base_block_days=3,
        
        # Dynamic algorithm settings (user-configurable)
        exceptional_constraint_threshold=8,
        constraint_safety_margin_percent=20,
        weekend_only_max_base_days=10,
        
        # Algorithm weights
        enable_home_balance_penalty=True,
        enable_weekend_fairness_weight=True,
        home_balance_weight=1.0,
        weekend_fairness_weight=1.0,
        
        # Flexibility
        allow_single_day_blocks=False,
        strict_consecutive_limits=True,
        auto_adjust_for_constraints=True
    )
    
    # Event 2: Intensive Exercise - Strict settings
    event2 = Event.objects.create(
        name="Intensive Combat Exercise",
        event_type="EXERCISE",
        description="High-intensity exercise with strict scheduling requirements",
        start_date=date.today() + timedelta(days=35),
        end_date=date.today() + timedelta(days=65),
        
        # Stricter core settings
        min_required_soldiers_per_day=12,
        base_days_per_soldier=20,
        home_days_per_soldier=10,
        max_consecutive_base_days=10,
        max_consecutive_home_days=7,
        min_base_block_days=5,
        
        # Stricter algorithm settings
        exceptional_constraint_threshold=5,
        constraint_safety_margin_percent=30,
        weekend_only_max_base_days=7,
        
        # Higher weights for strictness
        enable_home_balance_penalty=True,
        enable_weekend_fairness_weight=True,
        home_balance_weight=1.5,
        weekend_fairness_weight=1.5,
        
        # Strict flexibility
        allow_single_day_blocks=False,
        strict_consecutive_limits=True,
        auto_adjust_for_constraints=False  # No auto-adjustment
    )
    
    # Event 3: Flexible Maintenance - Relaxed settings
    event3 = Event.objects.create(
        name="Equipment Maintenance Period",
        event_type="MAINTENANCE",
        description="Flexible maintenance schedule with relaxed constraints",
        start_date=date.today() + timedelta(days=70),
        end_date=date.today() + timedelta(days=100),
        
        # Relaxed core settings
        min_required_soldiers_per_day=5,
        base_days_per_soldier=10,
        home_days_per_soldier=20,
        max_consecutive_base_days=5,
        max_consecutive_home_days=15,
        min_base_block_days=2,
        
        # Relaxed algorithm settings
        exceptional_constraint_threshold=15,
        constraint_safety_margin_percent=40,
        weekend_only_max_base_days=20,
        
        # Lower weights for flexibility
        enable_home_balance_penalty=False,
        enable_weekend_fairness_weight=False,
        home_balance_weight=0.5,
        weekend_fairness_weight=0.5,
        
        # Maximum flexibility
        allow_single_day_blocks=True,
        strict_consecutive_limits=False,
        auto_adjust_for_constraints=True
    )
    
    print(f"OK Created 3 events with different rule configurations")
    
    # 2. Create soldiers for each event
    print("\n2. Creating soldiers with various characteristics...")
    
    soldiers = []
    
    # Event 1 soldiers (Basic Training)
    for i in range(1, 11):
        soldier = Soldier.objects.create(
            event=event1,
            name=f"Trainee {i:02d}",
            soldier_id=f"T{i:03d}",
            rank="PRIVATE" if i <= 6 else "CORPORAL" if i <= 8 else "SERGEANT",
            is_exceptional_output=(i in [9, 10]),  # 2 exceptional soldiers
            is_weekend_only_soldier_flag=(i in [8])  # 1 weekend-only soldier
        )
        soldiers.append(soldier)
    
    # Event 2 soldiers (Intensive Exercise)
    for i in range(1, 16):
        soldier = Soldier.objects.create(
            event=event2,
            name=f"Combat {i:02d}",
            soldier_id=f"C{i:03d}",
            rank="PRIVATE" if i <= 8 else "CORPORAL" if i <= 12 else "SERGEANT" if i <= 14 else "LIEUTENANT",
            is_exceptional_output=(i in [13, 14, 15]),  # 3 exceptional soldiers
            is_weekend_only_soldier_flag=(i in [11, 12])  # 2 weekend-only soldiers
        )
        soldiers.append(soldier)
    
    # Event 3 soldiers (Maintenance)
    for i in range(1, 8):
        soldier = Soldier.objects.create(
            event=event3,
            name=f"Tech {i:02d}",
            soldier_id=f"M{i:03d}",
            rank="PRIVATE" if i <= 3 else "CORPORAL" if i <= 5 else "SERGEANT",
            is_exceptional_output=(i in [7]),  # 1 exceptional soldier
            is_weekend_only_soldier_flag=(i in [5, 6])  # 2 weekend-only soldiers
        )
        soldiers.append(soldier)
    
    print(f"OK Created {len(soldiers)} soldiers across all events")
    
    # 3. Add realistic constraints
    print("\n3. Adding realistic constraints to soldiers...")
    
    constraint_count = 0
    
    # Add constraints to exceptional soldiers
    exceptional_soldiers = [s for s in soldiers if s.is_exceptional_output]
    for soldier in exceptional_soldiers:
        event_start = soldier.event.start_date
        event_end = soldier.event.end_date
        
        # Add 5-12 constraints for exceptional soldiers
        num_constraints = 7 if soldier.event.event_type == "TRAINING" else 10
        
        for j in range(num_constraints):
            constraint_date = event_start + timedelta(days=j*3 + 2)  # Every 3 days
            if constraint_date <= event_end:
                SoldierConstraint.objects.create(
                    soldier=soldier,
                    constraint_date=constraint_date,
                    constraint_type="PERSONAL" if j % 2 == 0 else "MEDICAL",
                    description=f"Constraint {j+1} - {'Personal leave' if j % 2 == 0 else 'Medical appointment'}"
                )
                constraint_count += 1
    
    # Add some constraints to regular soldiers too
    regular_soldiers = [s for s in soldiers if not s.is_exceptional_output and not s.is_weekend_only_soldier_flag]
    for i, soldier in enumerate(regular_soldiers[:len(regular_soldiers)//2]):  # Half of regular soldiers
        event_start = soldier.event.start_date
        
        # Add 1-3 constraints for regular soldiers
        for j in range(2):
            constraint_date = event_start + timedelta(days=10 + j*7)
            SoldierConstraint.objects.create(
                soldier=soldier,
                constraint_date=constraint_date,
                constraint_type="FAMILY" if j == 0 else "TRAINING",
                description=f"{'Family event' if j == 0 else 'External training'}"
            )
            constraint_count += 1
    
    print(f"OK Added {constraint_count} constraints")
    
    # 4. Create scheduling runs
    print("\n4. Creating scheduling runs...")
    
    runs = []
    for event in [event1, event2, event3]:
        run = SchedulingRun.objects.create(
            event=event,
            name=f"Schedule for {event.name}",
            description=f"Automatic scheduling run for {event.name} - all soldiers included"
            # Note: soldiers_ids not set - will use all soldiers from event automatically
        )
        runs.append(run)
    
    print(f"OK Created {len(runs)} scheduling runs")
    
    # 5. Summary
    print("\n" + "="*50)
    print("COMPREHENSIVE TEST DATA CREATED")
    print("="*50)
    
    print("\nEVENTS:")
    for event in [event1, event2, event3]:
        print(f"  {event.id}. {event.name}")
        print(f"     Type: {event.event_type}")
        print(f"     Soldiers: {event.soldiers.count()}")
        print(f"     Rules: {'Strict' if event.strict_consecutive_limits else 'Flexible'}")
        print(f"     Auto-adjust: {'Yes' if event.auto_adjust_for_constraints else 'No'}")
        print(f"     Exception threshold: {event.exceptional_constraint_threshold}")
        print()
    
    print("SOLDIERS BY EVENT:")
    for event in [event1, event2, event3]:
        soldiers_in_event = event.soldiers.all()
        exceptional = soldiers_in_event.filter(is_exceptional_output=True).count()
        weekend_only = soldiers_in_event.filter(is_weekend_only_soldier_flag=True).count()
        constraints = SoldierConstraint.objects.filter(soldier__event=event).count()
        
        print(f"  {event.name}:")
        print(f"    Total: {soldiers_in_event.count()}")
        print(f"    Exceptional: {exceptional}")
        print(f"    Weekend-only: {weekend_only}")
        print(f"    Total constraints: {constraints}")
        print()
    
    print("ADMIN SITE TEST URLS:")
    print("  Events: http://127.0.0.1:8080/admin/schedule/event/")
    print("  Soldiers: http://127.0.0.1:8080/admin/schedule/soldier/")
    print("  Constraints: http://127.0.0.1:8080/admin/schedule/soldierconstraint/")
    print("  Scheduling Runs: http://127.0.0.1:8080/admin/schedule/schedulingrun/")
    
    print("\nAPI TEST EXAMPLES:")
    print(f"  GET /api/soldiers/?event={event1.id}  (should show {event1.soldiers.count()} soldiers)")
    print(f"  POST /api/scheduling-runs/{runs[0].id}/execute_algorithm/  (run algorithm)")
    
    return {
        'events': [event1, event2, event3],
        'soldiers': soldiers,
        'runs': runs,
        'constraint_count': constraint_count
    }

if __name__ == '__main__':
    create_comprehensive_test_data()