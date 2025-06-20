from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.utils import timezone

class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating users directly in auth_user table"""
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = [
            'username', 'first_name', 'last_name', 'email', 
            'password', 'password_confirm', 'is_staff', 'is_active'
        ]
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
            'email': {'required': True},
            'is_staff': {'default': False},
            'is_active': {'default': True}
        }
    
    def validate(self, attrs):
        """Validate that passwords match"""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs
    
    def create(self, validated_data):
        """Create a new user"""
        validated_data.pop('password_confirm')
        validated_data['date_joined'] = timezone.now()
        validated_data['is_superuser'] = False
        
        user = User.objects.create_user(**validated_data)
        return user

class UserDetailSerializer(serializers.ModelSerializer):
    """Serializer for retrieving user details from auth_user table"""
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'first_name', 'last_name', 'email',
            'is_staff', 'is_active', 'is_superuser', 'date_joined', 'last_login'
        ]
        read_only_fields = fields  # All fields are read-only for GET requests 