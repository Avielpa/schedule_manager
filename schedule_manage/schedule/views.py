# schedule/views.py
# Simplified API views for Event -> Schedule -> Soldiers flow

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import JSONParser, FormParser, MultiPartParser
from django.db import transaction
from datetime import date, timedelta
import logging
import json

# Set up logger
logger = logging.getLogger(__name__)

from .models import Event, Soldier, SoldierConstraint, SchedulingRun, Assignment
from .serializers import (
    EventSerializer, SoldierSerializer, SoldierConstraintSerializer, 
    SchedulingRunSerializer, SchedulingRunDetailSerializer, AssignmentSerializer
)

# Import scheduling algorithm components
try:
    from .algorithms.solver import SmartScheduleSoldiers
    from .algorithms.soldier import Soldier as AlgorithmSoldier
    from .tasks import run_scheduling_algorithm_async
except ImportError as e:
    logger.warning(f"Failed to import scheduling components: {e}")
    SmartScheduleSoldiers = None
    AlgorithmSoldier = None
    run_scheduling_algorithm_async = None


class EventViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing events with full JSON POST support
    
    Supports creating events via JSON POST:
    POST /api/events/
    Content-Type: application/json
    {
        "name": "Training Exercise",
        "event_type": "TRAINING",
        "description": "Advanced training",
        "start_date": "2025-01-01",
        "end_date": "2025-01-31",
        "min_required_soldiers_per_day": 10,
        "base_days_per_soldier": 15,
        "home_days_per_soldier": 16,
        "max_consecutive_base_days": 7,
        "max_consecutive_home_days": 10,
        "min_base_block_days": 3
    }
    """
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    parser_classes = [JSONParser, FormParser, MultiPartParser]
    
    def get_queryset(self):
        queryset = Event.objects.all()
        
        # Filter by event type
        event_type = self.request.query_params.get('event_type')
        if event_type:
            queryset = queryset.filter(event_type=event_type)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(start_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(end_date__lte=end_date)
        
        return queryset.order_by('-created_at')


class SoldierViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing soldiers with event association
    
    Supports creating soldiers via JSON POST:
    POST /api/soldiers/
    Content-Type: application/json
    {
        "event_id": 1,
        "name": "John Doe",
        "soldier_id": "S001",
        "rank": "PRIVATE", 
        "is_exceptional_output": false,
        "is_weekend_only_soldier_flag": false,
        "constraints_data": [
            {
                "constraint_date": "2025-01-15",
                "constraint_type": "MEDICAL",
                "description": "Medical appointment"
            }
        ]
    }
    
    Filter soldiers by event:
    GET /api/soldiers/?event=1
    
    Also supports bulk creation:
    POST /api/soldiers/bulk_create/
    [
        {"event_id": 1, "name": "Soldier 1", "soldier_id": "S001", "rank": "PRIVATE"},
        {"event_id": 1, "name": "Soldier 2", "soldier_id": "S002", "rank": "CORPORAL"}
    ]
    """
    queryset = Soldier.objects.all()
    serializer_class = SoldierSerializer
    parser_classes = [JSONParser, FormParser, MultiPartParser]
    
    def get_serializer_class(self):
        """Use detailed serializer for create/update operations"""
        if self.action in ['create', 'update', 'partial_update']:
            from .serializers import SoldierDetailSerializer
            return SoldierDetailSerializer
        return SoldierSerializer
    
    def get_queryset(self):
        queryset = Soldier.objects.select_related('event')
        
        # Filter by event (important!)
        event_id = self.request.query_params.get('event')
        if event_id:
            queryset = queryset.filter(event_id=event_id)
        
        # Filter by rank
        rank = self.request.query_params.get('rank')
        if rank:
            queryset = queryset.filter(rank=rank)
        
        # Filter by special flags
        is_exceptional = self.request.query_params.get('is_exceptional')
        if is_exceptional is not None:
            queryset = queryset.filter(is_exceptional_output=is_exceptional.lower() == 'true')
        
        is_weekend_only = self.request.query_params.get('is_weekend_only')
        if is_weekend_only is not None:
            queryset = queryset.filter(is_weekend_only_soldier_flag=is_weekend_only.lower() == 'true')
        
        return queryset.order_by('event', 'rank', 'name')
    
    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        """
        Create multiple soldiers at once via JSON POST
        
        POST /api/soldiers/bulk_create/
        Content-Type: application/json
        [
            {
                "name": "Soldier 1",
                "soldier_id": "S001", 
                "rank": "PRIVATE",
                "is_exceptional_output": false,
                "is_weekend_only_soldier_flag": false
            },
            {
                "name": "Soldier 2",
                "soldier_id": "S002",
                "rank": "CORPORAL",
                "is_exceptional_output": true,
                "constraints_data": [
                    {
                        "constraint_date": "2025-01-15",
                        "constraint_type": "PERSONAL",
                        "description": "Leave"
                    }
                ]
            }
        ]
        """
        soldiers_data = request.data
        
        # Validate input is a list
        if not isinstance(soldiers_data, list):
            return Response(
                {"error": "Expected a JSON array of soldier objects"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if len(soldiers_data) == 0:
            return Response(
                {"error": "Cannot create empty list of soldiers"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        created_soldiers = []
        errors = []
        
        # Use detailed serializer for bulk creation
        from .serializers import SoldierDetailSerializer
        
        with transaction.atomic():
            for i, soldier_data in enumerate(soldiers_data):
                serializer = SoldierDetailSerializer(data=soldier_data, context={'request': request})
                if serializer.is_valid():
                    try:
                        soldier = serializer.save()
                        created_soldiers.append(SoldierDetailSerializer(soldier).data)
                    except Exception as e:
                        errors.append({"index": i, "error": str(e)})
                else:
                    errors.append({"index": i, "errors": serializer.errors})
        
        return Response({
            "created_soldiers": created_soldiers,
            "errors": errors,
            "summary": {
                "total": len(soldiers_data),
                "created": len(created_soldiers),
                "failed": len(errors)
            }
        })


class SoldierConstraintViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing soldier constraints with JSON POST support
    
    POST /api/soldier-constraints/
    Content-Type: application/json
    {
        "soldier": 1,
        "constraint_date": "2025-01-15",
        "constraint_type": "MEDICAL",
        "description": "Doctor appointment"
    }
    """
    queryset = SoldierConstraint.objects.all()
    serializer_class = SoldierConstraintSerializer
    parser_classes = [JSONParser, FormParser, MultiPartParser]
    
    def get_queryset(self):
        queryset = SoldierConstraint.objects.select_related('soldier')
        
        # Filter by soldier
        soldier_id = self.request.query_params.get('soldier')
        if soldier_id:
            queryset = queryset.filter(soldier_id=soldier_id)
        
        # Filter by constraint type
        constraint_type = self.request.query_params.get('constraint_type')
        if constraint_type:
            queryset = queryset.filter(constraint_type=constraint_type)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(constraint_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(constraint_date__lte=end_date)
        
        return queryset.order_by('constraint_date')


class SchedulingRunViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing scheduling runs with JSON POST support
    
    POST /api/scheduling-runs/
    Content-Type: application/json
    {
        "name": "January 2025 Schedule",
        "description": "Monthly schedule for training",
        "event_id": 1,
        "soldiers_ids": [1, 2, 3, 4, 5]  // Optional - if not provided, uses all soldiers from the event
    }
    
    Execute algorithm:
    POST /api/scheduling-runs/1/execute_algorithm/
    """
    queryset = SchedulingRun.objects.all()
    parser_classes = [JSONParser, FormParser, MultiPartParser]
    
    def get_serializer_class(self):
        if self.action in ['retrieve', 'create', 'update', 'partial_update']:
            return SchedulingRunDetailSerializer
        return SchedulingRunSerializer
    
    def get_queryset(self):
        queryset = SchedulingRun.objects.select_related('event', 'created_by').prefetch_related('soldiers')
        
        # Filter by event
        event_id = self.request.query_params.get('event')
        if event_id:
            queryset = queryset.filter(event_id=event_id)
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset.order_by('-created_at')
    
    @action(detail=True, methods=['post'])
    def execute_algorithm(self, request, pk=None):
        """Execute the scheduling algorithm for this run"""
        scheduling_run = self.get_object()
        
        if scheduling_run.status == 'IN_PROGRESS':
            return Response(
                {"error": "Algorithm is already running"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Clear existing assignments
        scheduling_run.assignments.all().delete()
        
        # Update status
        scheduling_run.status = 'IN_PROGRESS'
        scheduling_run.save()
        
        try:
            # Get soldiers and their constraints
            soldiers = scheduling_run.get_target_soldiers()
            if not soldiers.exists():
                scheduling_run.status = 'FAILURE'
                scheduling_run.solution_details = 'No soldiers available for scheduling'
                scheduling_run.save()
                return Response(
                    {"error": "No soldiers available for scheduling"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Convert to algorithm format
            algorithm_soldiers = []
            for soldier in soldiers:
                constraints = list(soldier.constraints.values_list('constraint_date', flat=True))
                # Convert date objects to ISO format strings
                constraint_strings = [d.isoformat() if hasattr(d, 'isoformat') else str(d) for d in constraints]
                algorithm_soldiers.append(AlgorithmSoldier(
                    id=str(soldier.id),
                    name=soldier.name,
                    unavailable_days=constraint_strings,
                    is_exceptional_output=soldier.is_exceptional_output,
                    is_weekend_only_soldier_flag=soldier.is_weekend_only_soldier_flag
                ))
            
            # Get parameters from event
            event = scheduling_run.event
            base_days = event.base_days_per_soldier or 30
            home_days = event.home_days_per_soldier or 25
            
            # Run the algorithm
            if SmartScheduleSoldiers:
                algorithm = SmartScheduleSoldiers(
                    soldiers=algorithm_soldiers,
                    start_date=event.start_date,
                    end_date=event.end_date,
                    default_base_days_target=base_days,
                    default_home_days_target=home_days,
                    max_consecutive_base_days=event.max_consecutive_base_days,
                    max_consecutive_home_days=event.max_consecutive_home_days,
                    min_base_block_days=event.min_base_block_days,
                    min_required_soldiers_per_day=event.min_required_soldiers_per_day
                )
                
                solution_data, status_code = algorithm.solve()
                
                if solution_data and status_code in [1, 2]:  # OPTIMAL or FEASIBLE
                    # Save assignments
                    assignments = []
                    for soldier_name, soldier_schedule in solution_data.items():
                        if soldier_name == 'daily_soldiers_count':
                            continue
                        
                        # Find the soldier by name
                        try:
                            soldier = soldiers.get(name=soldier_name)
                        except Soldier.DoesNotExist:
                            logger.warning(f"Soldier {soldier_name} not found in database")
                            continue
                        
                        # Create assignments from the schedule
                        for day_assignment in soldier_schedule['schedule']:
                            assignment_date = date.fromisoformat(day_assignment['date'])
                            is_on_base = day_assignment['status'] == 'Base'
                            
                            assignments.append(Assignment(
                                scheduling_run=scheduling_run,
                                soldier=soldier,
                                assignment_date=assignment_date,
                                is_on_base=is_on_base
                            ))
                    
                    Assignment.objects.bulk_create(assignments)
                    
                    scheduling_run.status = 'SUCCESS'
                    scheduling_run.solution_details = f"Successfully created {len(assignments)} assignments"
                    scheduling_run.save()
                    
                    return Response({
                        "message": "Algorithm executed successfully",
                        "assignments_created": len(assignments)
                    })
                else:
                    scheduling_run.status = 'NO_SOLUTION'
                    scheduling_run.solution_details = 'No feasible solution found'
                    scheduling_run.save()
                    
                    return Response(
                        {"error": "No feasible solution found"}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
            else:
                scheduling_run.status = 'FAILURE'
                scheduling_run.solution_details = 'Scheduling algorithm not available'
                scheduling_run.save()
                
                return Response(
                    {"error": "Scheduling algorithm not available"}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        except Exception as e:
            logger.error(f"Algorithm execution failed: {str(e)}")
            scheduling_run.status = 'FAILURE'
            scheduling_run.solution_details = f'Algorithm failed: {str(e)}'
            scheduling_run.save()
            
            return Response(
                {"error": f"Algorithm execution failed: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AssignmentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for viewing assignments (read-only)
    
    Provides filtered access to assignments:
    GET /api/assignments/
    GET /api/assignments/?scheduling_run=1
    GET /api/assignments/?soldier=1
    GET /api/assignments/?start_date=2025-01-01&end_date=2025-01-31
    
    Calendar view:
    GET /api/assignments/calendar/?scheduling_run=1
    """
    queryset = Assignment.objects.all()
    serializer_class = AssignmentSerializer
    parser_classes = [JSONParser, FormParser, MultiPartParser]
    
    def get_queryset(self):
        queryset = Assignment.objects.select_related('soldier', 'scheduling_run')
        
        # Filter by scheduling run
        scheduling_run_id = self.request.query_params.get('scheduling_run')
        if scheduling_run_id:
            queryset = queryset.filter(scheduling_run_id=scheduling_run_id)
        
        # Filter by soldier
        soldier_id = self.request.query_params.get('soldier')
        if soldier_id:
            queryset = queryset.filter(soldier_id=soldier_id)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(assignment_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(assignment_date__lte=end_date)
        
        # Filter by assignment type
        is_on_base = self.request.query_params.get('is_on_base')
        if is_on_base is not None:
            queryset = queryset.filter(is_on_base=is_on_base.lower() == 'true')
        
        return queryset.order_by('assignment_date', 'soldier__name')
    
    @action(detail=False, methods=['get'])
    def calendar(self, request):
        """Get assignments in calendar format"""
        queryset = self.filter_queryset(self.get_queryset())
        
        calendar_data = {}
        for assignment in queryset:
            date_str = assignment.assignment_date.strftime('%Y-%m-%d')
            if date_str not in calendar_data:
                calendar_data[date_str] = {'on_base': [], 'at_home': []}
            
            soldier_data = {
                'id': assignment.soldier.id,
                'name': assignment.soldier.name,
                'rank': assignment.soldier.rank
            }
            
            if assignment.is_on_base:
                calendar_data[date_str]['on_base'].append(soldier_data)
            else:
                calendar_data[date_str]['at_home'].append(soldier_data)
        
        return Response(calendar_data)