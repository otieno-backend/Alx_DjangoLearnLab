from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    PostViewSet,
    CommentViewSet,
    LikePostView,
    UnlikePostView,
)


router = DefaultRouter()

router.register(r"comments", CommentViewSet, basename="comment")
router.register(r"", PostViewSet, basename="post")


urlpatterns = [
    path("", include(router.urls)),

    path(
        "<int:post_id>/like/",
        LikePostView.as_view(),
        name="like",
    ),

    path(
        "<int:post_id>/unlike/",
        UnlikePostView.as_view(),
        name="unlike",
    ),
]
