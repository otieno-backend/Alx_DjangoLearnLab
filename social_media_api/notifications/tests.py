
# Create your tests here.
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from notifications.models import Notification
from notifications.utils import create_notification
from notifications.tasks import notify_followers
from posts.models import Post


User = get_user_model()


class NotificationUtilityTests(APITestCase):
    def setUp(self):
        self.actor = User.objects.create_user(
            username="actor",
            password="password123",
        )

        self.recipient = User.objects.create_user(
            username="recipient",
            password="password123",
        )

        self.post = Post.objects.create(
            author=self.actor,
            title="Test Post",
            content="Test content",
        )

    def test_create_notification(self):
        notification = create_notification(
            recipient=self.recipient,
            actor=self.actor,
            verb="liked your post",
            target=self.post,
        )

        self.assertIsNotNone(notification)
        self.assertEqual(notification.recipient, self.recipient)
        self.assertEqual(notification.actor, self.actor)
        self.assertEqual(notification.verb, "liked your post")
        self.assertEqual(notification.target, self.post)
        self.assertFalse(notification.read)

    def test_actor_does_not_receive_own_notification(self):
        notification = create_notification(
            recipient=self.actor,
            actor=self.actor,
            verb="liked your post",
            target=self.post,
        )

        self.assertIsNone(notification)
        self.assertEqual(Notification.objects.count(), 0)

    def test_notification_uses_correct_content_type(self):
        notification = create_notification(
            recipient=self.recipient,
            actor=self.actor,
            verb="liked your post",
            target=self.post,
        )

        expected_content_type = ContentType.objects.get_for_model(
            self.post
        )

        self.assertEqual(
            notification.target_content_type,
            expected_content_type,
        )
        self.assertEqual(
            notification.target_object_id,
            self.post.id,
        )


class NotificationListTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="user",
            password="password123",
        )

        self.actor = User.objects.create_user(
            username="actor",
            password="password123",
        )

        self.post = Post.objects.create(
            author=self.actor,
            title="Test Post",
            content="Test content",
        )

        self.client.force_authenticate(user=self.user)

    def test_authenticated_user_can_list_notifications(self):
        Notification.objects.create(
            recipient=self.user,
            actor=self.actor,
            verb="liked your post",
            target_content_type=ContentType.objects.get_for_model(
                self.post
            ),
            target_object_id=self.post.id,
        )

        response = self.client.get(
            reverse("notification-list")
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(response.data["unread_count"], 1)
        self.assertEqual(len(response.data["notifications"]), 1)

        notification = response.data["notifications"][0]

        self.assertEqual(notification["actor"], "actor")
        self.assertEqual(notification["verb"], "liked your post")
        self.assertFalse(notification["read"])
        self.assertEqual(notification["target_type"], "post")
        self.assertEqual(notification["target_id"], self.post.id)

    def test_user_only_sees_their_own_notifications(self):
        other_user = User.objects.create_user(
            username="other",
            password="password123",
        )

        Notification.objects.create(
            recipient=self.user,
            actor=self.actor,
            verb="liked your post",
            target_content_type=ContentType.objects.get_for_model(
                self.post
            ),
            target_object_id=self.post.id,
        )

        Notification.objects.create(
            recipient=other_user,
            actor=self.actor,
            verb="liked your post",
            target_content_type=ContentType.objects.get_for_model(
                self.post
            ),
            target_object_id=self.post.id,
        )

        response = self.client.get(
            reverse("notification-list")
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(response.data["unread_count"], 1)
        self.assertEqual(len(response.data["notifications"]), 1)

    def test_unread_count_is_correct(self):
        content_type = ContentType.objects.get_for_model(self.post)

        Notification.objects.create(
            recipient=self.user,
            actor=self.actor,
            verb="liked your post",
            target_content_type=content_type,
            target_object_id=self.post.id,
            read=False,
        )

        Notification.objects.create(
            recipient=self.user,
            actor=self.actor,
            verb="commented on your post",
            target_content_type=content_type,
            target_object_id=self.post.id,
            read=True,
        )

        response = self.client.get(
            reverse("notification-list")
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(response.data["unread_count"], 1)


class MarkNotificationReadTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="user",
            password="password123",
        )

        self.other_user = User.objects.create_user(
            username="other",
            password="password123",
        )

        self.actor = User.objects.create_user(
            username="actor",
            password="password123",
        )

        self.post = Post.objects.create(
            author=self.actor,
            title="Test Post",
            content="Test content",
        )

        self.notification = Notification.objects.create(
            recipient=self.user,
            actor=self.actor,
            verb="liked your post",
            target_content_type=ContentType.objects.get_for_model(
                self.post
            ),
            target_object_id=self.post.id,
        )

        self.client.force_authenticate(user=self.user)

    def test_user_can_mark_notification_as_read(self):
        response = self.client.patch(
            reverse(
                "notification-read",
                kwargs={"notification_id": self.notification.id},
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.notification.refresh_from_db()

        self.assertTrue(self.notification.read)

    def test_user_cannot_mark_another_users_notification_as_read(self):
        other_notification = Notification.objects.create(
            recipient=self.other_user,
            actor=self.actor,
            verb="liked your post",
            target_content_type=ContentType.objects.get_for_model(
                self.post
            ),
            target_object_id=self.post.id,
        )

        response = self.client.patch(
            reverse(
                "notification-read",
                kwargs={
                    "notification_id": other_notification.id,
                },
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

        other_notification.refresh_from_db()

        self.assertFalse(other_notification.read)

    def test_marking_nonexistent_notification_returns_404(self):
        response = self.client.patch(
            reverse(
                "notification-read",
                kwargs={"notification_id": 99999},
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_unauthenticated_user_cannot_list_notifications(self):
        self.client.force_authenticate(user=None)

        response = self.client.get(
            reverse("notification-list")
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_unauthenticated_user_cannot_mark_notification_read(self):
        self.client.force_authenticate(user=None)

        response = self.client.patch(
            reverse(
                "notification-read",
                kwargs={"notification_id": self.notification.id},
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )


class NotifyFollowersTaskTests(APITestCase):
    def setUp(self):
        self.author = User.objects.create_user(
            username="author",
            password="password123",
        )

        self.follower1 = User.objects.create_user(
            username="follower1",
            password="password123",
        )

        self.follower2 = User.objects.create_user(
            username="follower2",
            password="password123",
        )

        self.post = Post.objects.create(
            author=self.author,
            title="New Post",
            content="New post content",
        )

        self.author.followers.add(
            self.follower1,
            self.follower2,
        )

    def test_notify_followers_creates_notifications(self):
        notify_followers(self.post.id)

        self.assertEqual(
            Notification.objects.count(),
            2,
        )

        self.assertTrue(
            Notification.objects.filter(
                recipient=self.follower1,
                actor=self.author,
                verb="created a new post",
                target_object_id=self.post.id,
            ).exists()
        )

        self.assertTrue(
            Notification.objects.filter(
                recipient=self.follower2,
                actor=self.author,
                verb="created a new post",
                target_object_id=self.post.id,
            ).exists()
        )

    def test_post_author_does_not_receive_notification(self):
        self.author.followers.add(self.author)

        notify_followers(self.post.id)

        self.assertFalse(
            Notification.objects.filter(
                recipient=self.author,
            ).exists()
        )

    def test_notify_followers_with_invalid_post_id(self):
        notify_followers(99999)

        self.assertEqual(
            Notification.objects.count(),
            0,
        )
