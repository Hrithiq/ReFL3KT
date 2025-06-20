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
    lookup_field = 'pk'
    
    def get_queryset(self):
        return Goal.objects.all()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return GoalCreateSerializer
        return GoalSerializer
    
    def perform_create(self, serializer):
        serializer.save()
    
    def perform_update(self, serializer):
        serializer.save()
    
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

    # goals/views.py (partial update)
    @action(detail=False, methods=['get', 'post'], url_path='user/(?P<user_id>[^/.]+)')
    def by_user(self, request, user_id=None):
        if request.method == 'GET':
            goals = Goal.objects.filter(user_id=user_id)
            serializer = self.get_serializer(goals, many=True)
            return Response(serializer.data)
        elif request.method == 'POST':
            user = get_object_or_404(User, id=user_id)
            # Pass context with request to serializer
            serializer = GoalCreateSerializer(
                data=request.data,
                context={'request': request}  # Add this line
            )
            if serializer.is_valid():
                serializer.save(user=user)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [AllowAny]
    lookup_field = 'pk'
    
    def get_queryset(self):
        # Use 'goal_id' from URL kwargs instead of 'goal_pk'
        goal_id = self.kwargs.get('goal_id')
        if goal_id:
            return Task.objects.filter(goal_id=goal_id)
        return Task.objects.all()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return TaskCreateSerializer
        return TaskSerializer
    
    def perform_create(self, serializer):
        # Capture 'goal_id' from URL
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
    lookup_field = 'pk'
    
    def get_queryset(self):
        return Goal.objects.filter(is_group_goal=True).distinct()
    
    # def perform_create(self, serializer):
    #     user = get_object_or_404(User, id=self.request.data.get('user_id'))
    #     member_ids = self.request.data.get('member_ids', [])
    #     serializer.save(user=user, member_ids=member_ids)

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
        goals = self.get_queryset().filter(group_members__user_id=user_id)
        serializer = GoalSerializer(goals, many=True)
        return Response(serializer.data)
