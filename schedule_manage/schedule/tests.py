# schedule/tests.py
"""
Simple tests for the simplified schedule management system
"""

from django.test import TestCase
from django.contrib.auth.models import User
from datetime import date, timedelta
from .models import Event, Soldier, SchedulingRun, SoldierConstraint, Assignment


class EventModelTest(TestCase):
    """Test the Event model"""
    
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        
    def test_create_event(self):
        """Test creating a simple event"""
        event = Event.objects.create(
            name="Test Training",
            event_type="TRAINING",
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
            min_required_soldiers_per_day=10,
            created_by=self.user
        )
        
        self.assertEqual(event.name, "Test Training")
        self.assertEqual(event.event_type, "TRAINING")
        self.assertEqual(event.min_required_soldiers_per_day, 10)


class SoldierModelTest(TestCase):
    """Test the Soldier model"""
    
    def test_create_soldier(self):
        """Test creating a soldier"""
        soldier = Soldier.objects.create(
            name="John Doe",
            rank="PRIVATE",
            soldier_id="S001"
        )
        
        self.assertEqual(soldier.name, "John Doe")
        self.assertEqual(soldier.rank, "PRIVATE")
        self.assertEqual(soldier.soldier_id, "S001")
        self.assertFalse(soldier.is_exceptional_output)
        self.assertFalse(soldier.is_weekend_only_soldier_flag)


class SoldierConstraintModelTest(TestCase):
    """Test the SoldierConstraint model"""
    
    def test_create_constraint(self):
        """Test creating a soldier constraint"""
        soldier = Soldier.objects.create(name="Jane Doe", rank="CORPORAL")
        constraint = SoldierConstraint.objects.create(
            soldier=soldier,
            constraint_date=date.today() + timedelta(days=5),
            constraint_type="PERSONAL",
            description="Personal leave"
        )
        
        self.assertEqual(constraint.soldier, soldier)
        self.assertEqual(constraint.constraint_type, "PERSONAL")
        self.assertEqual(constraint.description, "Personal leave")


class SchedulingRunModelTest(TestCase):
    """Test the SchedulingRun model"""
    
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.event = Event.objects.create(
            name="Test Event",
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
            created_by=self.user
        )
        self.soldiers = [
            Soldier.objects.create(name=f"Soldier {i}", rank="PRIVATE") 
            for i in range(1, 6)
        ]
        
    def test_create_scheduling_run(self):
        """Test creating a scheduling run"""
        run = SchedulingRun.objects.create(
            name="Test Schedule",
            event=self.event,
            created_by=self.user
        )
        
        # Add soldiers to the run
        run.soldiers.set(self.soldiers)
        
        self.assertEqual(run.name, "Test Schedule")
        self.assertEqual(run.event, self.event)
        self.assertEqual(run.status, "PENDING")
        self.assertEqual(run.soldiers.count(), 5)
        
    def test_get_target_soldiers(self):
        """Test getting target soldiers from scheduling run"""
        run = SchedulingRun.objects.create(
            name="Test Schedule",
            event=self.event,
            created_by=self.user
        )
        run.soldiers.set(self.soldiers[:3])  # Add only first 3 soldiers
        
        target_soldiers = run.get_target_soldiers()
        self.assertEqual(target_soldiers.count(), 3)


class AssignmentModelTest(TestCase):
    """Test the Assignment model"""
    
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.event = Event.objects.create(
            name="Test Event",
            start_date=date.today(),
            end_date=date.today() + timedelta(days=7),
            created_by=self.user
        )
        self.soldier = Soldier.objects.create(name="Test Soldier", rank="PRIVATE")
        self.scheduling_run = SchedulingRun.objects.create(
            name="Test Schedule",
            event=self.event,
            created_by=self.user
        )
        
    def test_create_assignment(self):
        """Test creating an assignment"""
        assignment = Assignment.objects.create(
            scheduling_run=self.scheduling_run,
            soldier=self.soldier,
            assignment_date=date.today(),
            is_on_base=True
        )
        
        self.assertEqual(assignment.scheduling_run, self.scheduling_run)
        self.assertEqual(assignment.soldier, self.soldier)
        self.assertTrue(assignment.is_on_base)
        self.assertEqual(assignment.assignment_date, date.today())


class IntegrationTest(TestCase):
    """Test the complete flow"""
    
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        
    def test_complete_scheduling_flow(self):
        """Test the complete event -> schedule -> soldiers flow"""
        # 1. Create an event
        event = Event.objects.create(
            name="Integration Test Event",
            event_type="TRAINING",
            start_date=date.today(),
            end_date=date.today() + timedelta(days=14),
            min_required_soldiers_per_day=3,
            base_days_per_soldier=7,
            home_days_per_soldier=7,
            created_by=self.user
        )
        
        # 2. Create soldiers
        soldiers = []
        for i in range(1, 6):
            soldier = Soldier.objects.create(
                name=f"Soldier {i}",
                rank="PRIVATE",
                soldier_id=f"S00{i}"
            )
            soldiers.append(soldier)
        
        # 3. Add some constraints
        SoldierConstraint.objects.create(
            soldier=soldiers[0],
            constraint_date=date.today() + timedelta(days=5),
            constraint_type="PERSONAL"
        )
        
        # 4. Create scheduling run
        scheduling_run = SchedulingRun.objects.create(
            name="Integration Test Schedule",
            event=event,
            created_by=self.user
        )
        scheduling_run.soldiers.set(soldiers)
        
        # 5. Verify the setup
        self.assertEqual(event.name, "Integration Test Event")
        self.assertEqual(scheduling_run.soldiers.count(), 5)
        self.assertEqual(soldiers[0].constraints.count(), 1)
        self.assertEqual(scheduling_run.status, "PENDING")
        
        # The algorithm execution would be tested separately or mocked