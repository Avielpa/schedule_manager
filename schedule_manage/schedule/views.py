# schedule/views.py
# Full views.py file with all ViewSets + fixes

from typing import List
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .serializers import (
    SoldierSerializer, SoldierConstraintSerializer, SchedulingRunSerializer, 
    ScheduleCreateSerializer, ScheduleUpdateSerializer, AssignmentSerializer, EventSerializer
)
from .models import Soldier, SoldierConstraint, SchedulingRun, Assignment, Event
from datetime import date, timedelta
from .algorithms import SmartScheduleSoldiers
from .algorithms.soldier import Soldier as AlgorithmSoldier
from django.db import transaction
import traceback
from ortools.sat.python import cp_model


class SoldierViewSet(viewsets.ModelViewSet):
    queryset = Soldier.objects.all()
    serializer_class = SoldierSerializer

    def get_serializer_class(self):
        if self.action == 'add_constraint':
            return SoldierConstraintSerializer
        return super().get_serializer_class()

    @action(detail=True, methods=['post','get'], url_path='add_constraint')
    def add_constraint(self, request, pk=None):
        soldier = self.get_object()
        serializer = SoldierConstraintSerializer(data=request.data)
        if serializer.is_valid():
            constraint_date = serializer.validated_data['constraint_date']
            description = serializer.validated_data.get('description', '')

            constraint = SoldierConstraint.objects.create(
                soldier=soldier,
                constraint_date=constraint_date,
                description=description
            )
            return Response(SoldierConstraintSerializer(constraint).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], url_path='count')
    def count_soldiers(self, request):
        soldier_count = self.get_queryset().count()
        return Response({"total_soldiers": soldier_count}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='bulk_create')
    def bulk_create_soldiers(self, request):
        serializer = self.get_serializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)
        
        with transaction.atomic(): 
            serializer.save() 
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['put'], url_path='bulk_update')
    def bulk_update_soldiers(self, request):
        serializer = self.get_serializer(data=request.data, many=True, partial=True) 
        serializer.is_valid(raise_exception=True)

        soldier_ids_to_update = [item['id'] for item in request.data if 'id' in item]
        existing_soldiers = self.get_queryset().filter(id__in=soldier_ids_to_update)
        
        soldier_instances = {soldier.id: soldier for soldier in existing_soldiers}

        updated_instances = []
        with transaction.atomic(): 
            for item_data in serializer.validated_data:
                soldier_id = item_data.get('id')
                if soldier_id and soldier_id in soldier_instances:
                    instance = soldier_instances[soldier_id]
                    updated_instance = self.serializer_class.update(instance, item_data) 
                    updated_instances.append(updated_instance)
                else:
                    pass 
        
        return Response(self.get_serializer(updated_instances, many=True).data, status=status.HTTP_200_OK)


class AssignmentViewSet(viewsets.ModelViewSet):
    queryset = Assignment.objects.all()
    serializer_class = AssignmentSerializer
    filterset_fields = ['soldier', 'scheduling_run', 'assignment_date', 'is_on_base']
    search_fields = ['soldier__name', 'assignment_date']


class SchedulingRunViewSet(viewsets.ModelViewSet):
    queryset = SchedulingRun.objects.all()
    serializer_class = SchedulingRunSerializer
    
    def get_serializer_class(self):
        if self.action == 'run_scheduling_new': 
            return ScheduleCreateSerializer
        elif self.action == 'update_existing_scheduling_run': 
            return ScheduleUpdateSerializer
        return SchedulingRunSerializer 

    @action(detail=False, methods=['post'], url_path='run_scheduling_new')
    def run_scheduling_new(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return self._handle_scheduling_run(request, serializer.validated_data, create_new=True)

    @action(detail=False, methods=['post'], url_path='update_existing_scheduling_run')
    def update_existing_scheduling_run(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return self._handle_scheduling_run(request, serializer.validated_data, create_new=False)

    def _analyze_problem_complexity(self, algorithm_soldiers: List[AlgorithmSoldier], 
                                   start_date: date, end_date: date, 
                                   min_required_soldiers: int) -> dict:
        """Analyzes problem complexity and returns parameter recommendations"""
        total_days = (end_date - start_date).days + 1
        required_total = total_days * min_required_soldiers
        
        total_available = 0
        exceptional_soldiers = 0
        weekend_soldiers = 0
        heavily_constrained = 0
        
        print(f"🔍 Analyzing problem: {len(algorithm_soldiers)} soldiers, {total_days} days")
        
        for soldier in algorithm_soldiers:
            available_days = total_days - len(soldier.raw_constraints)
            total_available += available_days
            constraints_ratio = len(soldier.raw_constraints) / total_days
            
            if soldier.is_exceptional_output:
                exceptional_soldiers += 1
            if soldier.is_weekend_only_soldier_flag:
                weekend_soldiers += 1
            if constraints_ratio > 0.4:
                heavily_constrained += 1
                print(f"⚠️ Heavily constrained soldier: {soldier.name} - {constraints_ratio:.1%} constraints")
        
        availability_ratio = total_available / required_total if required_total > 0 else 1.0
        
        # Determine difficulty level
        if heavily_constrained >= 3 or availability_ratio < 1.1:
            difficulty = "APOCALYPTIC"
        elif heavily_constrained >= 2 or availability_ratio < 1.3:
            difficulty = "EXTREME"
        elif heavily_constrained >= 1 or availability_ratio < 1.5:
            difficulty = "HARD"
        else:
            difficulty = "MEDIUM"
        
        analysis = {
            'total_days': total_days,
            'total_soldiers': len(algorithm_soldiers),
            'required_total': required_total,
            'total_available': total_available,
            'availability_ratio': availability_ratio,
            'exceptional_soldiers': exceptional_soldiers,
            'weekend_soldiers': weekend_soldiers,
            'heavily_constrained': heavily_constrained,
            'difficulty': difficulty
        }
        
        print(f"📊 Problem Analysis:")
        print(f"    🎯 Total requirement: {required_total} work days")
        print(f"    ✅ Total availability: {total_available} days")
        print(f"    📈 Availability ratio: {availability_ratio:.2f}")
        print(f"    ⚠️ Exceptional soldiers: {exceptional_soldiers}")
        print(f"    🏖️ Weekend soldiers: {weekend_soldiers}")
        print(f"    💀 Heavily constrained soldiers: {heavily_constrained}")
        print(f"    🔥 Difficulty level: {difficulty}")
        
        return analysis

    def _get_adaptive_parameters(self, analysis: dict, original_params: dict) -> dict:
        """Returns parameters adapted to the difficulty level"""
        difficulty = analysis['difficulty']
        params = original_params.copy()
        
        if difficulty == "APOCALYPTIC":
            print("💀 Apocalyptic situation - extreme parameters")
            params.update({
                'flexible_daily_requirement': True,
                'penalty_one_day_block': 50_000_000,
                'penalty_shortage': 5_000_000,
                'penalty_no_work': 20_000_000,
                'penalty_long_block': 200_000,
                'critical_penalty_long_block': 10_000_000
            })
        elif difficulty == "EXTREME":
            print("🔥 Extreme situation - strict parameters")
            params.update({
                'flexible_daily_requirement': True,
                'penalty_one_day_block': 30_000_000,
                'penalty_shortage': 3_000_000,
                'penalty_no_work': 15_000_000,
                'penalty_long_block': 150_000,
                'critical_penalty_long_block': 7_000_000
            })
        elif difficulty == "HARD":
            print("⚠️ Hard situation - increased parameters")
            params.update({
                'flexible_daily_requirement': True,
                'penalty_one_day_block': 20_000_000,
                'penalty_shortage': 2_000_000,
                'penalty_no_work': 10_000_000,
                'penalty_long_block': 100_000,
                'critical_penalty_long_block': 5_000_000
            })
        else:
            print("🟢 Medium situation - normal parameters")
            params.update({
                'flexible_daily_requirement': True,
                'penalty_one_day_block': 10_000_000,
                'penalty_shortage': 1_000_000,
                'penalty_no_work': 5_000_000,
                'penalty_long_block': 50_000,
                'critical_penalty_long_block': 2_000_000
            })
        
        return params

    def _handle_scheduling_run(self, request, validated_data, create_new=True):
        
        scheduling_run_id = validated_data.get('scheduling_run_id') 
        scheduling_run = None

        if create_new or not scheduling_run_id:
            scheduling_run = SchedulingRun.objects.create(
                start_date=validated_data['start_date'],
                end_date=validated_data['end_date'],
                default_base_days_target=validated_data['default_base_days_target'],
                default_home_days_target=validated_data['default_home_days_target'],
                max_consecutive_base_days=validated_data['max_consecutive_base_days'],
                max_consecutive_home_days=validated_data['max_consecutive_home_days'],
                min_base_block_days=validated_data['min_base_block_days'],
                min_required_soldiers_per_day=validated_data.get('min_required_soldiers_per_day'),
                max_total_home_days=validated_data.get('max_total_home_days'),
                max_weekend_base_days_per_soldier=validated_data.get('max_weekend_base_days_per_soldier'), 
                status='IN_PROGRESS'
            )
        else:
            try:
                scheduling_run = SchedulingRun.objects.get(id=scheduling_run_id)
                scheduling_run.start_date = validated_data.get('start_date', scheduling_run.start_date)
                scheduling_run.end_date = validated_data.get('end_date', scheduling_run.end_date)
                scheduling_run.default_base_days_target = validated_data.get('default_base_days_target', scheduling_run.default_base_days_target)
                scheduling_run.default_home_days_target = validated_data.get('default_home_days_target', scheduling_run.default_home_days_target)
                scheduling_run.max_consecutive_base_days = validated_data.get('max_consecutive_base_days', scheduling_run.max_consecutive_base_days)
                scheduling_run.max_consecutive_home_days = validated_data.get('max_consecutive_home_days', scheduling_run.max_consecutive_home_days)
                scheduling_run.min_base_block_days = validated_data.get('min_base_block_days', scheduling_run.min_base_block_days)
                scheduling_run.min_required_soldiers_per_day = validated_data.get('min_required_soldiers_per_day', scheduling_run.min_required_soldiers_per_day)
                scheduling_run.max_total_home_days = validated_data.get('max_total_home_days', scheduling_run.max_total_home_days)
                scheduling_run.max_weekend_base_days_per_soldier = validated_data.get('max_weekend_base_days_per_soldier', scheduling_run.max_weekend_base_days_per_soldier) 

                scheduling_run.status = 'IN_PROGRESS'
                scheduling_run.solution_details = ""
                scheduling_run.save()
                
                start_date_to_clear = validated_data.get('start_date', scheduling_run.start_date)
                end_date_to_clear = validated_data.get('end_date', scheduling_run.end_date)

                Assignment.objects.filter(
                    scheduling_run=scheduling_run, 
                    assignment_date__gte=start_date_to_clear, 
                    assignment_date__lte=end_date_to_clear
                ).delete()

            except SchedulingRun.DoesNotExist:
                return Response({"detail": f"SchedulingRun with ID {scheduling_run_id} not found."}, status=status.HTTP_404_NOT_FOUND)

        start_date = scheduling_run.start_date
        end_date = scheduling_run.end_date
        
        try:
            print(f"🚀 Starting advanced scheduling V9.0")
            print(f"📅 Range: {start_date} - {end_date}")
            
            # Preparing soldiers
            all_soldiers = Soldier.objects.all()
            algorithm_soldiers: List[AlgorithmSoldier] = []
            soldier_map = {s_model.id: s_model for s_model in all_soldiers}

            for s_model in all_soldiers:
                soldier_constraints_dates = s_model.constraints.filter(
                    constraint_date__gte=start_date,
                    constraint_date__lte=end_date
                ).values_list('constraint_date', flat=True)

                algo_soldier = AlgorithmSoldier(
                    id=str(s_model.id), 
                    name=s_model.name,
                    unavailable_days=[d.isoformat() for d in soldier_constraints_dates],
                    is_exceptional_output=getattr(s_model, 'is_exceptional_output', False),
                    is_weekend_only_soldier_flag=getattr(s_model, 'is_weekend_only_soldier_flag', False),
                    color=getattr(s_model, 'color', None)
                )
                algorithm_soldiers.append(algo_soldier)

            # Analyzing problem complexity
            analysis = self._analyze_problem_complexity(
                algorithm_soldiers, start_date, end_date, 
                scheduling_run.min_required_soldiers_per_day
            )

            # Getting adaptive parameters
            original_params = {
                'default_base_days_target': scheduling_run.default_base_days_target,
                'default_home_days_target': scheduling_run.default_home_days_target,
                'max_consecutive_base_days': scheduling_run.max_consecutive_base_days,
                'max_consecutive_home_days': scheduling_run.max_consecutive_home_days,
                'min_base_block_days': scheduling_run.min_base_block_days,
                'min_required_soldiers_per_day': scheduling_run.min_required_soldiers_per_day,
                'max_total_home_days': scheduling_run.max_total_home_days,
                'max_weekend_base_days_per_soldier': scheduling_run.max_weekend_base_days_per_soldier,
            }
            
            adaptive_params = self._get_adaptive_parameters(analysis, original_params)

            with transaction.atomic():
                print("🔧 Creating advanced solver...")
                
                # Handling soldiers with problematic names
                print("🔍 Checking soldier names...")
                for soldier in algorithm_soldiers:
                    if not soldier.name or not soldier.name.strip():
                        print(f"⚠️ Soldier with empty name found: {soldier}")
                        soldier.name = f"Soldier_{soldier.id}"
                    
                    # Clean soldier name from special characters
                    original_name = soldier.name
                    soldier.name = soldier.name.replace('"', '').replace("'", '').strip()
                    if original_name != soldier.name:
                        print(f"🔧 Soldier name fixed: '{original_name}' -> '{soldier.name}'")
                
                scheduler = None
                scheduler_created = False
                
                try:
                    scheduler = SmartScheduleSoldiers(
                        soldiers=algorithm_soldiers,
                        start_date=start_date,
                        end_date=end_date,
                        default_base_days_target=scheduling_run.default_base_days_target,
                        default_home_days_target=scheduling_run.default_home_days_target,
                        max_consecutive_base_days=scheduling_run.max_consecutive_base_days,
                        max_consecutive_home_days=scheduling_run.max_consecutive_home_days,
                        min_base_block_days=scheduling_run.min_base_block_days,
                        min_required_soldiers_per_day=scheduling_run.min_required_soldiers_per_day,
                        max_total_home_days=scheduling_run.max_total_home_days,
                        max_weekend_base_days_per_soldier=scheduling_run.max_weekend_base_days_per_soldier,
                        
                        # Parameters adapted to the problem
                        flexible_daily_requirement=adaptive_params.get('flexible_daily_requirement', True),
                        penalty_one_day_block=adaptive_params.get('penalty_one_day_block', 20_000_000),
                        penalty_shortage=adaptive_params.get('penalty_shortage', 2_000_000),
                        penalty_no_work=adaptive_params.get('penalty_no_work', 10_000_000),
                        penalty_long_block=adaptive_params.get('penalty_long_block', 100_000),
                        critical_penalty_long_block=adaptive_params.get('critical_penalty_long_block', 5_000_000)
                    )
                    
                    print("✅ Solver created successfully")
                    scheduler_created = True
                    
                except Exception as create_error:
                    print(f"❌ Error creating solver: {create_error}")
                    traceback.print_exc()
                    scheduler_created = False
                
                if not scheduler_created or scheduler is None:
                    scheduling_run.status = 'CREATION_ERROR'
                    scheduling_run.solution_details = (
                        f"❌ Error creating solver\n"
                        f"🔥 Difficulty level: {analysis['difficulty']}\n"
                        f"📊 Availability ratio: {analysis['availability_ratio']:.2f}\n"
                        f"💡 There is a problem creating the solver - check the modules"
                    )
                    scheduling_run.save()
                    return Response(
                        {"detail": "Error creating solver"}, 
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
                
                # Adding solver settings before running
                if scheduler and scheduler.solver:
                    scheduler.solver.parameters.max_time_in_seconds = 300  # 5 minutes maximum
                    print("⚙️ Solver configured with a maximum time of 300 seconds")
                
                print("🔄 Running algorithm...")
                
                # משתנים לטיפול בתוצאות - הגדרה מראש
                solution_data = None
                solver_status = None
                solve_successful = False
                status_name = "UNKNOWN"
                wall_time = 0.0
                objective_value = "N/A"
                
                # הרצת הפתרון עם הגנה מפני שגיאות
                try:
                    solution_data, solver_status = scheduler.solve()
                    solve_successful = True
                    print("🎯 פתרון הושלם בהצלחה")
                    
                except Exception as solve_error:
                    print(f"❌ שגיאה בהרצת הפותר: {solve_error}")
                    traceback.print_exc()
                    solve_successful = False
                
                # קבלת תוצאות רק אם הפתרון הצליח ויש solver
                if solve_successful and scheduler and hasattr(scheduler, 'solver'):
                    try:
                        # בדיקה אם solver.Solve() נקרא בהצלחה
                        if solver_status is not None:
                            status_name = scheduler.solver.StatusName(solver_status)
                            
                            # קבלת WallTime רק אם הפתרון רץ
                            try:
                                wall_time = scheduler.solver.WallTime()
                            except RuntimeError as wall_time_error:
                                print(f"⚠️ לא ניתן לקבל זמן פתרון: {wall_time_error}")
                                wall_time = 0.0
                            
                            # קבלת ObjectiveValue רק אם יש פתרון תקין
                            if solution_data and (solver_status == cp_model.OPTIMAL or solver_status == cp_model.FEASIBLE):
                                try:
                                    objective_value = scheduler.solver.ObjectiveValue()
                                except Exception as obj_error:
                                    print(f"⚠️ לא ניתן לקבל ערך מטרה: {obj_error}")
                                    objective_value = "N/A"
                        else:
                            status_name = "FAILED_TO_GET_STATUS"
                            
                    except Exception as results_error:
                        print(f"⚠️ שגיאה בקבלת תוצאות פותר: {results_error}")
                        status_name = "ERROR_GETTING_RESULTS"
                        wall_time = 0.0
                        objective_value = "N/A"
                else:
                    if not solve_successful:
                        status_name = "SOLVE_FAILED"
                    elif not scheduler:
                        status_name = "NO_SCHEDULER"
                    else:
                        status_name = "NO_SOLVER_ATTRIBUTE"
                    print(f"🚨 לא ניתן לקבל תוצאות פותר: {status_name}")

                print(f"🎯 Solution status: {status_name}")
                print(f"⏱️ Solution time: {wall_time:.2f} seconds")
                print(f"💰 Solution cost: {objective_value}")

                if solution_data and solve_successful:
                    print("✅ Advanced solution found!")
                    
                    # Processing the solution
                    presence_map = {}
                    current_date = start_date
                    while current_date <= end_date:
                        date_iso = current_date.isoformat()
                        soldiers_on_base_today = []
                        for soldier_name, data in solution_data.items():
                            if soldier_name == 'daily_soldiers_count':
                                continue
                            for day_schedule in data['schedule']:
                                if day_schedule['date'] == date_iso and day_schedule['status'] == 'בסיס':
                                    soldiers_on_base_today.append(soldier_name)
                                    break
                        presence_map[current_date] = soldiers_on_base_today
                        current_date += timedelta(days=1)
                    
                    # Saving results to the database
                    print("💾 Saving results...")
                    current_date = start_date
                    assignments_created = 0
                    while current_date <= end_date:
                        soldiers_on_base_for_day = presence_map.get(current_date, [])
                        for algo_soldier in algorithm_soldiers:
                            django_soldier_obj = soldier_map.get(int(algo_soldier.id))
                            if django_soldier_obj:
                                is_on_base = algo_soldier.name in soldiers_on_base_for_day
                                Assignment.objects.create(
                                    scheduling_run=scheduling_run,
                                    soldier=django_soldier_obj,
                                    assignment_date=current_date,
                                    is_on_base=is_on_base
                                )
                                assignments_created += 1
                        current_date += timedelta(days=1)
                    
                    print(f"✅ {assignments_created} assignments created")
                    
                    # Update success status
                    if status_name == 'OPTIMAL':
                        scheduling_run.status = 'SUCCESS'
                    elif status_name == 'FEASIBLE':
                        scheduling_run.status = 'FEASIBLE'
                    else:
                        scheduling_run.status = 'SUCCESS'  # Any working solution is a success
                        
                    scheduling_run.solution_details = (
                        f"✅ Solution found successfully!\n"
                        f"🎯 Status: {status_name}\n"
                        f"⏱️ Solution time: {wall_time:.2f} seconds\n"
                        f"💰 Cost: {objective_value}\n"
                        f"🔥 Difficulty level: {analysis['difficulty']}\n"
                        f"📊 Availability ratio: {analysis['availability_ratio']:.2f}\n"
                        f"💾 {assignments_created} assignments created"
                    )
                else:
                    print("❌ No solution found")
                    
                    if not solve_successful:
                        scheduling_run.status = 'SOLVER_ERROR'
                        scheduling_run.solution_details = (
                            f"❌ Error running the algorithm\n"
                            f"🔥 Difficulty level: {analysis['difficulty']}\n"
                            f"📊 Availability ratio: {analysis['availability_ratio']:.2f}\n"
                            f"💡 There is a problem with the algorithm or data structure"
                        )
                    else:
                        scheduling_run.status = 'NO_SOLUTION'
                        scheduling_run.solution_details = (
                            f"❌ Algorithm found no solution\n"
                            f"🎯 Status: {status_name}\n"
                            f"⏱️ Attempt time: {wall_time:.2f} seconds\n"
                            f"🔥 Difficulty level: {analysis['difficulty']}\n"
                            f"📊 Availability ratio: {analysis['availability_ratio']:.2f}\n"
                            f"💡 The problem is too extreme - try softening parameters or reducing constraints"
                        )
                
                scheduling_run.save()

            # Return results
            response_data = SchedulingRunSerializer(scheduling_run).data 
            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            print(f"❌ General algorithm error: {e}")
            traceback.print_exc()
            
            if scheduling_run:
                scheduling_run.status = 'FAILURE'
                scheduling_run.solution_details = (
                    f"❌ Critical general error during scheduling\n"
                    f"🐛 Error: {str(e)}\n"
                    f"📋 Details: {traceback.format_exc()[-500:]}"  # Only last 500 characters
                )
                scheduling_run.save()
            
            return Response(
                {"detail": f"Error during scheduling: {e}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'], url_path='detailed_schedule')
    def get_detailed_schedule(self, request, pk=None):
        try:
            scheduling_run = self.get_object()
        except SchedulingRun.DoesNotExist:
            return Response({"detail": "Scheduling run not found."}, status=status.HTTP_404_NOT_FOUND)

        assignments = Assignment.objects.filter(scheduling_run=scheduling_run).order_by('assignment_date', 'soldier__name')

        detailed_schedule = {}
        for assignment in assignments:
            date_str = assignment.assignment_date.strftime('%Y-%m-%d')
            if date_str not in detailed_schedule:
                detailed_schedule[date_str] = {
                    'date': date_str,
                    'soldiers_on_base': [],
                    'soldiers_at_home': []
                }
            
            soldier_name = assignment.soldier.name
            if assignment.is_on_base:
                detailed_schedule[date_str]['soldiers_on_base'].append(soldier_name)
            else:
                detailed_schedule[date_str]['soldiers_at_home'].append(soldier_name)
        
        sorted_schedule_list = sorted(detailed_schedule.values(), key=lambda x: x['date'])

        return Response(sorted_schedule_list, status=status.HTTP_200_OK)


class EventViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows managing events in the system.
    """
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    filterset_fields = ['event_type', 'start_date', 'end_date'] 
    search_fields = ['name', 'description', 'soldier_constraint__soldier__name']