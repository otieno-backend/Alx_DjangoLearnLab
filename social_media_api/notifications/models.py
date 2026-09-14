from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models


class Notification(models.Model):
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications_sent",
    )
    verb = models.CharField(max_length=255)

    target_content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
    )
    target_object_id = models.PositiveBigIntegerField()

    target = GenericForeignKey(
        "target_content_type",
        "target_object_id",
    )

    timestamp = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)

    class Meta:
        ordering = ["read", "-timestamp"]

    def __str__(self):
        return f"{self.actor} {self.verb} for {self.recipient}"
