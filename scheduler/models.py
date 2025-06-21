from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.exceptions import ValidationError
from goals.models import Goal, Task
import math

class UserAvailability(models.Model):
    """User's available time slots for scheduling"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='availabilities')
    day_of_week = models.IntegerField(choices=[
        (0, 'Monday'), (1, 'Tuesday'), (2, 'Wednesday'), 
        (3, 'Thursday'), (4, 'Friday'), (5, 'Saturday'), (6, 'Sunday')
    ])
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['user', 'day_of_week', 'start_time', 'end_time']
    
    def clean(self):
        if self.start_time >= self.end_time:
            raise ValidationError("Start time must be before end time")
    
    def __str__(self):
        return f"{self.user.username} - {self.get_day_of_week_display()} {self.start_time}-{self.end_time}"

class ScheduledTask(models.Model):
    """Scheduled task with priority score and scheduling metadata"""
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='schedules')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='scheduled_tasks')
    
    # Priority calculation components
    urgency_score = models.FloatField(default=0.0)
    importance_score = models.FloatField(default=0.0)
    progress_score = models.FloatField(default=0.0)
    final_priority_score = models.FloatField(default=0.0)
    
    # Scheduling details
    scheduled_start = models.DateTimeField(null=True, blank=True)
    scheduled_end = models.DateTimeField(null=True, blank=True)
    actual_start = models.DateTimeField(null=True, blank=True)
    actual_end = models.DateTimeField(null=True, blank=True)
    
    # Status tracking
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('skipped', 'Skipped'),
        ('rescheduled', 'Rescheduled')
    ], default='pending')
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    skip_count = models.IntegerField(default=0)
    last_calculated = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-final_priority_score', 'scheduled_start']
    
    def __str__(self):
        return f"{self.task.title} - Priority: {self.final_priority_score:.2f}"
    
    def calculate_priority_score(self):
        """Calculate the weighted priority score based on the AI scheduling algorithm"""
        # Calculate urgency (1 / (days_left_to_deadline + 1))
        urgency = 0.0
        if self.task.due_date:
            days_left = (self.task.due_date - timezone.now()).days
            urgency = 1.0 / (max(days_left, 0) + 1)
        else:
            urgency = 0.1  # Low urgency for tasks without deadline
        
        # Calculate importance (priority level)
        priority_map = {'high': 3.0, 'medium': 2.0, 'low': 1.0}
        importance = priority_map.get(self.task.goal.priority, 2.0)
        
        # Calculate progress (1 - progress_percentage)
        progress = 1.0 - (self.task.goal.progress / 100.0)
        
        # Store individual scores
        self.urgency_score = urgency
        self.importance_score = importance
        self.progress_score = progress
        
        # Calculate final weighted score
        # Priority = (Urgency * 0.4) + (Importance * 0.4) + (Progress * 0.2)
        self.final_priority_score = (urgency * 0.4) + (importance * 0.4) + (progress * 0.2)
        
        self.last_calculated = timezone.now()
        return self.final_priority_score
    
    def mark_completed(self):
        """Mark task as completed and trigger rescheduling"""
        self.status = 'completed'
        self.actual_end = timezone.now()
        self.save()
        
        # Trigger rescheduling for remaining tasks
        from .services import SchedulingService
        scheduler = SchedulingService(self.user)
        scheduler.reschedule_remaining_tasks()
    
    def mark_skipped(self):
        """Mark task as skipped and increase urgency for next scheduling"""
        self.status = 'skipped'
        self.skip_count += 1
        self.save()
        
        # Increase urgency for the task
        if self.task.due_date:
            # Move deadline closer by 1 day for each skip
            self.task.due_date = self.task.due_date - timezone.timedelta(days=1)
            self.task.save()
        
        # Trigger rescheduling
        from .services import SchedulingService
        scheduler = SchedulingService(self.user)
        scheduler.reschedule_remaining_tasks()

class SchedulingSession(models.Model):
    """Tracks scheduling sessions and their results"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='scheduling_sessions')
    session_date = models.DateField(auto_now_add=True)
    total_tasks_scheduled = models.IntegerField(default=0)
    total_time_scheduled = models.IntegerField(default=0)  # in minutes
    session_notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.session_date} - {self.total_tasks_scheduled} tasks"
