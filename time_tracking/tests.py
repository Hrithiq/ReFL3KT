from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from .models import Category, TimeEntry
from datetime import datetime, timedelta
from django.utils import timezone

User = get_user_model()

class TimeTrackingTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', 
            password='testpass123'
        )
        self.category = Category.objects.create(
            user=self.user,
            name="Test Category",
            color="#FFFFFF"
        )
        self.client.force_authenticate(user=self.user)

    def test_create_time_entry(self):
        url = '/api/time-entries/'
        data = {
            "description": "Test entry",
            "category": self.category.id,
            "start_time": timezone.now().isoformat(),
            "is_active": True
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        entry = TimeEntry.objects.get(description="Test entry")
        self.assertEqual(entry.user, self.user)
        self.assertEqual(entry.category, self.category)
        self.assertTrue(entry.is_active)
        self.assertIsNone(entry.end_time)

    def test_end_time_entry(self):
        # Create an active entry
        start_time = timezone.now()
        entry = TimeEntry.objects.create(
            user=self.user,
            description="Test entry",
            category=self.category,
            start_time=start_time
        )
        print(f"Testing with entry.id = {entry.id}")
        # End the entry
        url = f'/api/time-entries/{entry.id}/end/'
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Refresh from db and verify
        entry.refresh_from_db()
        self.assertFalse(entry.is_active)
        self.assertIsNotNone(entry.end_time)
        self.assertTrue(entry.end_time > entry.start_time)

    def test_active_entry_limit(self):
        # Create first active entry
        start_time = timezone.now()
        TimeEntry.objects.create(
            user=self.user,
            description="Entry 1",
            category=self.category,
            start_time=start_time
        )
        
        # Try to create second active entry
        data = {
            "description": "Entry 2",
            "category": self.category.id,
            "start_time": timezone.now().isoformat()
        }
        response = self.client.post('/api/time-entries/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("already have an active time entry", str(response.content))

    def test_category_creation(self):
        url = '/api/categories/'
        data = {
            "name": "New Category",
            "color": "#FF0000"
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Category.objects.filter(name="New Category").exists())
        category = Category.objects.get(name="New Category")
        self.assertEqual(category.user, self.user)
        self.assertEqual(category.color, "#FF0000")

    def test_time_entry_validation(self):
        url = '/api/time-entries/'
        start_time = timezone.now()
        end_time = start_time - timedelta(hours=1)  # End before start
        data = {
            "description": "Test entry",
            "category": self.category.id,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat()
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("End time must be after start time", str(response.content))

# Run tests with:
# python manage.py test time_tracking
