from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

class Goal(models.Model):
    GOAL_STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('paused', 'Paused'),
        ('cancelled', 'Cancelled'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    # Basic fields
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='goals')
    
    # Hierarchy
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subgoals')
    
    # Status and priority
    status = models.CharField(max_length=20, choices=GOAL_STATUS_CHOICES, default='active')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    
    # Time tracking
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deadline = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Progress tracking
    progress = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        default=0.0,
        help_text="Progress percentage (0-100)"
    )
    
    # Group functionality
    is_group_goal = models.BooleanField(default=False)
    group_members = models.ManyToManyField(User, through='GroupGoalMember', related_name='group_goals')
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['user', 'name', 'parent']
    
    def __str__(self):
        return f"{self.name} ({self.user.username})"
    
    def save(self, *args, **kwargs):
        # Auto-update progress based on subgoals
        if self.subgoals.exists():
            total_progress = sum(subgoal.progress for subgoal in self.subgoals.all())
            self.progress = total_progress / self.subgoals.count()
        
        # Mark as completed if progress is 100%
        if self.progress >= 100.0 and self.status != 'completed':
            self.status = 'completed'
            self.completed_at = timezone.now()
        
        super().save(*args, **kwargs)
    
    @property
    def is_root(self):
        return self.parent is None
    
    @property
    def has_children(self):
        return self.subgoals.exists()
    
    @property
    def all_children(self):
        """Get all descendants recursively"""
        children = []
        for subgoal in self.subgoals.all():
            children.append(subgoal)
            children.extend(subgoal.all_children)
        return children

class Task(models.Model):
    TASK_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Basic fields
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    goal = models.ForeignKey(Goal, on_delete=models.CASCADE, related_name='tasks')
    
    # Status and recurring
    status = models.CharField(max_length=20, choices=TASK_STATUS_CHOICES, default='pending')
    is_recurring = models.BooleanField(default=False)
    
    # Time tracking
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    due_date = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Estimated time in minutes
    estimated_time = models.PositiveIntegerField(default=60, help_text="Estimated time in minutes")
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} ({self.goal.name})"
    
    def save(self, *args, **kwargs):
        # Update goal progress when task is completed
        if self.status == 'completed' and not self.completed_at:
            self.completed_at = timezone.now()
        
        super().save(*args, **kwargs)
        
        # Update parent goal progress
        self.goal.save()

class GroupGoalMember(models.Model):
    ROLE_CHOICES = [
        ('owner', 'Owner'),
        ('admin', 'Admin'),
        ('member', 'Member'),
    ]
    
    goal = models.ForeignKey(Goal, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    joined_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['goal', 'user']
    
    def __str__(self):
        return f"{self.user.username} - {self.goal.name} ({self.role})"