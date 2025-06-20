from django.shortcuts import render, get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.contrib.auth.models import User
from .serializers import UserCreateSerializer, UserDetailSerializer

# Create your views here.

@api_view(['POST'])
@permission_classes([AllowAny])
def create_user(request):
    """Create a new user directly in auth_user table"""
    serializer = UserCreateSerializer(data=request.data)
    
    if serializer.is_valid():
        try:
            user = serializer.save()
            return Response({
                'id': user.id,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': user.email,
                'is_staff': user.is_staff,
                'is_active': user.is_active,
                'date_joined': user.date_joined,
                'message': 'User created successfully'
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({
                'error': f'Failed to create user: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        return Response({
            'error': 'Invalid data',
            'details': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_user_details(request, user_id):
    """Get user details directly from auth_user table by user ID"""
    try:
        user = get_object_or_404(User, id=user_id)
        serializer = UserDetailSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            'error': f'Failed to retrieve user: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
