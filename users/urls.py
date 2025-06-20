from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('create/', views.create_user, name='create_user'),
    path('<int:user_id>/', views.get_user_details, name='get_user_details'),
] 