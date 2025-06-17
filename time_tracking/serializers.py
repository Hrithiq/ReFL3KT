from rest_framework import serializers
from .models import Category, TimeEntry

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'color', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

    def create(self, validated_data):
        # Create category without user
        return Category.objects.create(**validated_data)

class TimeEntrySerializer(serializers.ModelSerializer):
    duration = serializers.DurationField(read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = TimeEntry
        fields = ['id', 'description', 'start_time', 'end_time', 'category', 
                 'category_name', 'is_active', 'duration', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at', 'is_active']

    def validate(self, data):
        # Validate start_time is required
        if 'start_time' not in data:
            raise serializers.ValidationError({"start_time": "This field is required."})

        # Only validate end_time if both start_time and end_time are provided
        if 'end_time' in data:
            if data['start_time'] >= data['end_time']:
                raise serializers.ValidationError("End time must be after start time")
            
        # Check for existing active entry when creating a new one
        if not self.instance and data.get('is_active', True):
            if TimeEntry.objects.filter(is_active=True).exists():
                raise serializers.ValidationError(
                    "There is already an active time entry. Please end it before starting a new one."
                )
            
        return data

    def create(self, validated_data):
        # Create time entry without user
        return TimeEntry.objects.create(**validated_data)
