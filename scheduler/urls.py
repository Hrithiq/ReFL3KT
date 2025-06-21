from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserAvailabilityViewSet, ScheduledTaskViewSet, 
    SchedulingViewSet, SchedulingSessionViewSet
)

router = DefaultRouter()
router.register(r'availability', UserAvailabilityViewSet, basename='availability')
router.register(r'scheduled-tasks', ScheduledTaskViewSet, basename='scheduled-tasks')
router.register(r'scheduling', SchedulingViewSet, basename='scheduling')
router.register(r'sessions', SchedulingSessionViewSet, basename='sessions')

urlpatterns = [
    path('', include(router.urls)),
] 