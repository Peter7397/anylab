from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ForumCategoryViewSet, ForumTagViewSet, ForumPostViewSet, ForumReplyViewSet,
    ForumAttachmentViewSet, forum_notifications, mark_notification_read,
    mark_all_notifications_read, unread_notification_count, forum_mentions,
    mark_mention_read
)

router = DefaultRouter()
router.register(r'categories', ForumCategoryViewSet, basename='forum-category')
router.register(r'posts', ForumPostViewSet, basename='forum-post')
router.register(r'replies', ForumReplyViewSet, basename='forum-reply')

urlpatterns = [
    # Router URLs
    path('', include(router.urls)),
    
    # Tags endpoint (using ListCreateAPIView, not ViewSet)
    path('tags/', ForumTagViewSet.as_view(), name='forum-tag-list'),
    
    # Attachments endpoint (using ListCreateAPIView, not ViewSet)
    path('attachments/', ForumAttachmentViewSet.as_view(), name='forum-attachment-list'),
    
    # Notification endpoints
    path('notifications/', forum_notifications, name='forum-notifications'),
    path('notifications/<int:notification_id>/read/', mark_notification_read, name='forum-notification-read'),
    path('notifications/read-all/', mark_all_notifications_read, name='forum-notifications-read-all'),
    path('notifications/unread-count/', unread_notification_count, name='forum-notifications-unread-count'),
    
    # Mention endpoints
    path('mentions/', forum_mentions, name='forum-mentions'),
    path('mentions/<int:mention_id>/read/', mark_mention_read, name='forum-mention-read'),
]

