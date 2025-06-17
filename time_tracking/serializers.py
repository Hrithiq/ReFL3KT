from rest_framework import serializers
from .models import Category, TimeEntry

class CategorySerializer(serializers.ModelSerializer):
    category_id = serializers.IntegerField(source='id', read_only=True)
    name = serializers.CharField(source='_name')
    color = serializers.CharField(source='_color')

    class Meta:
        model = Category
        fields = ['category_id', 'name', 'color']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Convert to Flutter format
        return {
            '_categoryId': data['category_id'],
            '_name': data['name'],
            '_color': data['color']
        }

class TimeEntrySerializer(serializers.ModelSerializer):
    time_entry_id = serializers.IntegerField(source='id', read_only=True)
    category_id = serializers.IntegerField(source='category.id', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    description = serializers.CharField(source='_description')
    start_time = serializers.DateTimeField(source='_startTime')
    end_time = serializers.DateTimeField(source='_endTime')

    class Meta:
        model = TimeEntry
        fields = [
            'time_entry_id',
            'description',
            'start_time',
            'end_time',
            'category_id',
            'category_name',
            'is_active'
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Convert to Flutter format
        return {
            '_timeEntryId': str(data['time_entry_id']),
            '_description': data['description'],
            '_startTime': data['start_time'],
            '_endTime': data['end_time'],
            '_categoryId': data['category_id'],
            '_categoryName': data['category_name']
        }

    def to_internal_value(self, data):
        # Convert from Flutter format to internal format
        internal_data = {
            'description': data.get('_description', ''),
            'start_time': data.get('_startTime'),
            'end_time': data.get('_endTime'),
            'category': data.get('_categoryId')
        }
        return super().to_internal_value(internal_data)

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
