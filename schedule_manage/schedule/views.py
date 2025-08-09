# schedule/views.py
# Enhanced API views with hierarchical organizational structure

from typing import List
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.core.cache import cache
from django.db.models import Prefetch, Q
from django.db import transaction
from datetime import date, timedelta
import logging

# Set up logger
logger = logging.getLogger(__name__)

from .models import (
    Organization, Unit, ImportBatch, Soldier, SoldierConstraint, 
    SchedulingRun, Assignment, Event, UserOrganizationRole
)
from .serializers import (
    OrganizationSerializer, UnitListSerializer, UnitDetailSerializer,
    ImportBatchSerializer, SoldierSerializer, SoldierConstraintSerializer, 
    SchedulingRunSerializer, AssignmentSerializer, EventSerializer,
    UserOrganizationRoleSerializer
)

# Import scheduling algorithm components
try:
    from .algorithms import SmartScheduleSoldiers
    from .algorithms.soldier import Soldier as AlgorithmSoldier
    from .tasks import run_scheduling_algorithm_async
except ImportError as e:
    logger.warning(f"Failed to import scheduling components: {e}")
    SmartScheduleSoldiers = None
    AlgorithmSoldier = None
    run_scheduling_algorithm_async = None

logger = logging.getLogger(__name__)


class OrganizationViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing organizations - top level containers
    """
    queryset = Organization.objects.all()
    
    @action(detail=True, methods=['get'])
    def units_hierarchy(self, request, pk=None):
        """Get complete unit hierarchy for organization"""
        organization = self.get_object()
        
        def build_hierarchy(parent_unit=None):
            units = Unit.objects.filter(
                organization=organization,
                parent_unit=parent_unit
            ).prefetch_related('soldiers')
            
            result = []
            for unit in units:
                unit_data = {
                    'id': unit.id,
                    'name': unit.name,
                    'code': unit.code,
                    'unit_type': unit.unit_type,
                    'soldier_count': unit.soldiers.filter(status='ACTIVE').count(),
                    'sub_units': build_hierarchy(unit)
                }
                result.append(unit_data)
            return result
        
        hierarchy = build_hierarchy()
        return Response(hierarchy)
    
    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        """Get organization statistics"""
        organization = self.get_object()
        
        stats = {
            'total_units': organization.units.count(),
            'total_soldiers': organization.soldiers.filter(status='ACTIVE').count(),
            'recent_imports': organization.import_batches.count(),
            'active_schedules': organization.scheduling_runs.filter(
                status__in=['IN_PROGRESS', 'SUCCESS']
            ).count(),
            'upcoming_events': organization.events.filter(
                start_date__gte=date.today()
            ).count()
        }
        
        return Response(stats)


class UnitViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing units with hierarchy support
    Units are the key to separating soldier lists and events
    """
    queryset = Unit.objects.select_related('organization', 'parent_unit').all()
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by organization if specified
        org_id = self.request.query_params.get('organization')
        if org_id:
            queryset = queryset.filter(organization_id=org_id)
        
        # Filter by unit type if specified
        unit_type = self.request.query_params.get('unit_type')
        if unit_type:
            queryset = queryset.filter(unit_type=unit_type)
        
        # Filter by parent unit if specified
        parent_id = self.request.query_params.get('parent_unit')
        if parent_id:
            queryset = queryset.filter(parent_unit_id=parent_id)
        elif self.request.query_params.get('top_level') == 'true':
            queryset = queryset.filter(parent_unit__isnull=True)
        
        return queryset
    
    @action(detail=True, methods=['get'])
    def soldiers(self, request, pk=None):
        """Get all soldiers in unit and sub-units"""
        unit = self.get_object()
        soldiers = unit.get_all_soldiers().filter(status='ACTIVE').select_related('unit')
        
        # Simple soldier data
        soldier_data = []
        for soldier in soldiers:
            soldier_data.append({
                'id': soldier.id,
                'name': soldier.name,
                'rank': soldier.rank,
                'unit_code': soldier.unit.code,
                'is_exceptional_output': soldier.is_exceptional_output,
                'is_weekend_only_soldier_flag': soldier.is_weekend_only_soldier_flag
            })
        
        return Response(soldier_data)
    
    @action(detail=True, methods=['post'])
    def bulk_create_soldiers(self, request, pk=None):
        """
        Create multiple soldiers for this specific unit
        This is how you separate soldier lists between events
        """
        unit = self.get_object()
        soldiers_data = request.data
        
        if not isinstance(soldiers_data, list):
            return Response(
                {"error": "Expected list of soldier data"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        created_soldiers = []
        errors = []
        
        # Create import batch to track this soldier list
        import_batch = ImportBatch.objects.create(
            name=f"Bulk Import - {unit.name}",
            organization=unit.organization,
            unit=unit,
            imported_by=request.user if request.user.is_authenticated else None,
            total_soldiers=len(soldiers_data)
        )
        
        with transaction.atomic():
            for i, soldier_data in enumerate(soldiers_data):
                try:
                    # Validate and sanitize soldier data
                    allowed_fields = {'name', 'soldier_id', 'rank', 'status', 'phone', 'email', 'notes'}
                    sanitized_data = {k: v for k, v in soldier_data.items() if k in allowed_fields}
                    
                    # Generate soldier ID if not provided
                    if 'soldier_id' not in sanitized_data:
                        sanitized_data['soldier_id'] = f"{unit.code}_{i+1:04d}"
                    
                    soldier = Soldier.objects.create(
                        organization=unit.organization,
                        unit=unit,
                        import_batch=import_batch,
                        **sanitized_data
                    )
                    created_soldiers.append(soldier)
                    import_batch.successful_imports += 1
                    
                except Exception as e:
                    errors.append({
                        'index': i,
                        'data': soldier_data,
                        'error': str(e)
                    })
                    import_batch.failed_imports += 1
        
        import_batch.save()
        
        return Response({
            'import_batch_id': import_batch.id,
            'created_count': len(created_soldiers),
            'error_count': len(errors),
            'errors': errors,
            'created_soldiers': [
                {'id': s.id, 'name': s.name, 'soldier_id': s.soldier_id} 
                for s in created_soldiers
            ]
        })
    
    @action(detail=True, methods=['post'])
    def create_event_for_unit(self, request, pk=None):
        """
        Create event targeting this entire unit
        This ensures events only run on specific unit's soldiers
        """
        unit = self.get_object()
        event_data = request.data.copy()
        
        # Create event
        event = Event.objects.create(
            organization=unit.organization,
            created_by=request.user if request.user.is_authenticated else None,
            **{k: v for k, v in event_data.items() if k not in ['target_units', 'specific_soldiers']}
        )
        
        # Add this unit as target
        event.target_units.add(unit)
        
        return Response({
            'event_id': event.id,
            'name': event.name,
            'target_unit': unit.name,
            'soldier_count': unit.get_all_soldiers().filter(status='ACTIVE').count()
        })
    
    @action(detail=True, methods=['post'])
    def run_schedule_for_unit(self, request, pk=None):
        """
        Run scheduling algorithm for only this unit's soldiers
        This is how you create separate schedules for separate events
        """
        unit = self.get_object()
        schedule_data = request.data.copy()
        
        # Create scheduling run targeting only this unit
        scheduling_run = SchedulingRun.objects.create(
            organization=unit.organization,
            name=f"Schedule for {unit.name}",
            created_by=request.user if request.user.is_authenticated else None,
            **{k: v for k, v in schedule_data.items() if k not in ['target_units']}
        )
        
        # Target only this unit
        scheduling_run.target_units.add(unit)
        
        # Get soldiers for this unit only
        target_soldiers = unit.get_all_soldiers().filter(status='ACTIVE')
        
        return Response({
            'scheduling_run_id': scheduling_run.id,
            'name': scheduling_run.name,
            'target_unit': unit.name,
            'target_soldier_count': target_soldiers.count(),
            'status': 'Created - ready to execute'
        })


class SoldierViewSet(viewsets.ModelViewSet):
    """
    Enhanced soldier management with organizational context
    """
    queryset = Soldier.objects.select_related('organization', 'unit', 'import_batch').prefetch_related(
        Prefetch('constraints', queryset=SoldierConstraint.objects.order_by('constraint_date'))
    )
    serializer_class = SoldierSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by organization
        org_id = self.request.query_params.get('organization')
        if org_id:
            queryset = queryset.filter(organization_id=org_id)
        
        # Filter by unit
        unit_id = self.request.query_params.get('unit')
        if unit_id:
            queryset = queryset.filter(unit_id=unit_id)
        
        # Filter by import batch (to see soldiers from specific imports)
        batch_id = self.request.query_params.get('import_batch')
        if batch_id:
            queryset = queryset.filter(import_batch_id=batch_id)
        
        # Filter by status
        status_filter = self.request.query_params.get('status', 'ACTIVE')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset


class EventViewSet(viewsets.ModelViewSet):
    """
    Enhanced event management with unit targeting
    """
    queryset = Event.objects.select_related('organization').prefetch_related(
        'target_units', 'specific_soldiers'
    )
    serializer_class = EventSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by organization
        org_id = self.request.query_params.get('organization')
        if org_id:
            queryset = queryset.filter(organization_id=org_id)
        
        # Filter by unit
        unit_id = self.request.query_params.get('unit')
        if unit_id:
            queryset = queryset.filter(target_units__id=unit_id)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(start_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(end_date__lte=end_date)
        
        return queryset
    
    @action(detail=True, methods=['get'])
    def target_soldiers(self, request, pk=None):
        """Get all soldiers that will be affected by this event"""
        event = self.get_object()
        soldiers = event.get_target_soldiers()
        
        soldier_data = []
        for soldier in soldiers:
            soldier_data.append({
                'id': soldier.id,
                'name': soldier.name,
                'rank': soldier.rank,
                'unit': soldier.unit.name,
                'unit_code': soldier.unit.code
            })
        
        return Response({
            'event_name': event.name,
            'total_soldiers': len(soldiers),
            'soldiers': soldier_data
        })


class SchedulingRunViewSet(viewsets.ModelViewSet):
    """
    Enhanced scheduling run management with unit targeting
    """
    queryset = SchedulingRun.objects.select_related('organization').prefetch_related(
        'target_units', 'assignments__soldier'
    )
    serializer_class = SchedulingRunSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by organization
        org_id = self.request.query_params.get('organization')
        if org_id:
            queryset = queryset.filter(organization_id=org_id)
        
        # Filter by unit
        unit_id = self.request.query_params.get('unit')
        if unit_id:
            queryset = queryset.filter(target_units__id=unit_id)
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset
    
    def _convert_soldiers_to_algorithm_format(self, soldiers):
        """Convert Django soldiers to algorithm format"""
        algorithm_soldiers = []
        for soldier in soldiers:
            constraints = list(soldier.constraints.values_list('constraint_date', flat=True))
            algorithm_soldiers.append(AlgorithmSoldier(
                name=soldier.name,
                constraints=constraints,
                is_exceptional_output=soldier.is_exceptional_output,
                is_weekend_only_soldier_flag=soldier.is_weekend_only_soldier_flag
            ))
        return algorithm_soldiers
    
    def _save_algorithm_solution(self, solution, scheduling_run, target_soldiers):
        """Save algorithm solution to database"""
        assignments_created = 0
        for soldier_name, schedule in solution.items():
            soldier = target_soldiers.get(name=soldier_name)
            for date_str, is_on_base in schedule.items():
                Assignment.objects.create(
                    scheduling_run=scheduling_run,
                    soldier=soldier,
                    assignment_date=date_str,
                    is_on_base=is_on_base
                )
                assignments_created += 1
        return assignments_created
    
    def _run_scheduling_algorithm(self, scheduling_run, target_soldiers):
        """Execute the core scheduling algorithm"""
        if not (SmartScheduleSoldiers and AlgorithmSoldier):
            return None, 'Algorithm components not available'
        
        algorithm_soldiers = self._convert_soldiers_to_algorithm_format(target_soldiers)
        
        scheduler = SmartScheduleSoldiers()
        solution = scheduler.solve(
            soldiers=algorithm_soldiers,
            start_date=scheduling_run.start_date,
            end_date=scheduling_run.end_date,
            default_base_days_target=scheduling_run.default_base_days_target,
            default_home_days_target=scheduling_run.default_home_days_target,
            max_consecutive_base_days=scheduling_run.max_consecutive_base_days,
            max_consecutive_home_days=scheduling_run.max_consecutive_home_days,
            min_base_block_days=scheduling_run.min_base_block_days,
            min_required_soldiers_per_day=scheduling_run.min_required_soldiers_per_day
        )
        
        if solution:
            assignments_created = self._save_algorithm_solution(solution, scheduling_run, target_soldiers)
            return 'SUCCESS', f'Created {assignments_created} assignments'
        else:
            return 'NO_SOLUTION', 'Algorithm could not find a feasible solution'
    
    @action(detail=True, methods=['post'])
    def execute_algorithm(self, request, pk=None):
        """Execute the scheduling algorithm for this run"""
        scheduling_run = self.get_object()
        
        if scheduling_run.status != 'PENDING':
            return Response(
                {"error": "Scheduling run is not in PENDING status"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        scheduling_run.status = 'IN_PROGRESS'
        scheduling_run.save()
        
        try:
            target_soldiers = scheduling_run.get_target_soldiers().prefetch_related('constraints')
            
            if not target_soldiers.exists():
                scheduling_run.status = 'FAILURE'
                scheduling_run.solution_details = 'No target soldiers found'
                scheduling_run.save()
                return Response(
                    {"error": "No target soldiers found"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            status_result, details = self._run_scheduling_algorithm(scheduling_run, target_soldiers)
            scheduling_run.status = status_result
            scheduling_run.solution_details = details
            scheduling_run.save()
            
            return Response({
                'status': scheduling_run.status,
                'details': scheduling_run.solution_details,
                'target_soldiers': target_soldiers.count()
            })
            
        except Exception as e:
            scheduling_run.status = 'FAILURE'
            scheduling_run.solution_details = f'Error: {str(e)}'
            scheduling_run.save()
            
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AssignmentViewSet(viewsets.ModelViewSet):
    """
    Enhanced assignment management
    """
    queryset = Assignment.objects.select_related(
        'scheduling_run', 'soldier__unit', 'soldier__organization'
    )
    serializer_class = AssignmentSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by scheduling run
        run_id = self.request.query_params.get('scheduling_run')
        if run_id:
            queryset = queryset.filter(scheduling_run_id=run_id)
        
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
        
        return queryset


class SoldierConstraintViewSet(viewsets.ModelViewSet):
    """
    Enhanced soldier constraint management
    """
    queryset = SoldierConstraint.objects.select_related('soldier__unit', 'created_by')
    serializer_class = SoldierConstraintSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by soldier
        soldier_id = self.request.query_params.get('soldier')
        if soldier_id:
            queryset = queryset.filter(soldier_id=soldier_id)
        
        # Filter by unit
        unit_id = self.request.query_params.get('unit')
        if unit_id:
            queryset = queryset.filter(soldier__unit_id=unit_id)
        
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
        
        return queryset


class ImportBatchViewSet(viewsets.ModelViewSet):
    """
    Track and manage soldier import batches
    """
    queryset = ImportBatch.objects.select_related('organization', 'unit', 'imported_by').prefetch_related('soldiers')
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by organization
        org_id = self.request.query_params.get('organization')
        if org_id:
            queryset = queryset.filter(organization_id=org_id)
        
        # Filter by unit
        unit_id = self.request.query_params.get('unit')
        if unit_id:
            queryset = queryset.filter(unit_id=unit_id)
        
        return queryset
    
    @action(detail=True, methods=['get'])
    def soldiers(self, request, pk=None):
        """Get all soldiers from this import batch"""
        import_batch = self.get_object()
        soldiers = import_batch.soldiers.all()
        
        soldier_data = []
        for soldier in soldiers:
            soldier_data.append({
                'id': soldier.id,
                'name': soldier.name,
                'soldier_id': soldier.soldier_id,
                'rank': soldier.rank,
                'unit': soldier.unit.name,
                'status': soldier.status
            })
        
        return Response({
            'import_batch': import_batch.name,
            'total_soldiers': soldiers.count(),
            'soldiers': soldier_data
        })