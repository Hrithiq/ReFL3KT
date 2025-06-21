from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime, timedelta

from .models import UserAvailability, ScheduledTask, SchedulingSession
from .serializers import (
    UserAvailabilitySerializer, ScheduledTaskSerializer, SchedulingSessionSerializer,
    TaskPrioritySerializer, SchedulingRequestSerializer, SchedulingResponseSerializer,
    TaskActionSerializer, HighPriorityTasksResponseSerializer
)
from .services import SchedulingService
from goals.models import Goal, Task

class UserAvailabilityViewSet(viewsets.ModelViewSet):
    """ViewSet for managing user availability"""
    serializer_class = UserAvailabilitySerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        user_id = self.kwargs.get('user_id')
        if user_id:
            return UserAvailability.objects.filter(user_id=user_id)
        return UserAvailability.objects.all()
    
    @action(detail=False, methods=['get'], url_path='user/(?P<user_id>[^/.]+)')
    def by_user(self, request, user_id=None):
        """Get all availability slots for a specific user"""
        availabilities = self.get_queryset()
        serializer = self.get_serializer(availabilities, many=True)
        return Response(serializer.data)

class ScheduledTaskViewSet(viewsets.ModelViewSet):
    """ViewSet for managing scheduled tasks"""
    serializer_class = ScheduledTaskSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        user_id = self.kwargs.get('user_id')
        if user_id:
            return ScheduledTask.objects.filter(user_id=user_id)
        return ScheduledTask.objects.all()
    
    @action(detail=False, methods=['get'], url_path='user/(?P<user_id>[^/.]+)')
    def by_user(self, request, user_id=None):
        """Get all scheduled tasks for a specific user"""
        scheduled_tasks = self.get_queryset()
        serializer = self.get_serializer(scheduled_tasks, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], url_path='complete')
    def complete_task(self, request, pk=None):
        """Mark a scheduled task as completed"""
        scheduled_task = self.get_object()
        scheduled_task.mark_completed()
        serializer = self.get_serializer(scheduled_task)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], url_path='skip')
    def skip_task(self, request, pk=None):
        """Mark a scheduled task as skipped"""
        scheduled_task = self.get_object()
        scheduled_task.mark_skipped()
        serializer = self.get_serializer(scheduled_task)
        return Response(serializer.data)

class SchedulingViewSet(viewsets.ViewSet):
    """ViewSet for AI scheduling operations"""
    permission_classes = [AllowAny]
    
    @action(detail=False, methods=['post'], url_path='schedule/(?P<user_id>[^/.]+)')
    def schedule_tasks(self, request, user_id=None):
        """
        Schedule tasks using the AI scheduling algorithm
        
        Request body:
        {
            "start_date": "2024-01-01T09:00:00Z",  // optional
            "end_date": "2024-01-07T17:00:00Z",    // optional
            "task_ids": [1, 2, 3],                 // optional, specific tasks
            "include_all_tasks": true              // optional, default true
        }
        """
        user = get_object_or_404(User, id=user_id)
        
        # Validate request data
        request_serializer = SchedulingRequestSerializer(data=request.data)
        if not request_serializer.is_valid():
            return Response(request_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = request_serializer.validated_data
        
        # Initialize scheduling service
        scheduler = SchedulingService(user)
        
        # Get tasks to schedule
        if data.get('task_ids'):
            # Schedule specific tasks
            tasks = Task.objects.filter(
                id__in=data['task_ids'],
                goal__user=user
            )
        elif data.get('include_all_tasks', True):
            # Schedule all user's tasks
            tasks = scheduler.get_all_tasks_for_user()
        else:
            return Response(
                {"error": "No tasks specified for scheduling"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Perform scheduling
        try:
            scheduled_tasks = scheduler.schedule_tasks(
                tasks=tasks,
                start_date=data.get('start_date'),
                end_date=data.get('end_date')
            )
            
            # Get the latest scheduling session
            latest_session = SchedulingSession.objects.filter(
                user=user
            ).order_by('-created_at').first()
            
            # Prepare response
            response_data = {
                'scheduled_tasks': ScheduledTaskSerializer(scheduled_tasks, many=True).data,
                'total_tasks_scheduled': len(scheduled_tasks),
                'total_time_scheduled': sum(task.task.estimated_time for task in scheduled_tasks),
                'scheduling_session': SchedulingSessionSerializer(latest_session).data if latest_session else None
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {"error": f"Scheduling failed: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'], url_path='high-priority/(?P<user_id>[^/.]+)')
    def get_high_priority_tasks(self, request, user_id=None):
        """
        Get high priority tasks that are close to due date
        
        Query parameters:
        - limit: number of tasks to return (default: 10)
        """
        user = get_object_or_404(User, id=user_id)
        limit = int(request.query_params.get('limit', 10))
        
        scheduler = SchedulingService(user)
        high_priority_tasks = scheduler.get_high_priority_tasks(limit=limit)
        
        # Convert to serializer format
        task_data = []
        for task_info in high_priority_tasks:
            task_data.append({
                'task_id': task_info['task'].id,
                'task_title': task_info['task'].title,
                'goal_name': task_info['goal_name'],
                'priority_score': task_info['priority_score'],
                'urgency_score': task_info['urgency_score'],
                'importance_score': task_info['importance_score'],
                'progress_score': task_info['progress_score'],
                'days_to_deadline': task_info['days_to_deadline'],
                'estimated_time': task_info['estimated_time'],
                'due_date': task_info['task'].due_date
            })
        
        response_data = {
            'tasks': task_data,
            'total_count': len(task_data),
            'generated_at': timezone.now()
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['post'], url_path='task-action/(?P<user_id>[^/.]+)')
    def perform_task_action(self, request, user_id=None):
        """
        Perform actions on tasks (complete, skip)
        
        Request body:
        {
            "task_id": 1,
            "action": "complete",  // or "skip"
            "notes": "Optional notes"
        }
        """
        user = get_object_or_404(User, id=user_id)
        
        # Validate request data
        action_serializer = TaskActionSerializer(data=request.data)
        if not action_serializer.is_valid():
            return Response(action_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = action_serializer.validated_data
        
        # Get the task
        task = get_object_or_404(Task, id=data['task_id'], goal__user=user)
        
        # Initialize scheduling service
        scheduler = SchedulingService(user)
        
        try:
            if data['action'] == 'complete':
                scheduler.handle_task_completion(task)
                message = "Task completed successfully"
            elif data['action'] == 'skip':
                scheduler.handle_task_skip(task)
                message = "Task skipped successfully"
            else:
                return Response(
                    {"error": "Invalid action"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            return Response({
                "message": message,
                "task_id": task.id,
                "action": data['action']
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {"error": f"Action failed: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'], url_path='reschedule/(?P<user_id>[^/.]+)')
    def reschedule_remaining_tasks(self, request, user_id=None):
        """Reschedule remaining tasks after changes"""
        user = get_object_or_404(User, id=user_id)
        
        scheduler = SchedulingService(user)
        
        try:
            scheduler.reschedule_remaining_tasks()
            
            # Get updated scheduled tasks
            scheduled_tasks = ScheduledTask.objects.filter(
                user=user,
                status__in=['pending', 'in_progress']
            )
            
            return Response({
                "message": "Tasks rescheduled successfully",
                "scheduled_tasks": ScheduledTaskSerializer(scheduled_tasks, many=True).data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {"error": f"Rescheduling failed: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class SchedulingSessionViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing scheduling sessions"""
    serializer_class = SchedulingSessionSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        user_id = self.kwargs.get('user_id')
        if user_id:
            return SchedulingSession.objects.filter(user_id=user_id)
        return SchedulingSession.objects.all()
    
    @action(detail=False, methods=['get'], url_path='user/(?P<user_id>[^/.]+)')
    def by_user(self, request, user_id=None):
        """Get all scheduling sessions for a specific user"""
        sessions = self.get_queryset()
        serializer = self.get_serializer(sessions, many=True)
        return Response(serializer.data)
