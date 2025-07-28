# schedule/serializers.py

from rest_framework import serializers
from .models import Soldier, SoldierConstraint, SchedulingRun, Assignment,Event
from datetime import date

class SoldierConstraintSerializer(serializers.ModelSerializer):
    """
    Serializer for soldier constraints. Also used as a nested field in SoldierSerializer.
    """
    class Meta:
        model = SoldierConstraint
        fields = ['constraint_date', 'description']
        extra_kwargs = {'id': {'read_only': True}} 

class SoldierSerializer(serializers.ModelSerializer):
    constraints = SoldierConstraintSerializer(many=True, required=False, allow_empty=True)

    class Meta:
        model = Soldier
        # Adding new fields:
        fields = ['id', 'name', 'is_exceptional_output', 'is_weekend_only_soldier_flag', 'constraints']
        read_only_fields = ['id'] 
    
    def create(self, validated_data):
        constraints_data = validated_data.pop('constraints', []) 
        # New: Extract new fields if they exist
        is_exceptional_output = validated_data.pop('is_exceptional_output', False)
        is_weekend_only_soldier_flag = validated_data.pop('is_weekend_only_soldier_flag', False)

        soldier = Soldier.objects.create(
            is_exceptional_output=is_exceptional_output,
            is_weekend_only_soldier_flag=is_weekend_only_soldier_flag,
            **validated_data
        ) 
        
        for constraint_data in constraints_data:
            constraint = SoldierConstraint(soldier=soldier, **constraint_data)
            constraint.save() 
        
        return soldier

    def update(self, instance, validated_data):
        constraints_data = validated_data.pop('constraints', [])
        
        instance.name = validated_data.get('name', instance.name)
        # New: Update new fields
        instance.is_exceptional_output = validated_data.get('is_exceptional_output', instance.is_exceptional_output)
        instance.is_weekend_only_soldier_flag = validated_data.get('is_weekend_only_soldier_flag', instance.is_weekend_only_soldier_flag)
        instance.save()

        # Delete and recreate existing constraints to handle complex updates
        instance.constraints.all().delete() 
        for constraint_data in constraints_data:
            constraint = SoldierConstraint(soldier=instance, **constraint_data)
            constraint.save() 
        
        return instance

class AssignmentSerializer(serializers.ModelSerializer):
    """
    Serializer for the Assignment model.
    """
    soldier_name = serializers.CharField(source='soldier.name', read_only=True)
    
    class Meta:
        model = Assignment
        fields = ['id', 'soldier', 'soldier_name', 'assignment_date', 'is_on_base']
        read_only_fields = ['soldier']

class SchedulingRunSerializer(serializers.ModelSerializer):
    """
    Serializer for the SchedulingRun model, including nested assignments.
    """
    assignments = AssignmentSerializer(many=True, read_only=True)

    class Meta:
        model = SchedulingRun
        fields = [
            'id', 'run_date', 'start_date', 'end_date',
            'default_base_days_target', 'default_home_days_target',
            'max_consecutive_base_days', 'max_consecutive_home_days',
            'min_base_block_days', 'min_required_soldiers_per_day',
            'max_total_home_days', 'max_weekend_base_days_per_soldier', # New
            'status', 'solution_details', 'assignments'
        ]
        read_only_fields = ['run_date', 'status', 'solution_details', 'assignments']

class ScheduleCreateSerializer(serializers.Serializer):
    """
    Serializer for receiving data to create a new scheduling run.
    All fields are required.
    """
    start_date = serializers.DateField(required=True)
    end_date = serializers.DateField(required=True)
    default_base_days_target = serializers.IntegerField(default=7)
    default_home_days_target = serializers.IntegerField(default=5)
    max_consecutive_base_days = serializers.IntegerField(default=14)
    max_consecutive_home_days = serializers.IntegerField(default=7)
    min_base_block_days = serializers.IntegerField(default=3)
    min_required_soldiers_per_day = serializers.IntegerField(required=True)
    max_total_home_days = serializers.IntegerField(required=False, allow_null=True)
    max_weekend_base_days_per_soldier = serializers.IntegerField(required=False, allow_null=True) # New


    def validate(self, data):
        if data['start_date'] >= data['end_date']:
            raise serializers.ValidationError("Start date must be before end date.")
        return data

class ScheduleUpdateSerializer(serializers.Serializer):
    """
    Serializer for receiving data to update an existing scheduling run.
    Only scheduling_run_id is required, other fields are optional.
    """
    scheduling_run_id = serializers.IntegerField(required=True, help_text="ID of existing scheduling run to update")
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
    default_base_days_target = serializers.IntegerField(required=False)
    default_home_days_target = serializers.IntegerField(required=False)
    max_consecutive_base_days = serializers.IntegerField(required=False)
    max_consecutive_home_days = serializers.IntegerField(required=False)
    min_base_block_days = serializers.IntegerField(required=False)
    min_required_soldiers_per_day = serializers.IntegerField(required=False)
    max_total_home_days = serializers.IntegerField(required=False, allow_null=True)
    max_weekend_base_days_per_soldier = serializers.IntegerField(required=False, allow_null=True) # New


    def validate(self, data):
        if 'start_date' in data and 'end_date' in data and data['start_date'] >= data['end_date']:
            raise serializers.ValidationError("Start date must be before end date.")
        return data 


class EventSerializer(serializers.ModelSerializer):
    """
    Serializer for the Event model.
    """
    # We will keep soldier_name for now, but it might be removed later
    # if we fully decouple SoldierConstraint from Event.
    soldier_name = serializers.SerializerMethodField()
    
    # This field will allow sending/receiving a list of soldier IDs
    soldiers = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Soldier.objects.all(), required=False
    )

    class Meta:
        model = Event
        fields = [
            'id', 'event_type', 'name', 'description', 
            'start_date', 'end_date', 'soldier_constraint',
            'soldier_name', 'soldiers' # Add the new 'soldiers' field
        ]
        read_only_fields = ['soldier_name'] # soldier_name is still read-only

    def get_soldier_name(self, obj):
        if obj.soldier_constraint and obj.soldier_constraint.soldier:
            return obj.soldier_constraint.soldier.name
        return None
