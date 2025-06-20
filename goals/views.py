from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from .models import Goal, Task, GroupGoalMember
from .serializers import (
    GoalSerializer, GoalCreateSerializer, GoalTreeSerializer, GoalAnalyticsSerializer,
    TaskSerializer, TaskCreateSerializer,
    GroupGoalCreateSerializer, GroupGoalMemberSerializer
)

class GoalViewSet(viewsets.ModelViewSet):
    serializer_class = GoalSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        user_id = self.kwargs.get('user_id')
        if user_id:
            return Goal.objects.filter(user_id=user_id)
        return Goal.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        if self.action == 'create':
            return GoalCreateSerializer
        return GoalSerializer
    
    def perform_create(self, serializer):
        user_id = self.kwargs.get('user_id')
        if user_id:
            serializer.save(user_id=user_id)
        else:
            serializer.save(user=self.request.user)
    
    def perform_update(self, serializer):
        user_id = self.kwargs.get('user_id')
        if user_id:
            serializer.save(user_id=user_id)
        else:
            serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['get'], url_path='root_goals/(?P<user_id>[^/.]+)')
    def root_goals(self, request, user_id=None):
        """Get all root goals (parent=null) for a user"""
        goals = Goal.objects.filter(user_id=user_id, parent__isnull=True)
        serializer = self.get_serializer(goals, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'], url_path='analytics')
    def analytics(self, request, pk=None, user_id=None):
        """Returns 1-level breakdown of time spent on immediate children"""
        goal = self.get_object()
        serializer = GoalAnalyticsSerializer(goal)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'], url_path='tree_widget')
    def tree_widget(self, request, pk=None, user_id=None):
        """Returns adjacency list for tree visualization"""
        goal = self.get_object()
        serializer = GoalTreeSerializer(goal)
        return Response(serializer.data)

class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        goal_id = self.kwargs.get('goal_id')
        if goal_id:
            return Task.objects.filter(goal_id=goal_id)
        return Task.objects.filter(goal__user=self.request.user)
    
    def get_serializer_class(self):
        if self.action == 'create':
            return TaskCreateSerializer
        return TaskSerializer
    
    def perform_create(self, serializer):
        goal_id = self.kwargs.get('goal_id')
        if goal_id:
            goal = get_object_or_404(Goal, id=goal_id)
            serializer.save(goal=goal)
        else:
            serializer.save()
    
    @action(detail=True, methods=['get'], url_path='detail')
    def task_detail(self, request, pk=None, goal_id=None):
        """Get single task details"""
        task = self.get_object()
        serializer = self.get_serializer(task)
        return Response(serializer.data)

class GroupGoalViewSet(viewsets.ModelViewSet):
    serializer_class = GroupGoalCreateSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        user_id = self.kwargs.get('user_id')
        if user_id:
            return Goal.objects.filter(
                is_group_goal=True,
                group_members__user_id=user_id
            ).distinct()
        return Goal.objects.filter(
            is_group_goal=True,
            group_members__user=self.request.user
        ).distinct()
    
    def perform_create(self, serializer):
        serializer.save()
    
    @action(detail=True, methods=['put'], url_path='members')
    def update_members(self, request, pk=None):
        """Add/remove group members"""
        goal = self.get_object()
        action = request.data.get('action')  # 'add' or 'remove'
        user_ids = request.data.get('user_ids', [])
        
        if action == 'add':
            for user_id in user_ids:
                try:
                    user = User.objects.get(id=user_id)
                    GroupGoalMember.objects.get_or_create(
                        goal=goal,
                        user=user,
                        defaults={'role': 'member'}
                    )
                except User.DoesNotExist:
                    pass
        
        elif action == 'remove':
            GroupGoalMember.objects.filter(
                goal=goal,
                user_id__in=user_ids
            ).exclude(role='owner').delete()
        
        return Response({'status': 'Members updated successfully'})
    
    @action(detail=False, methods=['get'], url_path='(?P<user_id>[^/.]+)')
    def user_group_goals(self, request, user_id=None):
        """Get all group goals for a user"""
        goals = self.get_queryset()
        serializer = GoalSerializer(goals, many=True)
        return Response(serializer.data)
