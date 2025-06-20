from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CategoryViewSet, TimeEntryViewSet

router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'time-entries', TimeEntryViewSet, basename='time-entry')

urlpatterns = [
    path('users/<str:user_id>/', include([
        path('categories/', CategoryViewSet.as_view({'get': 'list', 'post': 'create'})),
        path('categories/<int:pk>/', CategoryViewSet.as_view({
            'get': 'retrieve',
            'put': 'update',
            'patch': 'partial_update',
            'delete': 'destroy'
        })),
        path('categories/<int:pk>/analytics/', CategoryViewSet.as_view({'get': 'analytics'})),
        
        path('time-entries/', TimeEntryViewSet.as_view({'get': 'list', 'post': 'create'})),
        path('time-entries/<int:pk>/', TimeEntryViewSet.as_view({
            'get': 'retrieve',
            'put': 'update',
            'patch': 'partial_update',
            'delete': 'destroy'
        })),
        path('time-entries/current_time_entry/', TimeEntryViewSet.as_view({'get': 'current_time_entry'})),
        path('time-entries/recent_entries/', TimeEntryViewSet.as_view({'get': 'recent_entries'})),
        path('time-entries/analytics/', TimeEntryViewSet.as_view({'get': 'analytics'})),
    ])),
] 