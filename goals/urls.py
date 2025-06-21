from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers
from . import views

# Main router
router = DefaultRouter()
router.register(r'goals', views.GoalViewSet, basename='goal')

# Nested router for tasks under goals
goals_router = routers.NestedDefaultRouter(router, r'goals', lookup='goal')
goals_router.register(r'tasks', views.TaskViewSet, basename='goal-tasks')

urlpatterns = [
    path('users/<int:user_id>/', include([
        path('goals/', views.GoalViewSet.as_view({'post': 'by_user', 'get': 'by_user',})),
        path('goals/root/', views.GoalViewSet.as_view({'get': 'root_goals'})),
        path('goals/<int:pk>/', views.GoalViewSet.as_view({
            'get': 'retrieve',
            'put': 'update',
            'post': 'create',
            'patch': 'partial_update',
            'delete': 'destroy'
        })),
        path('goals/<int:pk>/analytics/', views.GoalViewSet.as_view({'get': 'analytics'})),
        path('goals/<int:pk>/tree_widget/', views.GoalViewSet.as_view({'get': 'tree_widget'})),
        path('goals/<int:goal_id>/tasks/', views.TaskViewSet.as_view({'get': 'list', 'post': 'create'})),
        path('goals/<int:goal_id>/tasks/<int:pk>/', views.TaskViewSet.as_view({
            'get': 'retrieve',  
            'put': 'update',
            'patch': 'partial_update',
            'delete': 'destroy'
        })),
    ])),
]