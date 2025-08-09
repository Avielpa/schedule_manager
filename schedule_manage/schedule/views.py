# schedule/views.py
# Simplified API views for Event -> Schedule -> Soldiers flow

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from datetime import date, timedelta
import logging

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
    API endpoint for managing events
    """
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    
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
    API endpoint for managing soldiers
    """
    queryset = Soldier.objects.all()
    serializer_class = SoldierSerializer
    
    def get_queryset(self):
        queryset = Soldier.objects.all()
        
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
        
        return queryset.order_by('rank', 'name')
    
    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        """Create multiple soldiers at once"""
        soldiers_data = request.data
        if not isinstance(soldiers_data, list):
            return Response(
                {"error": "Expected a list of soldiers"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        created_soldiers = []
        errors = []
        
        for i, soldier_data in enumerate(soldiers_data):
            serializer = self.get_serializer(data=soldier_data)
            if serializer.is_valid():
                soldier = serializer.save()
                created_soldiers.append(serializer.data)
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
    API endpoint for managing soldier constraints
    """
    queryset = SoldierConstraint.objects.all()
    serializer_class = SoldierConstraintSerializer
    
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
    API endpoint for managing scheduling runs
    """
    queryset = SchedulingRun.objects.all()
    
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
                algorithm_soldiers.append(AlgorithmSoldier(
                    soldier_id=soldier.id,
                    name=soldier.name,
                    constraints=constraints,
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
                    base_days_target=base_days,
                    home_days_target=home_days,
                    max_consecutive_base_days=event.max_consecutive_base_days,
                    max_consecutive_home_days=event.max_consecutive_home_days,
                    min_base_block_days=event.min_base_block_days,
                    min_required_soldiers_per_day=event.min_required_soldiers_per_day
                )
                
                success, assignments_data = algorithm.solve()
                
                if success:
                    # Save assignments
                    assignments = []
                    for assignment_data in assignments_data:
                        soldier = Soldier.objects.get(id=assignment_data['soldier_id'])
                        assignments.append(Assignment(
                            scheduling_run=scheduling_run,
                            soldier=soldier,
                            assignment_date=assignment_data['date'],
                            is_on_base=assignment_data['is_on_base']
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
    """
    queryset = Assignment.objects.all()
    serializer_class = AssignmentSerializer
    
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