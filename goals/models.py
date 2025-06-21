from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Goal(models.Model):
    STATUS_CHOICES = [
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]
    
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='goals')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subgoals')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_started')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deadline = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    progress = models.FloatField(default=0.0)  # 0.0 to 100.0
    
    def __str__(self):
        return f"{self.name} - {self.user.username}"
    
    @property
    def children(self):
        """Get all immediate children (subgoals and tasks)"""
        children = []
        children.extend(self.subgoals.all())
        children.extend(self.tasks.all())
        return children
    
    @property
    def total_time_spent_recursive(self):
        """Calculate total time spent recursively on all tasks under this goal"""
        total_time = 0
        
        # Add time from direct tasks
        for task in self.tasks.all():
            total_time += task.actual_time_spent
        
        # Add time from subgoals recursively
        for subgoal in self.subgoals.all():
            total_time += subgoal.total_time_spent_recursive
        
        return total_time

class Task(models.Model):
    TASK_STATUS_CHOICES = [
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    goal = models.ForeignKey(Goal, on_delete=models.CASCADE, related_name='tasks')
    category = models.ForeignKey('time_tracking.Category', on_delete=models.SET_NULL, null=True, blank=True)
    
    status = models.CharField(max_length=20, choices=TASK_STATUS_CHOICES, default='not_started')
    is_recurring = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    due_date = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    estimated_time = models.IntegerField(default=0)  # in minutes
    
    def __str__(self):
        return f"{self.title} - {self.goal.name}"
    
    @property
    def actual_time_spent(self):
        """Calculate actual time spent on this task based on time entries in the category"""
        if not self.category:
            return 0
        
        from time_tracking.models import TimeEntry
        
        # Get all time entries for this category
        time_entries = TimeEntry.objects.filter(category=self.category)
        
        total_minutes = 0
        for entry in time_entries:
            if entry.start_time and entry.end_time:
                duration = entry.end_time - entry.start_time
                total_minutes += duration.total_seconds() / 60
        
        return total_minutes