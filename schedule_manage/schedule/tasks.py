# schedule/tasks.py
# Celery tasks for asynchronous processing

from celery import shared_task
from typing import List
from datetime import date, timedelta
from django.db import transaction
import traceback
import logging
from ortools.sat.python import cp_model

from .models import Soldier, SoldierConstraint, SchedulingRun, Assignment
from .algorithms import SmartScheduleSoldiers
from .algorithms.soldier import Soldier as AlgorithmSoldier

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def run_scheduling_algorithm_async(self, scheduling_run_id: int):
    """
    Asynchronous task for running the scheduling algorithm
    
    Args:
        scheduling_run_id (int): ID of the SchedulingRun to process
        
    Returns:
        dict: Result of the scheduling operation
    """
    try:
        logger.info(f"Starting async scheduling task for run {scheduling_run_id}")
        
        # Get the scheduling run
        scheduling_run = SchedulingRun.objects.get(id=scheduling_run_id)
        scheduling_run.status = 'IN_PROGRESS'
        scheduling_run.save()
        
        start_date = scheduling_run.start_date
        end_date = scheduling_run.end_date
        
        # Prepare soldiers with optimized queries
        all_soldiers = Soldier.objects.prefetch_related('constraints').all()
        algorithm_soldiers: List[AlgorithmSoldier] = []
        soldier_map = {s_model.id: s_model for s_model in all_soldiers}

        for s_model in all_soldiers:
            soldier_constraints_dates = [
                constraint.constraint_date 
                for constraint in s_model.constraints.all()
                if start_date <= constraint.constraint_date <= end_date
            ]

            algo_soldier = AlgorithmSoldier(
                id=str(s_model.id), 
                name=s_model.name,
                unavailable_days=[d.isoformat() for d in soldier_constraints_dates],
                is_exceptional_output=getattr(s_model, 'is_exceptional_output', False),
                is_weekend_only_soldier_flag=getattr(s_model, 'is_weekend_only_soldier_flag', False),
                color=getattr(s_model, 'color', None)
            )
            algorithm_soldiers.append(algo_soldier)

        # Analyze problem complexity
        analysis = _analyze_problem_complexity_async(
            algorithm_soldiers, start_date, end_date, 
            scheduling_run.min_required_soldiers_per_day
        )

        # Get adaptive parameters
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
        
        adaptive_params = _get_adaptive_parameters_async(analysis, original_params)

        with transaction.atomic():
            logger.info("Creating scheduler...")
            
            # Clean soldier names
            for soldier in algorithm_soldiers:
                if not soldier.name or not soldier.name.strip():
                    soldier.name = f"Soldier_{soldier.id}"
                
                original_name = soldier.name
                soldier.name = soldier.name.replace('"', '').replace("'", '').strip()
                if original_name != soldier.name:
                    logger.info(f"Soldier name cleaned: '{original_name}' -> '{soldier.name}'")
            
            # Create scheduler
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
                
                # Adaptive parameters
                flexible_daily_requirement=adaptive_params.get('flexible_daily_requirement', True),
                penalty_one_day_block=adaptive_params.get('penalty_one_day_block', 20_000_000),
                penalty_shortage=adaptive_params.get('penalty_shortage', 2_000_000),
                penalty_no_work=adaptive_params.get('penalty_no_work', 10_000_000),
                penalty_long_block=adaptive_params.get('penalty_long_block', 100_000),
                critical_penalty_long_block=adaptive_params.get('critical_penalty_long_block', 5_000_000)
            )
            
            # Configure solver
            if scheduler and scheduler.solver:
                scheduler.solver.parameters.max_time_in_seconds = 600  # 10 minutes for async
            
            logger.info("Running algorithm...")
            solution_data, solver_status = scheduler.solve()
            
            # Process results
            if solution_data and solver_status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
                logger.info("Solution found! Processing results...")
                
                # Save assignments
                assignments_created = _save_assignments_async(
                    solution_data, scheduling_run, algorithm_soldiers, 
                    soldier_map, start_date, end_date
                )
                
                # Export results
                try:
                    scheduler.export_to_excel(solution_data, "schedule.xlsx")
                    scheduler.export_to_json(solution_data, "schedule.json")
                except Exception as export_error:
                    logger.error(f"Export error: {export_error}")
                
                # Update success status
                status_name = scheduler.solver.StatusName(solver_status)
                wall_time = scheduler.solver.WallTime()
                objective_value = scheduler.solver.ObjectiveValue()
                
                scheduling_run.status = 'SUCCESS'
                scheduling_run.solution_details = (
                    f"✅ Solution found successfully!\n"
                    f"🎯 Status: {status_name}\n"
                    f"⏱️ Solution time: {wall_time:.2f} seconds\n"
                    f"💰 Cost: {objective_value}\n"
                    f"🔥 Difficulty level: {analysis['difficulty']}\n"
                    f"📊 Availability ratio: {analysis['availability_ratio']:.2f}\n"
                    f"💾 {assignments_created} assignments created"
                )
                
                return {
                    'success': True,
                    'status': status_name,
                    'assignments_created': assignments_created,
                    'analysis': analysis
                }
            else:
                logger.error("No solution found")
                scheduling_run.status = 'NO_SOLUTION'
                scheduling_run.solution_details = (
                    f"❌ Algorithm found no solution\n"
                    f"🔥 Difficulty level: {analysis['difficulty']}\n"
                    f"📊 Availability ratio: {analysis['availability_ratio']:.2f}\n"
                    f"💡 Problem too complex - try relaxing constraints"
                )
                
                return {
                    'success': False,
                    'error': 'No solution found',
                    'analysis': analysis
                }
                
    except Exception as exc:
        logger.error(f"Scheduling task failed: {exc}")
        logger.error(traceback.format_exc())
        
        try:
            scheduling_run = SchedulingRun.objects.get(id=scheduling_run_id)
            scheduling_run.status = 'FAILURE'
            scheduling_run.solution_details = f"❌ Task failed: {str(exc)}"
            scheduling_run.save()
        except:
            pass
        
        # Retry mechanism
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying task, attempt {self.request.retries + 1}")
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        
        return {
            'success': False,
            'error': str(exc),
            'retries_exhausted': True
        }
    
    finally:
        try:
            scheduling_run.save()
        except:
            pass


def _analyze_problem_complexity_async(algorithm_soldiers: List[AlgorithmSoldier], 
                                    start_date: date, end_date: date, 
                                    min_required_soldiers: int) -> dict:
    """Analyze problem complexity for async processing"""
    total_days = (end_date - start_date).days + 1
    required_total = total_days * min_required_soldiers
    
    total_available = 0
    exceptional_soldiers = 0
    weekend_soldiers = 0
    heavily_constrained = 0
    
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
    
    return {
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


def _get_adaptive_parameters_async(analysis: dict, original_params: dict) -> dict:
    """Get parameters adapted to difficulty level"""
    difficulty = analysis['difficulty']
    params = original_params.copy()
    
    if difficulty == "APOCALYPTIC":
        params.update({
            'flexible_daily_requirement': True,
            'penalty_one_day_block': 50_000_000,
            'penalty_shortage': 5_000_000,
            'penalty_no_work': 20_000_000,
            'penalty_long_block': 200_000,
            'critical_penalty_long_block': 10_000_000
        })
    elif difficulty == "EXTREME":
        params.update({
            'flexible_daily_requirement': True,
            'penalty_one_day_block': 30_000_000,
            'penalty_shortage': 3_000_000,
            'penalty_no_work': 15_000_000,
            'penalty_long_block': 150_000,
            'critical_penalty_long_block': 7_000_000
        })
    elif difficulty == "HARD":
        params.update({
            'flexible_daily_requirement': True,
            'penalty_one_day_block': 20_000_000,
            'penalty_shortage': 2_000_000,
            'penalty_no_work': 10_000_000,
            'penalty_long_block': 100_000,
            'critical_penalty_long_block': 5_000_000
        })
    else:
        params.update({
            'flexible_daily_requirement': True,
            'penalty_one_day_block': 10_000_000,
            'penalty_shortage': 1_000_000,
            'penalty_no_work': 5_000_000,
            'penalty_long_block': 50_000,
            'critical_penalty_long_block': 2_000_000
        })
    
    return params


def _save_assignments_async(solution_data: dict, scheduling_run: SchedulingRun,
                          algorithm_soldiers: List[AlgorithmSoldier], soldier_map: dict,
                          start_date: date, end_date: date) -> int:
    """Save assignments to database efficiently"""
    assignments_to_create = []
    current_date = start_date
    
    # Build presence map
    presence_map = {}
    while current_date <= end_date:
        date_iso = current_date.isoformat()
        soldiers_on_base_today = []
        
        for soldier_name, data in solution_data.items():
            if soldier_name == 'daily_soldiers_count':
                continue
            for day_schedule in data['schedule']:
                if day_schedule['date'] == date_iso and day_schedule['status'] == 'Base':
                    soldiers_on_base_today.append(soldier_name)
                    break
        
        presence_map[current_date] = soldiers_on_base_today
        current_date += timedelta(days=1)
    
    # Create assignments in batch
    current_date = start_date
    while current_date <= end_date:
        soldiers_on_base_for_day = presence_map.get(current_date, [])
        
        for algo_soldier in algorithm_soldiers:
            django_soldier_obj = soldier_map.get(int(algo_soldier.id))
            if django_soldier_obj:
                is_on_base = algo_soldier.name in soldiers_on_base_for_day
                assignments_to_create.append(
                    Assignment(
                        scheduling_run=scheduling_run,
                        soldier=django_soldier_obj,
                        assignment_date=current_date,
                        is_on_base=is_on_base
                    )
                )
        current_date += timedelta(days=1)
    
    # Bulk create for better performance
    Assignment.objects.bulk_create(assignments_to_create, batch_size=1000)
    return len(assignments_to_create)


@shared_task
def cleanup_old_assignments(days_old: int = 30):
    """Clean up old assignments to keep database size manageable"""
    cutoff_date = date.today() - timedelta(days=days_old)
    
    old_runs = SchedulingRun.objects.filter(run_date__date__lt=cutoff_date)
    deleted_count = 0
    
    for run in old_runs:
        assignment_count = run.assignments.count()
        run.delete()
        deleted_count += assignment_count
    
    logger.info(f"Cleaned up {deleted_count} old assignments")
    return {'deleted_assignments': deleted_count, 'cutoff_date': cutoff_date.isoformat()}


@shared_task
def validate_schedule_consistency():
    """Validate that all schedules are consistent and report issues"""
    issues = []
    
    # Check for duplicate assignments
    duplicates = Assignment.objects.values(
        'scheduling_run', 'soldier', 'assignment_date'
    ).annotate(count=models.Count('id')).filter(count__gt=1)
    
    if duplicates:
        issues.append(f"Found {len(duplicates)} duplicate assignments")
    
    # Check for soldiers with impossible schedules
    # (This would be expanded based on business rules)
    
    return {'issues': issues, 'status': 'completed'}