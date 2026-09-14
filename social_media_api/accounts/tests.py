from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import User


class UserRegistrationTest(APITestCase):

    def test_user_can_register(self):
        data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpassword123",
            "bio": "Test user",
        }

        response = self.client.post(
            reverse("register"),
            data,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED
        )

        self.assertTrue(
            User.objects.filter(username="testuser").exists()
        )

        user = User.objects.get(username="testuser")

        self.assertEqual(user.email, "test@example.com")
        self.assertEqual(user.bio, "Test user")

        # Password should be hashed, not stored as plain text.
        self.assertNotEqual(
            user.password,
            "testpassword123"
        )

        # Registration should return an authentication token.
        self.assertIn("token", response.data)
        