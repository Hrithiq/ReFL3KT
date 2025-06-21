"""
User API Tests

This module contains comprehensive tests for the user creation and retrieval endpoints.
Tests cover both successful operations and error handling scenarios.

Endpoints tested:
- POST /api/create/ - Create a new user
- GET /api/<user_id>/ - Get user details by ID

To run these tests:
    python manage.py test users
"""

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from rest_framework import status
from django.utils import timezone

class UserCreationTests(APITestCase):
    """
    Test suite for user creation endpoint (POST /api/create/)
    
    Tests cover:
    - Successful user creation with valid data
    - Password validation and confirmation
    - Duplicate username handling
    - Required field validation
    """
    
    def setUp(self):
        """Set up test data for user creation tests"""
        self.user = User.objects.create_user(
            username='testuser',
            first_name='Test',
            last_name='User',
            email='test@example.com',
            password='testpass123'
        )
        self.user_id = self.user.id

    def test_create_user_success(self):
        """
        Test successful user creation via API
        
        Verifies:
        - User is created with correct data
        - Response contains all expected fields
        - User is actually saved to database
        - Default values are set correctly
        """
        url = '/api/create/'
        data = {
            'username': 'newuser',
            'first_name': 'New',
            'last_name': 'User',
            'email': 'new@example.com',
            'password': 'testpass123',
            'password_confirm': 'testpass123'
        }
        
        response = self.client.post(url, data, format='json')
        
        # Verify response status and data
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['username'], 'newuser')
        self.assertEqual(response.data['first_name'], 'New')
        self.assertEqual(response.data['last_name'], 'User')
        self.assertEqual(response.data['email'], 'new@example.com')
        self.assertFalse(response.data['is_staff'])
        self.assertTrue(response.data['is_active'])
        self.assertIn('id', response.data)
        self.assertIn('date_joined', response.data)
        
        # Verify user was actually created in database
        user = User.objects.get(username='newuser')
        self.assertEqual(user.first_name, 'New')
        self.assertEqual(user.last_name, 'User')
        self.assertEqual(user.email, 'new@example.com')
    
    def test_create_user_password_mismatch(self):
        """
        Test user creation with mismatched passwords
        
        Verifies that the API correctly rejects requests where
        password and password_confirm don't match.
        """
        url = '/api/create/'
        data = {
            'username': 'testuser',
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'test@example.com',
            'password': 'testpass123',
            'password_confirm': 'differentpass'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Passwords don\'t match', str(response.data))
    
    def test_create_user_duplicate_username(self):
        """
        Test user creation with duplicate username
        
        Verifies that the API correctly rejects requests to create
        users with usernames that already exist.
        """
        # Try to create second user with same username
        url = '/api/create/'
        data = {
            'username': 'testuser',
            'first_name': 'Test2',
            'last_name': 'User2',
            'email': 'test2@example.com',
            'password': 'testpass123',
            'password_confirm': 'testpass123'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username', response.data['details'])
    
    def test_create_user_missing_required_fields(self):
        """
        Test user creation with missing required fields
        
        Verifies that the API correctly rejects requests that are
        missing required fields (first_name, last_name, email).
        """
        url = '/api/create/'
        data = {
            'username': 'testuser',
            'password': 'testpass123',
            'password_confirm': 'testpass123'
            # Missing first_name, last_name, email
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('first_name', response.data['details'])
        self.assertIn('last_name', response.data['details'])
        self.assertIn('email', response.data['details'])

class UserDetailsTests(APITestCase):
    """
    Test suite for user details retrieval endpoint (GET /api/<user_id>/)
    
    Tests cover:
    - Successful user details retrieval
    - Handling of non-existent users
    - Handling of invalid user IDs
    """
    
    def setUp(self):
        """Set up test data for user details tests"""
        self.user = User.objects.create_user(
            username='testuser',
            first_name='Test',
            last_name='User',
            email='test@example.com',
            password='testpass123',
            is_staff=True,
            is_active=True
        )
        self.user_id = self.user.id

    def test_get_user_details_success(self):
        """
        Test successful user details retrieval via API
        
        Verifies:
        - User details are returned correctly
        - All expected fields are present
        - Field values match the database
        """
        url = f'/api/{self.user_id}/'
        
        response = self.client.get(url)
        
        # Verify response status and data
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.user_id)
        self.assertEqual(response.data['username'], 'testuser')
        self.assertEqual(response.data['first_name'], 'Test')
        self.assertEqual(response.data['last_name'], 'User')
        self.assertEqual(response.data['email'], 'test@example.com')
        self.assertTrue(response.data['is_staff'])
        self.assertTrue(response.data['is_active'])
        self.assertFalse(response.data['is_superuser'])
        self.assertIn('date_joined', response.data)
        self.assertIn('last_login', response.data)

    def test_get_user_details_not_found(self):
        """
        Test user details retrieval for non-existent user
        
        Verifies that the API returns a 404 status when
        trying to retrieve details for a user that doesn't exist.
        """
        url = '/api/99999/'  # Non-existent user ID
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_user_details_invalid_id(self):
        """
        Test user details retrieval with invalid user ID
        
        Verifies that the API handles invalid user IDs (non-integer)
        gracefully and returns appropriate error responses.
        """
        url = '/api/abc/'  # Invalid user ID (not an integer)
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
