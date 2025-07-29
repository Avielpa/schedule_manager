# schedule/serializers.py
# Enhanced serializers for hierarchical organizational system

from rest_framework import serializers
from datetime import date

from .models import (
    Organization, Unit, ImportBatch, Soldier, SoldierConstraint, 
    SchedulingRun, Assignment, Event, UserOrganizationRole
)


# =============================================================================
# ORGANIZATION SERIALIZERS
# =============================================================================

class OrganizationSerializer(serializers.ModelSerializer):
    """Serializer for organizations"""
    units_count = serializers.SerializerMethodField()
    soldiers_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Organization
        fields = [
            'id', 'name', 'code', 'description', 'contact_email', 
            'contact_phone', 'address', 'created_at', 'units_count', 'soldiers_count'
        ]
        read_only_fields = ['id', 'created_at', 'units_count', 'soldiers_count']
    
    def get_units_count(self, obj):
        return obj.units.count()
    
    def get_soldiers_count(self, obj):
        return obj.soldiers.filter(status='ACTIVE').count()


class UnitListSerializer(serializers.ModelSerializer):
    """Simplified unit serializer for lists"""
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    parent_unit_name = serializers.CharField(source='parent_unit.name', read_only=True)
    soldiers_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Unit
        fields = [
            'id', 'name', 'code', 'unit_type', 'organization_name', 
            'parent_unit_name', 'soldiers_count', 'is_active'
        ]
    
    def get_soldiers_count(self, obj):
        return obj.get_all_soldiers().filter(status='ACTIVE').count()


class UnitDetailSerializer(serializers.ModelSerializer):
    """Detailed unit serializer"""
    organization = OrganizationSerializer(read_only=True)
    organization_id = serializers.IntegerField(write_only=True)
    parent_unit_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    hierarchy_path = serializers.SerializerMethodField()
    soldiers_count = serializers.SerializerMethodField()
    sub_units_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Unit
        fields = [
            'id', 'name', 'code', 'unit_type', 'description', 'commander', 
            'location', 'organization', 'organization_id', 'parent_unit_id',
            'hierarchy_path', 'soldiers_count', 'sub_units_count',
            'default_min_soldiers_per_day', 'working_days', 'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'hierarchy_path', 'soldiers_count', 'sub_units_count']
    
    def get_hierarchy_path(self, obj):
        return obj.get_full_hierarchy()
    
    def get_soldiers_count(self, obj):
        return obj.get_all_soldiers().filter(status='ACTIVE').count()
    
    def get_sub_units_count(self, obj):
        return obj.sub_units.count()


# =============================================================================
# IMPORT BATCH SERIALIZERS
# =============================================================================

class ImportBatchSerializer(serializers.ModelSerializer):
    """Serializer for import batches"""
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    unit_name = serializers.CharField(source='unit.name', read_only=True)
    imported_by_username = serializers.CharField(source='imported_by.username', read_only=True)
    success_rate = serializers.SerializerMethodField()
    
    class Meta:
        model = ImportBatch
        fields = [
            'id', 'name', 'source_file', 'organization', 'organization_name',
            'unit', 'unit_name', 'imported_by', 'imported_by_username',
            'import_date', 'total_soldiers', 'successful_imports', 
            'failed_imports', 'success_rate', 'import_settings', 'notes'
        ]
        read_only_fields = [
            'id', 'import_date', 'organization_name', 'unit_name', 
            'imported_by_username', 'success_rate'
        ]
    
    def get_success_rate(self, obj):
        if obj.total_soldiers > 0:
            return round((obj.successful_imports / obj.total_soldiers) * 100, 1)
        return 0


# =============================================================================
# SOLDIER SERIALIZERS
# =============================================================================

class SoldierConstraintSerializer(serializers.ModelSerializer):
    """Serializer for soldier constraints"""
    soldier_name = serializers.CharField(source='soldier.name', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = SoldierConstraint
        fields = [
            'id', 'soldier', 'soldier_name', 'constraint_date', 'description',
            'constraint_type', 'is_recurring', 'created_by', 'created_by_username', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'soldier_name', 'created_by_username']


class SoldierListSerializer(serializers.ModelSerializer):
    """Simplified soldier serializer for lists"""
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    unit_name = serializers.CharField(source='unit.name', read_only=True)
    unit_hierarchy = serializers.SerializerMethodField()
    constraints_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Soldier
        fields = [
            'id', 'name', 'soldier_id', 'rank', 'status', 'organization_name',
            'unit_name', 'unit_hierarchy', 'constraints_count', 'is_exceptional_output',
            'is_weekend_only_soldier_flag'
        ]
    
    def get_unit_hierarchy(self, obj):
        return obj.unit.get_full_hierarchy()
    
    def get_constraints_count(self, obj):
        return obj.constraints.count()


class SoldierDetailSerializer(serializers.ModelSerializer):
    """Detailed soldier serializer"""
    organization = OrganizationSerializer(read_only=True)
    unit = UnitListSerializer(read_only=True)
    import_batch = ImportBatchSerializer(read_only=True)
    constraints = SoldierConstraintSerializer(many=True, read_only=True)
    full_designation = serializers.SerializerMethodField()
    
    # Write-only fields for creation/update
    organization_id = serializers.IntegerField(write_only=True)
    unit_id = serializers.IntegerField(write_only=True)
    import_batch_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    
    class Meta:
        model = Soldier
        fields = [
            'id', 'name', 'soldier_id', 'rank', 'organization', 'organization_id',
            'unit', 'unit_id', 'import_batch', 'import_batch_id', 'email', 'phone',
            'is_exceptional_output', 'is_weekend_only_soldier_flag', 'status',
            'hire_date', 'specialty', 'security_clearance', 'preferred_shift',
            'max_consecutive_days', 'constraints', 'full_designation',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'full_designation'
        ]
    
    def get_full_designation(self, obj):
        return obj.get_full_designation()
    
    def create(self, validated_data):
        """Create soldier with constraints"""
        constraints_data = validated_data.pop('constraints', [])
        soldier = Soldier.objects.create(**validated_data)
        
        for constraint_data in constraints_data:
            SoldierConstraint.objects.create(soldier=soldier, **constraint_data)
        
        return soldier


# For backward compatibility
SoldierSerializer = SoldierListSerializer


# =============================================================================
# EVENT SERIALIZERS
# =============================================================================

class EventSerializer(serializers.ModelSerializer):
    """Serializer for events"""
    organization = OrganizationSerializer(read_only=True)
    organization_id = serializers.IntegerField(write_only=True)
    target_units = UnitListSerializer(many=True, read_only=True)
    target_units_ids = serializers.ListField(
        child=serializers.IntegerField(), write_only=True, required=False
    )
    specific_soldiers = SoldierListSerializer(many=True, read_only=True)
    specific_soldiers_ids = serializers.ListField(
        child=serializers.IntegerField(), write_only=True, required=False
    )
    target_soldiers_count = serializers.SerializerMethodField()
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = Event
        fields = [
            'id', 'event_type', 'name', 'description', 'start_date', 'end_date',
            'organization', 'organization_id', 'target_units', 'target_units_ids',
            'specific_soldiers', 'specific_soldiers_ids', 'target_soldiers_count',
            'min_required_soldiers', 'max_home_days_per_soldier', 'base_days_per_soldier',
            'home_days_per_soldier', 'priority_level', 'is_mandatory', 'location',
            'soldier_constraint', 'created_by', 'created_by_username', 'created_at'
        ]
        read_only_fields = [
            'id', 'created_at', 'target_soldiers_count', 'created_by_username'
        ]
    
    def get_target_soldiers_count(self, obj):
        return len(obj.get_target_soldiers())
    
    def create(self, validated_data):
        target_units_ids = validated_data.pop('target_units_ids', [])
        specific_soldiers_ids = validated_data.pop('specific_soldiers_ids', [])
        
        event = Event.objects.create(**validated_data)
        
        if target_units_ids:
            event.target_units.set(target_units_ids)
        if specific_soldiers_ids:
            event.specific_soldiers.set(specific_soldiers_ids)
        
        return event
    
    def update(self, instance, validated_data):
        target_units_ids = validated_data.pop('target_units_ids', None)
        specific_soldiers_ids = validated_data.pop('specific_soldiers_ids', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        if target_units_ids is not None:
            instance.target_units.set(target_units_ids)
        if specific_soldiers_ids is not None:
            instance.specific_soldiers.set(specific_soldiers_ids)
        
        return instance


# =============================================================================
# SCHEDULING RUN SERIALIZERS
# =============================================================================

class SchedulingRunListSerializer(serializers.ModelSerializer):
    """Simplified scheduling run serializer for lists"""
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    target_units_count = serializers.SerializerMethodField()
    assignments_count = serializers.SerializerMethodField()
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = SchedulingRun
        fields = [
            'id', 'name', 'organization_name', 'start_date', 'end_date',
            'status', 'target_units_count', 'assignments_count',
            'created_by_username', 'run_date'
        ]
    
    def get_target_units_count(self, obj):
        return obj.target_units.count()
    
    def get_assignments_count(self, obj):
        return obj.assignments.count()


class SchedulingRunDetailSerializer(serializers.ModelSerializer):
    """Detailed scheduling run serializer"""
    organization = OrganizationSerializer(read_only=True)
    organization_id = serializers.IntegerField(write_only=True)
    target_units = UnitListSerializer(many=True, read_only=True)
    target_units_ids = serializers.ListField(
        child=serializers.IntegerField(), write_only=True, required=False
    )
    priority_soldiers = SoldierListSerializer(many=True, read_only=True)
    priority_soldiers_ids = serializers.ListField(
        child=serializers.IntegerField(), write_only=True, required=False
    )
    exclude_soldiers = SoldierListSerializer(many=True, read_only=True)
    exclude_soldiers_ids = serializers.ListField(
        child=serializers.IntegerField(), write_only=True, required=False
    )
    target_soldiers_count = serializers.SerializerMethodField()
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = SchedulingRun
        fields = [
            'id', 'name', 'description', 'organization', 'organization_id',
            'target_units', 'target_units_ids', 'priority_soldiers', 'priority_soldiers_ids',
            'exclude_soldiers', 'exclude_soldiers_ids', 'target_soldiers_count',
            'run_date', 'start_date', 'end_date', 'default_base_days_target',
            'default_home_days_target', 'max_consecutive_base_days',
            'max_consecutive_home_days', 'min_base_block_days',
            'min_required_soldiers_per_day', 'max_total_home_days',
            'max_weekend_base_days_per_soldier', 'status', 'solution_details',
            'algorithm_version', 'processing_time_seconds', 'created_by',
            'created_by_username'
        ]
        read_only_fields = [
            'id', 'run_date', 'status', 'solution_details', 'algorithm_version',
            'processing_time_seconds', 'target_soldiers_count', 'created_by_username'
        ]
    
    def get_target_soldiers_count(self, obj):
        return obj.get_target_soldiers().count()
    
    def create(self, validated_data):
        target_units_ids = validated_data.pop('target_units_ids', [])
        priority_soldiers_ids = validated_data.pop('priority_soldiers_ids', [])
        exclude_soldiers_ids = validated_data.pop('exclude_soldiers_ids', [])
        
        scheduling_run = SchedulingRun.objects.create(**validated_data)
        
        if target_units_ids:
            scheduling_run.target_units.set(target_units_ids)
        if priority_soldiers_ids:
            scheduling_run.priority_soldiers.set(priority_soldiers_ids)
        if exclude_soldiers_ids:
            scheduling_run.exclude_soldiers.set(exclude_soldiers_ids)
        
        return scheduling_run


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
    unit_name = serializers.CharField(source='soldier.unit.name', read_only=True)
    
    class Meta:
        model = Assignment
        fields = [
            'id', 'scheduling_run', 'scheduling_run_name', 'soldier', 'soldier_id',
            'assignment_date', 'is_on_base', 'shift_type', 'location', 'notes', 'unit_name'
        ]
        read_only_fields = ['id', 'scheduling_run_name', 'unit_name']


# =============================================================================
# USER ROLE SERIALIZERS
# =============================================================================

class UserOrganizationRoleSerializer(serializers.ModelSerializer):
    """Serializer for user organization roles"""
    user_username = serializers.CharField(source='user.username', read_only=True)
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    units = UnitListSerializer(many=True, read_only=True)
    units_ids = serializers.ListField(
        child=serializers.IntegerField(), write_only=True, required=False
    )
    managed_units_count = serializers.SerializerMethodField()
    
    class Meta:
        model = UserOrganizationRole
        fields = [
            'id', 'user', 'user_username', 'organization', 'organization_name',
            'units', 'units_ids', 'managed_units_count', 'role', 'created_at', 'is_active'
        ]
        read_only_fields = [
            'id', 'created_at', 'user_username', 'organization_name', 'managed_units_count'
        ]
    
    def get_managed_units_count(self, obj):
        count = obj.units.count()
        if count > 0:
            return count
        return 'All' if obj.role in ['ADMIN', 'SCHEDULER'] else 0
    
    def create(self, validated_data):
        units_ids = validated_data.pop('units_ids', [])
        role = UserOrganizationRole.objects.create(**validated_data)
        
        if units_ids:
            role.units.set(units_ids)
        
        return role
    
    def update(self, instance, validated_data):
        units_ids = validated_data.pop('units_ids', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        if units_ids is not None:
            instance.units.set(units_ids)
        
        return instance