from django.contrib import admin
from .models import UserAvailability, ScheduledTask, SchedulingSession

@admin.register(UserAvailability)
class UserAvailabilityAdmin(admin.ModelAdmin):
    list_display = ['user', 'day_of_week', 'start_time', 'end_time', 'is_active']
    list_filter = ['day_of_week', 'is_active', 'user']
    search_fields = ['user__username', 'user__email']
    ordering = ['user', 'day_of_week', 'start_time']

@admin.register(ScheduledTask)
class ScheduledTaskAdmin(admin.ModelAdmin):
    list_display = [
        'task', 'user', 'final_priority_score', 'status', 
        'scheduled_start', 'scheduled_end', 'skip_count'
    ]
    list_filter = ['status', 'user', 'scheduled_start']
    search_fields = ['task__title', 'user__username', 'task__goal__name']
    readonly_fields = [
        'urgency_score', 'importance_score', 'progress_score', 
        'final_priority_score', 'created_at', 'updated_at', 'last_calculated'
    ]
    ordering = ['-final_priority_score', 'scheduled_start']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('task', 'user', 'task__goal')

@admin.register(SchedulingSession)
class SchedulingSessionAdmin(admin.ModelAdmin):
    list_display = ['user', 'session_date', 'total_tasks_scheduled', 'total_time_scheduled', 'created_at']
    list_filter = ['session_date', 'user']
    search_fields = ['user__username', 'session_notes']
    readonly_fields = ['created_at']
    ordering = ['-created_at']
