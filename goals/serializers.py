from rest_framework import serializers
from .models import Goal, Task, GroupGoalMember
from django.contrib.auth.models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']

class GroupGoalMemberSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = GroupGoalMember
        fields = ['id', 'user', 'role', 'joined_at']

class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'goal', 'status', 
            'is_recurring', 'created_at', 'updated_at', 
            'due_date', 'completed_at', 'estimated_time'
        ]
        read_only_fields = ['created_at', 'updated_at', 'completed_at']

class GoalSerializer(serializers.ModelSerializer):
    subgoals = serializers.SerializerMethodField()
    tasks = TaskSerializer(many=True, read_only=True)
    group_members = GroupGoalMemberSerializer(many=True, read_only=True)
    parent_name = serializers.CharField(source='parent.name', read_only=True)
    
    class Meta:
        model = Goal
        fields = [
            'id', 'name', 'description', 'user', 'parent', 'parent_name',
            'status', 'priority', 'created_at', 'updated_at', 'deadline',
            'completed_at', 'progress', 'is_group_goal', 'subgoals',
            'tasks', 'group_members'
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

# goals/serializers.py (partial update)
class GoalCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Goal
        fields = ['name', 'description', 'parent', 'priority', 'deadline', 'is_group_goal']
    
    def create(self, validated_data):
        # Safely access request from context
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            # Use request.user if needed
            pass  # Your custom logic here
        return super().create(validated_data)


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
        """Get 1-level breakdown of immediate children"""
        children = obj.subgoals.all()
        return [
            {
                'goal_id': child.id,
                'name': child.name,
                'progress': child.progress,
                'status': child.status
            }
            for child in children
        ]
    
    def get_total_time_spent(self, obj):
        """Calculate total time spent on this goal and its tasks"""
        # This would integrate with your time tracking system
        # For now, return estimated time from tasks
        total_minutes = sum(task.estimated_time for task in obj.tasks.all())
        return total_minutes

class TaskCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ['title', 'description', 'goal', 'is_recurring', 'due_date', 'estimated_time']
        extra_kwargs = {
            'goal': {'required': False}  # <-- Add this line
        }
    
    def validate_goal(self, value):
        """Ensure task belongs to a goal owned by the user"""
        if value.user != self.context['request'].user:
            raise serializers.ValidationError("Task must belong to a goal owned by you")
        return value

class GroupGoalCreateSerializer(serializers.ModelSerializer):
    member_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )

    class Meta:
        model = Goal
        fields = ['name', 'description', 'priority', 'deadline', 'member_ids']
        extra_kwargs = {'user': {'read_only': True}}  # Add this

    def create(self, validated_data):
        member_ids = validated_data.pop('member_ids', [])
        request = self.context.get('request')
        
        # Create and save the Goal first
        goal = Goal.objects.create(
            user=request.user,
            is_group_goal=True,
            **validated_data
        )
        
        # Add owner as first member
        GroupGoalMember.objects.create(
            goal=goal,
            user=request.user,
            role='owner'
        )
        
        # Add other members
        for user_id in member_ids:
            try:
                user = User.objects.get(id=user_id)
                GroupGoalMember.objects.create(
                    goal=goal,
                    user=user,
                    role='member'
                )
            except User.DoesNotExist:
                pass
        
        return goal
