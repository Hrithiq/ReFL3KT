from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserAvailability, ScheduledTask, SchedulingSession
from goals.models import Goal, Task

class UserAvailabilitySerializer(serializers.ModelSerializer):
    day_name = serializers.CharField(source='get_day_of_week_display', read_only=True)
    
    class Meta:
        model = UserAvailability
        fields = [
            'id', 'user', 'day_of_week', 'day_name', 'start_time', 
            'end_time', 'is_active'
        ]
        read_only_fields = ['id']

class ScheduledTaskSerializer(serializers.ModelSerializer):
    task_title = serializers.CharField(source='task.title', read_only=True)
    task_description = serializers.CharField(source='task.description', read_only=True)
    goal_name = serializers.CharField(source='task.goal.name', read_only=True)
    goal_priority = serializers.CharField(source='task.goal.priority', read_only=True)
    estimated_time = serializers.IntegerField(source='task.estimated_time', read_only=True)
    due_date = serializers.DateTimeField(source='task.due_date', read_only=True)
    
    class Meta:
        model = ScheduledTask
        fields = [
            'id', 'task', 'task_title', 'task_description', 'goal_name', 
            'goal_priority', 'estimated_time', 'due_date',
            'urgency_score', 'importance_score', 'progress_score', 
            'final_priority_score', 'scheduled_start', 'scheduled_end',
            'actual_start', 'actual_end', 'status', 'skip_count',
            'created_at', 'updated_at', 'last_calculated'
        ]
        read_only_fields = [
            'id', 'urgency_score', 'importance_score', 'progress_score',
            'final_priority_score', 'created_at', 'updated_at', 'last_calculated'
        ]

class SchedulingSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = SchedulingSession
        fields = [
            'id', 'user', 'session_date', 'total_tasks_scheduled',
            'total_time_scheduled', 'session_notes', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

class TaskPrioritySerializer(serializers.Serializer):
    """Serializer for task priority calculation results"""
    task_id = serializers.IntegerField()
    task_title = serializers.CharField()
    goal_name = serializers.CharField()
    priority_score = serializers.FloatField()
    urgency_score = serializers.FloatField()
    importance_score = serializers.FloatField()
    progress_score = serializers.FloatField()
    days_to_deadline = serializers.IntegerField(allow_null=True)
    estimated_time = serializers.IntegerField()
    due_date = serializers.DateTimeField(allow_null=True)

class SchedulingRequestSerializer(serializers.Serializer):
    """Serializer for scheduling requests"""
    start_date = serializers.DateTimeField(required=False)
    end_date = serializers.DateTimeField(required=False)
    task_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False
    )
    include_all_tasks = serializers.BooleanField(default=True)

class SchedulingResponseSerializer(serializers.Serializer):
    """Serializer for scheduling responses"""
    scheduled_tasks = ScheduledTaskSerializer(many=True)
    total_tasks_scheduled = serializers.IntegerField()
    total_time_scheduled = serializers.IntegerField()
    scheduling_session = SchedulingSessionSerializer()

class TaskActionSerializer(serializers.Serializer):
    """Serializer for task actions (complete, skip)"""
    task_id = serializers.IntegerField()
    action = serializers.ChoiceField(choices=['complete', 'skip'])
    notes = serializers.CharField(required=False, allow_blank=True)

class HighPriorityTasksResponseSerializer(serializers.Serializer):
    """Serializer for high priority tasks response"""
    tasks = TaskPrioritySerializer(many=True)
    total_count = serializers.IntegerField()
    generated_at = serializers.DateTimeField() 