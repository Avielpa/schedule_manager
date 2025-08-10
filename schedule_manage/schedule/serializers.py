# schedule/serializers.py
# Simplified serializers for Event -> Schedule -> Soldiers flow

from rest_framework import serializers
from datetime import date

from .models import Event, Soldier, SoldierConstraint, SchedulingRun, Assignment


# =============================================================================
# SOLDIER SERIALIZERS
# =============================================================================

class SoldierConstraintSerializer(serializers.ModelSerializer):
    """Serializer for soldier constraints"""
    soldier_name = serializers.CharField(source='soldier.name', read_only=True)
    
    class Meta:
        model = SoldierConstraint
        fields = [
            'id', 'soldier', 'soldier_name', 'constraint_date', 'description',
            'constraint_type', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'soldier_name']


class SoldierListSerializer(serializers.ModelSerializer):
    """Simplified soldier serializer for lists"""
    event_name = serializers.CharField(source='event.name', read_only=True)
    constraints_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Soldier
        fields = [
            'id', 'event', 'event_name', 'name', 'soldier_id', 'rank', 'constraints_count', 'is_exceptional_output',
            'is_weekend_only_soldier_flag'
        ]
    
    def get_constraints_count(self, obj):
        return obj.constraints.count()


class SoldierDetailSerializer(serializers.ModelSerializer):
    """Detailed soldier serializer with JSON POST support"""
    event_name = serializers.CharField(source='event.name', read_only=True)
    event_id = serializers.IntegerField(write_only=True)
    constraints = SoldierConstraintSerializer(many=True, read_only=True)
    constraints_data = serializers.ListField(
        child=serializers.DictField(), 
        write_only=True, 
        required=False,
        help_text="List of constraints to create with soldier"
    )
    
    class Meta:
        model = Soldier
        fields = [
            'id', 'event', 'event_name', 'event_id', 'name', 'soldier_id', 'rank', 'is_exceptional_output', 'is_weekend_only_soldier_flag',
            'constraints', 'constraints_data', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
        
    def validate_event_id(self, value):
        """Validate event exists"""
        try:
            Event.objects.get(id=value)
        except Event.DoesNotExist:
            raise serializers.ValidationError("Event with this ID does not exist")
        return value
    
    def validate(self, data):
        """Validate soldier_id uniqueness within event"""
        soldier_id = data.get('soldier_id')
        event_id = data.get('event_id')
        
        if soldier_id and event_id:
            # Check if soldier_id already exists for this event
            if Soldier.objects.filter(soldier_id=soldier_id, event_id=event_id).exists():
                raise serializers.ValidationError({"soldier_id": "Soldier with this ID already exists in this event"})
        
        return data
    
    def create(self, validated_data):
        """Create soldier with optional constraints"""
        constraints_data = validated_data.pop('constraints_data', [])
        soldier = Soldier.objects.create(**validated_data)
        
        # Create constraints if provided
        for constraint_data in constraints_data:
            constraint_serializer = SoldierConstraintSerializer(data={
                **constraint_data,
                'soldier': soldier.id
            })
            if constraint_serializer.is_valid():
                constraint_serializer.save()
        
        return soldier


# For backward compatibility
SoldierSerializer = SoldierListSerializer


# =============================================================================
# EVENT SERIALIZERS
# =============================================================================

class EventSerializer(serializers.ModelSerializer):
    """Serializer for events with comprehensive JSON POST support"""
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = Event
        fields = [
            'id', 'name', 'event_type', 'description', 'start_date', 'end_date',
            'min_required_soldiers_per_day', 'base_days_per_soldier', 'home_days_per_soldier',
            'max_consecutive_base_days', 'max_consecutive_home_days', 'min_base_block_days',
            'created_by', 'created_by_username', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'created_by_username']
        
    def validate(self, data):
        """Validate event data"""
        if data['start_date'] >= data['end_date']:
            raise serializers.ValidationError("End date must be after start date")
        
        if data.get('min_required_soldiers_per_day', 1) < 1:
            raise serializers.ValidationError("Minimum required soldiers must be at least 1")
            
        return data
    
    def create(self, validated_data):
        """Create event with automatic created_by assignment"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['created_by'] = request.user
        return super().create(validated_data)


# =============================================================================
# SCHEDULING RUN SERIALIZERS
# =============================================================================

class SchedulingRunListSerializer(serializers.ModelSerializer):
    """Simplified scheduling run serializer for lists"""
    event_name = serializers.CharField(source='event.name', read_only=True)
    soldiers_count = serializers.SerializerMethodField()
    assignments_count = serializers.SerializerMethodField()
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = SchedulingRun
        fields = [
            'id', 'name', 'event', 'event_name', 'status', 'soldiers_count', 'assignments_count',
            'created_by_username', 'created_at'
        ]
    
    def get_soldiers_count(self, obj):
        return obj.soldiers.count()
    
    def get_assignments_count(self, obj):
        return obj.assignments.count()


class SchedulingRunDetailSerializer(serializers.ModelSerializer):
    """Detailed scheduling run serializer with enhanced JSON POST support"""
    event_name = serializers.CharField(source='event.name', read_only=True)
    event_id = serializers.IntegerField(write_only=True)
    soldiers = SoldierListSerializer(many=True, read_only=True)
    soldiers_ids = serializers.ListField(
        child=serializers.IntegerField(), 
        write_only=True, 
        required=False,
        help_text="List of soldier IDs to include in this scheduling run"
    )
    soldiers_count = serializers.SerializerMethodField()
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = SchedulingRun
        fields = [
            'id', 'name', 'description', 'event', 'event_name', 'event_id', 'soldiers', 'soldiers_ids',
            'soldiers_count', 'status', 'solution_details', 'processing_time_seconds', 
            'created_by', 'created_by_username', 'created_at'
        ]
        read_only_fields = [
            'id', 'created_at', 'status', 'solution_details', 'processing_time_seconds', 
            'soldiers_count', 'created_by_username'
        ]
        
    def validate_event_id(self, value):
        """Validate event exists"""
        try:
            Event.objects.get(id=value)
        except Event.DoesNotExist:
            raise serializers.ValidationError("Event with this ID does not exist")
        return value
    
    def validate_soldiers_ids(self, value):
        """Validate all soldier IDs exist"""
        if value:
            existing_ids = set(Soldier.objects.filter(id__in=value).values_list('id', flat=True))
            invalid_ids = set(value) - existing_ids
            if invalid_ids:
                raise serializers.ValidationError(f"Soldiers with IDs {list(invalid_ids)} do not exist")
        return value
    
    def get_soldiers_count(self, obj):
        return obj.soldiers.count()
    
    def create(self, validated_data):
        """Create scheduling run with automatic created_by assignment"""
        soldiers_ids = validated_data.pop('soldiers_ids', [])
        
        # Set created_by if user is authenticated
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['created_by'] = request.user
            
        scheduling_run = SchedulingRun.objects.create(**validated_data)
        
        if soldiers_ids:
            scheduling_run.soldiers.set(soldiers_ids)
        
        return scheduling_run
    
    def update(self, instance, validated_data):
        """Update scheduling run with soldiers management"""
        soldiers_ids = validated_data.pop('soldiers_ids', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        if soldiers_ids is not None:
            instance.soldiers.set(soldiers_ids)
        
        return instance


# For backward compatibility
SchedulingRunSerializer = SchedulingRunListSerializer


# =============================================================================
# ASSIGNMENT SERIALIZERS
# =============================================================================

class AssignmentSerializer(serializers.ModelSerializer):
    """Serializer for assignments"""
    soldier = SoldierListSerializer(read_only=True)
    soldier_id = serializers.IntegerField(write_only=True)
    scheduling_run_name = serializers.CharField(source='scheduling_run.name', read_only=True)
    
    class Meta:
        model = Assignment
        fields = [
            'id', 'scheduling_run', 'scheduling_run_name', 'soldier', 'soldier_id',
            'assignment_date', 'is_on_base'
        ]
        read_only_fields = ['id', 'scheduling_run_name']