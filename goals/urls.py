from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers
from . import views

# Main router
router = DefaultRouter()
router.register(r'goals', views.GoalViewSet, basename='goal')
router.register(r'group_goals', views.GroupGoalViewSet, basename='group-goal')

# Nested router for tasks under goals
goals_router = routers.NestedDefaultRouter(router, r'goals', lookup='goal')
goals_router.register(r'tasks', views.TaskViewSet, basename='goal-tasks')

urlpatterns = [
    path('', include(router.urls)),
    path('', include(goals_router.urls)),
]