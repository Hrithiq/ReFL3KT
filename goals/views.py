from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from .models import Goal, Task
from .serializers import (
    GoalSerializer, GoalCreateSerializer, GoalTreeSerializer, GoalAnalyticsSerializer,
    TaskSerializer, TaskCreateSerializer
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

    @action(detail=False, methods=['get', 'post'], url_path='user/(?P<user_id>[^/.]+)')
    def by_user(self, request, user_id=None):
        if request.method == 'GET':
            goals = Goal.objects.filter(user_id=user_id)
            serializer = self.get_serializer(goals, many=True)
            return Response(serializer.data)
        elif request.method == 'POST':
            user = get_object_or_404(User, id=user_id)
            # Pass context with user to serializer
            serializer = GoalCreateSerializer(
                data=request.data,
                context={'user': user, 'request': request}
            )
            if serializer.is_valid():
                serializer.save()
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
