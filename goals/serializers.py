from rest_framework import serializers
from .models import Goal, Task
from django.contrib.auth.models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']

class TaskSerializer(serializers.ModelSerializer):
    actual_time_spent = serializers.ReadOnlyField()
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'goal', 'category', 'category_name',
            'status', 'is_recurring', 'created_at', 'updated_at', 
            'due_date', 'completed_at', 'estimated_time', 'actual_time_spent'
        ]
        read_only_fields = ['created_at', 'updated_at', 'completed_at', 'actual_time_spent']

class GoalSerializer(serializers.ModelSerializer):
    subgoals = serializers.SerializerMethodField()
    tasks = TaskSerializer(many=True, read_only=True)
    parent_name = serializers.CharField(source='parent.name', read_only=True)
    
    class Meta:
        model = Goal
        fields = [
            'id', 'name', 'description', 'user', 'parent', 'parent_name',
            'status', 'priority', 'created_at', 'updated_at', 'deadline',
            'completed_at', 'progress', 'subgoals', 'tasks'
        ]
        read_only_fields = ['created_at', 'updated_at', 'completed_at', 'progress']
    
    def get_subgoals(self, obj):
        """Get immediate subgoals only (1 level deep)"""
        subgoals = obj.subgoals.all()
        return GoalSerializer(subgoals, many=True, context=self.context).data
    
    def validate_parent(self, value):
        """Ensure parent goal belongs to the same user"""
        if value and value.user != self.context['request'].user:
            raise serializers.ValidationError("Parent goal must belong to the same user")
        return value

class GoalCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Goal
        fields = ['name', 'description', 'parent', 'priority', 'deadline']
    
    def validate_parent(self, value):
        """Ensure parent goal belongs to the same user"""
        user = self.context.get('user')
        if value and user and value.user != user:
            raise serializers.ValidationError("Parent goal must belong to the same user")
        return value
    
    def create(self, validated_data):
        # Get user from context (passed from view)
        user = self.context.get('user')
        if user:
            validated_data['user'] = user
        
        # Create and save the goal
        goal = Goal.objects.create(**validated_data)
        return goal
    
    def to_representation(self, instance):
        """Use GoalSerializer for response representation"""
        return GoalSerializer(instance, context=self.context).data

class GoalTreeSerializer(serializers.ModelSerializer):
    """Serializer for tree visualization"""
    children = serializers.SerializerMethodField()
    
    class Meta:
        model = Goal
        fields = ['id', 'name', 'children']
    
    def get_children(self, obj):
        """Get immediate children for tree structure"""
        children = obj.subgoals.all()
        return [{'subgoal_name': child.name, 'goal_id': child.id} for child in children]

class GoalAnalyticsSerializer(serializers.ModelSerializer):
    """Serializer for goal analytics"""
    immediate_children = serializers.SerializerMethodField()
    total_time_spent = serializers.SerializerMethodField()
    
    class Meta:
        model = Goal
        fields = ['id', 'name', 'progress', 'immediate_children', 'total_time_spent']
    
    def get_immediate_children(self, obj):
        """Get 1-level breakdown of immediate children with time spent"""
        result = {}
        
        # Add subgoals with recursive time calculation
        for subgoal in obj.subgoals.all():
            result[subgoal.name] = subgoal.total_time_spent_recursive
        
        # Add direct tasks with their time spent
        for task in obj.tasks.all():
            result[task.title] = task.actual_time_spent
        
        return result
    
    def get_total_time_spent(self, obj):
        """Calculate total time spent on this goal and all its children"""
        return obj.total_time_spent_recursive

class TaskCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ['title', 'description', 'goal', 'category', 'is_recurring', 'due_date', 'estimated_time']
        extra_kwargs = {
            'goal': {'required': False}
        }
    
    def validate_goal(self, value):
        """Ensure task belongs to a goal owned by the user"""
        if value.user != self.context['request'].user:
            raise serializers.ValidationError("Task must belong to a goal owned by you")
        return value
