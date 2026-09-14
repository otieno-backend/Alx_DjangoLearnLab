from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework.authtoken.models import Token

from accounts.models import User
from notifications.models import Notification

from .models import Post, Comment, Like


class PostTestSetup(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="user1",
            email="user1@example.com",
            password="password123",
        )

        self.other_user = User.objects.create_user(
            username="user2",
            email="user2@example.com",
            password="password123",
        )

        self.token = Token.objects.create(
            user=self.user
        )

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {self.token.key}"
        )

        self.post = Post.objects.create(
            author=self.user,
            title="Test Post",
            content="This is a test post.",
        )


class PostCRUDTests(PostTestSetup):

    def test_authenticated_user_can_create_post(self):
        data = {
            "title": "New Post",
            "content": "This is new post content.",
        }

        response = self.client.post(
            reverse("post-list"),
            data,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED
        )

        self.assertTrue(
            Post.objects.filter(
                title="New Post"
            ).exists()
        )

        post = Post.objects.get(title="New Post")

        self.assertEqual(
            post.author,
            self.user
        )

    def test_unauthenticated_user_cannot_create_post(self):
        self.client.credentials()

        data = {
            "title": "New Post",
            "content": "New content.",
        }

        response = self.client.post(
            reverse("post-list"),
            data,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED
        )

    def test_user_can_list_posts(self):
        response = self.client.get(
            reverse("post-list")
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        # Pagination returns results inside "results".
        self.assertIn(
            "results",
            response.data
        )

        self.assertEqual(
            len(response.data["results"]),
            1
        )

    def test_user_can_retrieve_post(self):
        response = self.client.get(
            reverse(
                "post-detail",
                kwargs={"pk": self.post.id}
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.assertEqual(
            response.data["title"],
            "Test Post"
        )

        self.assertEqual(
            response.data["author"],
            "user1"
        )

    def test_author_can_update_post(self):
        data = {
            "title": "Updated Post",
            "content": "Updated content.",
        }

        response = self.client.put(
            reverse(
                "post-detail",
                kwargs={"pk": self.post.id}
            ),
            data,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.post.refresh_from_db()

        self.assertEqual(
            self.post.title,
            "Updated Post"
        )

        self.assertEqual(
            self.post.content,
            "Updated content."
        )

    def test_non_author_cannot_update_post(self):
        other_token = Token.objects.create(
            user=self.other_user
        )

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {other_token.key}"
        )

        data = {
            "title": "Unauthorized Update",
            "content": "This should not work.",
        }

        response = self.client.put(
            reverse(
                "post-detail",
                kwargs={"pk": self.post.id}
            ),
            data,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN
        )

    def test_author_can_delete_post(self):
        response = self.client.delete(
            reverse(
                "post-detail",
                kwargs={"pk": self.post.id}
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT
        )

        self.assertFalse(
            Post.objects.filter(
                id=self.post.id
            ).exists()
        )

    def test_non_author_cannot_delete_post(self):
        other_token = Token.objects.create(
            user=self.other_user
        )

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {other_token.key}"
        )

        response = self.client.delete(
            reverse(
                "post-detail",
                kwargs={"pk": self.post.id}
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN
        )


class PostValidationTests(PostTestSetup):

    def test_post_title_cannot_be_empty(self):
        data = {
            "title": "   ",
            "content": "Valid content.",
        }

        response = self.client.post(
            reverse("post-list"),
            data,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )

        self.assertIn(
            "title",
            response.data
        )

    def test_post_content_cannot_be_empty(self):
        data = {
            "title": "Valid title",
            "content": "   ",
        }

        response = self.client.post(
            reverse("post-list"),
            data,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )

        self.assertIn(
            "content",
            response.data
        )


class PostSearchTests(PostTestSetup):

    def test_posts_can_be_searched_by_title(self):
        Post.objects.create(
            author=self.user,
            title="Django Testing",
            content="Learning Django tests.",
        )

        response = self.client.get(
            reverse("post-list"),
            {"search": "Django"}
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.assertIn(
            "results",
            response.data
        )

        titles = [
            post["title"]
            for post in response.data["results"]
        ]

        self.assertIn(
            "Django Testing",
            titles
        )


class CommentTests(PostTestSetup):

    def test_authenticated_user_can_create_comment(self):
        data = {
            "post": self.post.id,
            "content": "This is a comment.",
        }

        response = self.client.post(
            reverse("comment-list"),
            data,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED
        )

        self.assertTrue(
            Comment.objects.filter(
                post=self.post,
                author=self.user,
                content="This is a comment.",
            ).exists()
        )

    def test_comment_author_is_set_automatically(self):
        data = {
            "post": self.post.id,
            "content": "My comment.",
        }

        response = self.client.post(
            reverse("comment-list"),
            data,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED
        )

        comment = Comment.objects.get(
            content="My comment."
        )

        self.assertEqual(
            comment.author,
            self.user
        )

    def test_unauthenticated_user_cannot_create_comment(self):
        self.client.credentials()

        data = {
            "post": self.post.id,
            "content": "Unauthorized comment.",
        }

        response = self.client.post(
            reverse("comment-list"),
            data,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED
        )

    def test_comment_content_cannot_be_empty(self):
        data = {
            "post": self.post.id,
            "content": "   ",
        }

        response = self.client.post(
            reverse("comment-list"),
            data,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )

        self.assertIn(
            "content",
            response.data
        )

    def test_comments_can_be_filtered_by_post(self):
        other_post = Post.objects.create(
            author=self.user,
            title="Other Post",
            content="Other content.",
        )

        Comment.objects.create(
            post=self.post,
            author=self.user,
            content="Comment on first post.",
        )

        Comment.objects.create(
            post=other_post,
            author=self.user,
            content="Comment on second post.",
        )

        response = self.client.get(
            reverse("comment-list"),
            {"post": self.post.id}
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.assertIn(
            "results",
            response.data
        )

        self.assertEqual(
            len(response.data["results"]),
            1
        )

        self.assertEqual(
            response.data["results"][0]["content"],
            "Comment on first post."
        )

    def test_comment_author_can_update_comment(self):
        comment = Comment.objects.create(
            post=self.post,
            author=self.user,
            content="Original comment.",
        )

        data = {
            "post": self.post.id,
            "content": "Updated comment.",
        }

        response = self.client.put(
            reverse(
                "comment-detail",
                kwargs={"pk": comment.id}
            ),
            data,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        comment.refresh_from_db()

        self.assertEqual(
            comment.content,
            "Updated comment."
        )

    def test_non_author_cannot_update_comment(self):
        comment = Comment.objects.create(
            post=self.post,
            author=self.user,
            content="Original comment.",
        )

        other_token = Token.objects.create(
            user=self.other_user
        )

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {other_token.key}"
        )

        data = {
            "post": self.post.id,
            "content": "Unauthorized update.",
        }

        response = self.client.put(
            reverse(
                "comment-detail",
                kwargs={"pk": comment.id}
            ),
            data,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN
        )

    def test_comment_author_can_delete_comment(self):
        comment = Comment.objects.create(
            post=self.post,
            author=self.user,
            content="Delete me.",
        )

        response = self.client.delete(
            reverse(
                "comment-detail",
                kwargs={"pk": comment.id}
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT
        )

        self.assertFalse(
            Comment.objects.filter(
                id=comment.id
            ).exists()
        )

class LikeTests(PostTestSetup):

    def test_user_can_like_post(self):
        response = self.client.post(
            reverse(
                "like",
                kwargs={"post_id": self.post.id}
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED
        )

        self.assertTrue(
            Like.objects.filter(
                user=self.user,
                post=self.post
            ).exists()
        )

    def test_user_cannot_like_post_twice(self):
        Like.objects.create(
            user=self.user,
            post=self.post
        )

        response = self.client.post(
            reverse(
                "like",
                kwargs={"post_id": self.post.id}
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )

        self.assertEqual(
            Like.objects.filter(
                user=self.user,
                post=self.post
            ).count(),
            1
        )

    def test_unauthenticated_user_cannot_like_post(self):
        self.client.credentials()

        response = self.client.post(
            reverse(
                "like",
                kwargs={"post_id": self.post.id}
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED
        )

    def test_user_can_unlike_post(self):
        Like.objects.create(
            user=self.user,
            post=self.post
        )

        response = self.client.delete(
            reverse(
                "unlike",
                kwargs={"post_id": self.post.id}
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.assertFalse(
            Like.objects.filter(
                user=self.user,
                post=self.post
            ).exists()
        )

    def test_user_cannot_unlike_post_without_like(self):
        response = self.client.delete(
            reverse(
                "unlike",
                kwargs={"post_id": self.post.id}
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )

    def test_like_creates_notification(self):
        # Use another user so recipient != actor.
        other_token = Token.objects.create(
            user=self.other_user
        )

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {other_token.key}"
        )

        response = self.client.post(
            reverse(
                "like",
                kwargs={"post_id": self.post.id}
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED
        )

        self.assertTrue(
            Notification.objects.filter(
                recipient=self.post.author,
                actor=self.other_user,
                verb="liked your post",
                target_object_id=self.post.id,
            ).exists()
        )

    def test_unlike_removes_like_notification(self):
        # Use another user so a notification is actually created.
        other_token = Token.objects.create(
            user=self.other_user
        )

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {other_token.key}"
        )

        self.client.post(
            reverse(
                "like",
                kwargs={"post_id": self.post.id}
            )
        )

        self.assertTrue(
            Notification.objects.filter(
                recipient=self.post.author,
                actor=self.other_user,
                verb="liked your post",
                target_object_id=self.post.id,
            ).exists()
        )

        response = self.client.delete(
            reverse(
                "unlike",
                kwargs={"post_id": self.post.id}
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.assertFalse(
            Notification.objects.filter(
                recipient=self.post.author,
                actor=self.other_user,
                verb="liked your post",
                target_object_id=self.post.id,
            ).exists()
        )
