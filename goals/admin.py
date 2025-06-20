from django.contrib import admin
from .models import Goal, Task, GroupGoalMember

@admin.register(Goal)
class GoalAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'parent', 'status', 'priority', 'progress', 'is_group_goal', 'created_at']
    list_filter = ['status', 'priority', 'is_group_goal', 'created_at']
    search_fields = ['name', 'description', 'user__username']
    readonly_fields = ['created_at', 'updated_at', 'completed_at']
    ordering = ['-created_at']

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'goal', 'status', 'is_recurring', 'due_date', 'estimated_time', 'created_at']
    list_filter = ['status', 'is_recurring', 'created_at']
    search_fields = ['title', 'description', 'goal__name']
    readonly_fields = ['created_at', 'updated_at', 'completed_at']
    ordering = ['-created_at']

@admin.register(GroupGoalMember)
class GroupGoalMemberAdmin(admin.ModelAdmin):
    list_display = ['goal', 'user', 'role', 'joined_at']
    list_filter = ['role', 'joined_at']
    search_fields = ['goal__name', 'user__username']
    readonly_fields = ['joined_at']
    ordering = ['-joined_at']
