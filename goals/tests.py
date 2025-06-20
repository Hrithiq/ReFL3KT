from django.test import TestCase
from rest_framework.test import APITestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Goal

User = get_user_model()

# Create your tests here.

class GoalAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.user_id = self.user.id

    def test_create_goal_for_user(self):
        url = f'/api/users/{self.user_id}/goals/'
        data = {
            "name": "Test API Goal",
            "description": "Created via API test",
            "priority": "high",
            "deadline": "2024-12-31T23:59:59Z"
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['name'], data['name'])
        self.assertEqual(response.data['description'], data['description'])
        self.assertEqual(response.data['priority'], data['priority'])
        self.assertEqual(response.data['user'], self.user_id)
