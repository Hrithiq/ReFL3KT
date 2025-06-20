from django.test import TestCase
from rest_framework.test import APITestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Goal, Task
from time_tracking.models import Category, TimeEntry
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

# Create your tests here.

class GoalAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.user_id = self.user.id
        
        # Create categories
        self.category1 = Category.objects.create(user=self.user, name="Study", color="#FF0000")
        self.category2 = Category.objects.create(user=self.user, name="Work", color="#00FF00")
        
        # Create goal hierarchy
        self.goal_a = Goal.objects.create(user=self.user, name="Goal A", priority="high")
        self.goal_b = Goal.objects.create(user=self.user, name="Goal B", parent=self.goal_a, priority="medium")
        self.goal_c = Goal.objects.create(user=self.user, name="Goal C", parent=self.goal_a, priority="medium")
        
        # Create tasks
        self.task1 = Task.objects.create(
            goal=self.goal_a,
            title="Task 1",
            category=self.category1,
            estimated_time=60
        )
        self.task2 = Task.objects.create(
            goal=self.goal_a,
            title="Task 2", 
            category=self.category2,
            estimated_time=90
        )
        self.task3 = Task.objects.create(
            goal=self.goal_b,
            title="Task 3",
            category=self.category1,
            estimated_time=120
        )

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

    def test_goal_analytics(self):
        # Create time entries for tasks
        start_time = timezone.now() - timedelta(hours=2)
        end_time = timezone.now() - timedelta(hours=1)
        
        # Time entry for task1 (1 hour)
        TimeEntry.objects.create(
            user=self.user,
            category=self.category1,
            description="Study session",
            start_time=start_time,
            end_time=end_time
        )
        
        # Time entry for task3 (30 minutes)
        start_time2 = timezone.now() - timedelta(hours=1)
        end_time2 = timezone.now() - timedelta(minutes=30)
        TimeEntry.objects.create(
            user=self.user,
            category=self.category1,
            description="Work session",
            start_time=start_time2,
            end_time=end_time2
        )
        
        url = f'/api/users/{self.user_id}/goals/{self.goal_a.id}/analytics/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('immediate_children', response.data)
        self.assertIn('total_time_spent', response.data)
        
        # Check that subgoals and tasks are included
        children = response.data['immediate_children']
        self.assertIn('Goal B', children)  # Subgoal
        self.assertIn('Goal C', children)  # Subgoal
        self.assertIn('Task 1', children)  # Task
        self.assertIn('Task 2', children)  # Task
        
        # Goal B should have time from task3 (30 minutes = 0.5 hours)
        self.assertAlmostEqual(children['Goal B'], 0.5, places=1)
        
        # Goal C should have 0 time (no tasks)
        self.assertEqual(children['Goal C'], 0)
        
        # Task 1 should have 1 hour (60 minutes)
        self.assertAlmostEqual(children['Task 1'], 60.0, places=1)
        
        # Task 2 should have 0 time (no time entries)
        self.assertEqual(children['Task 2'], 0)
