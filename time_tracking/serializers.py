from rest_framework import serializers
from .models import Category, TimeEntry

class CategorySerializer(serializers.ModelSerializer):
    category_id = serializers.IntegerField(source='id', read_only=True)
    
    class Meta:
        model = Category
        fields = ['category_id', 'name', 'color']
        # Exclude 'id' from being writable - let Django auto-generate it
        read_only_fields = ['category_id']
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        return {
            '_categoryId': data['category_id'],
            '_name': data['name'],
            '_color': data['color']
        }
    
    def create(self, validated_data):
        # Remove any 'id' field that might have been passed
        validated_data.pop('id', None)
        validated_data.pop('category_id', None)
        
        # Don't pass any 'id' field - let Django auto-generate it
        return Category.objects.create(
            name=validated_data['name'],
            color=validated_data['color'],
            user_id=validated_data.get('user_id')  # This should be set in the view
        )
class TimeEntrySerializer(serializers.ModelSerializer):
    time_entry_id = serializers.IntegerField(source='id', read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        source='category', 
        queryset=Category.objects.all(), 
        required=False, 
        allow_null=True
    )
    category_name = serializers.CharField(source='category.name', read_only=True)
    description = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    start_time = serializers.DateTimeField(required=False, allow_null=True)
    end_time = serializers.DateTimeField(required=False, allow_null=True)
    
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
        return {
            '_timeEntryId': str(data['time_entry_id']),
            '_description': data['description'],
            '_startTime': data['start_time'],
            '_endTime': data['end_time'],
            '_categoryId': data['category_id'],
            '_categoryName': data['category_name']
        }
    
    def validate(self, data):
        if data.get('start_time') and data.get('end_time'):
            if data['start_time'] >= data['end_time']:
                raise serializers.ValidationError("End time must be after start time")
        return data
    
    def create(self, validated_data):
        return TimeEntry.objects.create(
            description=validated_data.get('description'),
            start_time=validated_data.get('start_time'),
            end_time=validated_data.get('end_time'),
            category=validated_data.get('category'),
            user_id=validated_data.get('user_id'),  # Add this line
            is_active=validated_data.get('is_active', True)
    )
