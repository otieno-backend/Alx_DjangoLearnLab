from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework.authtoken.models import Token

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

        self.assertNotEqual(
            user.password,
            "testpassword123"
        )

        
        self.assertIn("token", response.data)


class UserLoginTest(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpassword123",
        )

    def test_user_can_login(self):
        data = {
            "username": "testuser",
            "password": "testpassword123",
        }

        response = self.client.post(
            reverse("login"),
            data,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.assertIn("token", response.data)

        self.assertEqual(
            response.data["user"]["username"],
            "testuser"
        )

    def test_user_cannot_login_with_wrong_password(self):
        data = {
            "username": "testuser",
            "password": "wrongpassword",
        }

        response = self.client.post(
            reverse("login"),
            data,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )


class ProfileTest(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpassword123",
            bio="Original bio",
        )

        self.token = Token.objects.create(
            user=self.user
        )

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {self.token.key}"
        )

    def test_authenticated_user_can_view_profile(self):
        response = self.client.get(
            reverse("profile")
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.assertEqual(
            response.data["username"],
            "testuser"
        )

        self.assertEqual(
            response.data["bio"],
            "Original bio"
        )

    def test_authenticated_user_can_update_profile(self):
        data = {
            "bio": "Updated bio",
        }

        response = self.client.put(
            reverse("profile"),
            data,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.user.refresh_from_db()

        self.assertEqual(
            self.user.bio,
            "Updated bio"
        )

    def test_unauthenticated_user_cannot_view_profile(self):
        self.client.credentials()

        response = self.client.get(
            reverse("profile")
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED
        )


class FollowUserTest(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="user1",
            password="password123",
        )

        self.other_user = User.objects.create_user(
            username="user2",
            password="password123",
        )

        self.token = Token.objects.create(
            user=self.user
        )

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {self.token.key}"
        )

    def test_user_can_follow_another_user(self):
        response = self.client.post(
            reverse(
                "follow-user",
                kwargs={"user_id": self.other_user.id}
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.assertTrue(
            self.user.following.filter(
                id=self.other_user.id
            ).exists()
        )

    def test_user_cannot_follow_themselves(self):
        response = self.client.post(
            reverse(
                "follow-user",
                kwargs={"user_id": self.user.id}
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )

        self.assertIn(
            "error",
            response.data
        )

    def test_user_cannot_follow_same_user_twice(self):
        self.user.following.add(self.other_user)

        response = self.client.post(
            reverse(
                "follow-user",
                kwargs={"user_id": self.other_user.id}
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )


class UnfollowUserTest(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="user1",
            password="password123",
        )

        self.other_user = User.objects.create_user(
            username="user2",
            password="password123",
        )

        self.user.following.add(self.other_user)

        self.token = Token.objects.create(
            user=self.user
        )

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {self.token.key}"
        )

    def test_user_can_unfollow_user(self):
        response = self.client.post(
            reverse(
                "unfollow-user",
                kwargs={"user_id": self.other_user.id}
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.assertFalse(
            self.user.following.filter(
                id=self.other_user.id
            ).exists()
        )


class FollowingFollowersTest(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="user1",
            password="password123",
        )

        self.followed_user = User.objects.create_user(
            username="user2",
            password="password123",
        )

        self.follower = User.objects.create_user(
            username="user3",
            password="password123",
        )

        # user1 follows user2
        self.user.following.add(self.followed_user)

        # user3 follows user1
        self.follower.following.add(self.user)

        self.token = Token.objects.create(
            user=self.user
        )

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {self.token.key}"
        )

    def test_following_list(self):
        response = self.client.get(
            reverse("following")
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        usernames = [
            user["username"]
            for user in response.data
        ]

        self.assertIn(
            "user2",
            usernames
        )

    def test_followers_list(self):
        response = self.client.get(
            reverse("followers")
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        usernames = [
            user["username"]
            for user in response.data
        ]

        self.assertIn(
            "user3",
            usernames
        )

    def test_user_following_list(self):
        response = self.client.get(
            reverse(
                "user-following",
                kwargs={"user_id": self.user.id}
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        usernames = [
            user["username"]
            for user in response.data
        ]

        self.assertIn(
            "user2",
            usernames
        )

    def test_user_followers_list(self):
        response = self.client.get(
            reverse(
                "user-followers",
                kwargs={"user_id": self.user.id}
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        usernames = [
            user["username"]
            for user in response.data
        ]

        self.assertIn(
            "user3",
            usernames
        )
