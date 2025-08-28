"""
Unit tests for the Users API endpoints.
"""

from django.contrib.auth.models import User
from django.urls import reverse

from rest_framework import status

from .test_base import BaseAPITestCase


class UserAPITestCase(BaseAPITestCase):
    """Test cases for User API endpoints."""

    def test_user_list_get(self):
        """Test retrieving list of users."""
        url = reverse("user-list-create")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should include test_user and test_user2 from setUp
        self.assertEqual(len(response.data), 2)

        usernames = [user["username"] for user in response.data]
        self.assertIn("testuser", usernames)
        self.assertIn("testuser2", usernames)

    def test_user_list_empty(self):
        """Test retrieving empty user list."""
        # Delete all users
        User.objects.all().delete()

        url = reverse("user-list-create")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_user_create_success(self):
        """Test creating a new user successfully."""
        url = reverse("user-list-create")
        data = {"username": "newuser", "email": "newuser@example.com"}

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["username"], "newuser")
        self.assertEqual(response.data["email"], "newuser@example.com")

        # Verify user was created in database
        self.assertEqual(User.objects.filter(username="newuser").count(), 1)
        created_user = User.objects.get(username="newuser")
        self.assertEqual(created_user.email, "newuser@example.com")

    def test_user_create_without_email(self):
        """Test creating a user without email."""
        url = reverse("user-list-create")
        data = {"username": "userwithoutemail"}

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["username"], "userwithoutemail")
        self.assertEqual(response.data["email"], "")  # Should be empty string

    def test_user_create_duplicate_username(self):
        """Test creating a user with duplicate username."""
        url = reverse("user-list-create")
        data = {"username": "testuser", "email": "duplicate@example.com"}  # This username already exists from setUp

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("username", response.data)

    def test_user_create_invalid_data(self):
        """Test creating a user with invalid data."""
        url = reverse("user-list-create")
        data = {
            "email": "user@example.com"
            # Missing username
        }

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("username", response.data)

    def test_user_create_empty_username(self):
        """Test creating a user with empty username."""
        url = reverse("user-list-create")
        data = {"username": "", "email": "user@example.com"}

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("username", response.data)

    def test_user_create_invalid_email(self):
        """Test creating a user with invalid email format."""
        url = reverse("user-list-create")
        data = {"username": "testinvalidemail", "email": "invalid-email"}

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    def test_user_serialization_fields(self):
        """Test that user serialization includes only expected fields."""
        url = reverse("user-list-create")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        if response.data:
            user_data = response.data[0]
            expected_fields = ["id", "username", "email"]

            # Check that all expected fields are present
            for field in expected_fields:
                self.assertIn(field, user_data)

            # Check that sensitive fields are not exposed
            sensitive_fields = ["password", "is_staff", "is_superuser", "is_active"]
            for field in sensitive_fields:
                self.assertNotIn(field, user_data)

    def test_user_username_max_length(self):
        """Test user username maximum length validation."""
        url = reverse("user-list-create")

        # Create a username longer than Django's default max_length (150)
        long_username = "x" * 151

        data = {"username": long_username, "email": "user@example.com"}

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("username", response.data)

    def test_user_list_ordering(self):
        """Test that user list is returned in consistent order."""
        # Create additional users with specific usernames for ordering test
        User.objects.create_user(username="aaa_user", email="aaa@example.com")
        User.objects.create_user(username="zzz_user", email="zzz@example.com")

        url = reverse("user-list-create")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 4)  # 2 from setUp + 2 created here

        # Check that users are returned (Django's default ordering by pk)
        user_ids = [user["id"] for user in response.data]
        self.assertEqual(user_ids, sorted(user_ids))  # Should be in ascending order by ID

    def test_user_list_content_type(self):
        """Test that user list returns correct content type."""
        url = reverse("user-list-create")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["content-type"], "application/json")
