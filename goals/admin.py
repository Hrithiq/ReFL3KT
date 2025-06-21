from django.contrib import admin
from .models import Goal, Task

class TaskInline(admin.TabularInline):
    model = Task
    extra = 1

class GoalAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'status', 'priority', 'progress', 'created_at']
    list_filter = ['status', 'priority', 'created_at']
    search_fields = ['name', 'description', 'user__username']
    readonly_fields = ['created_at', 'updated_at', 'completed_at', 'progress']
    inlines = [TaskInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'user', 'parent')
        }),
        ('Status & Priority', {
            'fields': ('status', 'priority', 'progress')
        }),
        ('Timeline', {
            'fields': ('deadline', 'created_at', 'updated_at', 'completed_at')
        }),
    )

class TaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'goal', 'status', 'estimated_time', 'created_at']
    list_filter = ['status', 'is_recurring', 'created_at']
    search_fields = ['title', 'description', 'goal__name']
    readonly_fields = ['created_at', 'updated_at', 'completed_at', 'actual_time_spent']

admin.site.register(Goal, GoalAdmin)
admin.site.register(Task, TaskAdmin)
