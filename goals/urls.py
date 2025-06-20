from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'goals', views.GoalViewSet, basename='goal')
router.register(r'tasks', views.TaskViewSet, basename='task')
router.register(r'group_goals', views.GroupGoalViewSet, basename='group-goal')

urlpatterns = [
    path('goals/<int:user_id>/', views.GoalViewSet.as_view({'post': 'create_for_user'}), name='goal-create-for-user'),
    path('', include(router.urls)),
]