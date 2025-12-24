from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q, Count
from django.utils import timezone
from django.shortcuts import get_object_or_404

from .models import (
    ForumCategory, ForumTag, ForumPost, ForumReply, ForumAttachment,
    ForumLike, ForumMention, ForumNotification, ForumPostTag
)
from .serializers import (
    ForumCategorySerializer, ForumTagSerializer, ForumPostListSerializer,
    ForumPostDetailSerializer, ForumPostCreateSerializer, ForumPostUpdateSerializer,
    ForumReplySerializer, ForumReplyCreateSerializer, ForumReplyUpdateSerializer,
    ForumAttachmentSerializer, ForumLikeSerializer, ForumMentionSerializer,
    ForumNotificationSerializer
)
from .permissions import (
    ForumPublicOrAuthenticatedReadOnly, ForumCategoryPermission,
    ForumPostWritePermission, IsOwnerOrReadOnly, IsAdminOrReadOnly
)
from .utils import extract_mentions, create_mentions


class ForumPagination(PageNumberPagination):
    """Custom pagination for forum endpoints"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class ForumCategoryViewSet(ModelViewSet):
    """ViewSet for ForumCategory"""
    queryset = ForumCategory.objects.filter(is_active=True)
    serializer_class = ForumCategorySerializer
    permission_classes = [ForumCategoryPermission]
    pagination_class = None
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter by public visibility if user is not authenticated
        if not self.request.user.is_authenticated:
            queryset = queryset.filter(is_public_visible=True)
        return queryset.order_by('sort_order', 'name')


class ForumTagViewSet(generics.ListCreateAPIView):
    """ViewSet for ForumTag"""
    queryset = ForumTag.objects.all()
    serializer_class = ForumTagSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = None
    
    def get_queryset(self):
        # Filter by search query if provided
        search = self.request.query_params.get('search', '')
        queryset = super().get_queryset()
        if search:
            queryset = queryset.filter(name__icontains=search)
        return queryset.order_by('-usage_count', 'name')


class ForumPostViewSet(ModelViewSet):
    """ViewSet for ForumPost"""
    queryset = ForumPost.objects.all()
    permission_classes = [ForumPublicOrAuthenticatedReadOnly]
    pagination_class = ForumPagination
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ForumPostListSerializer
        elif self.action == 'create':
            return ForumPostCreateSerializer
        elif self.action == 'update' or self.action == 'partial_update':
            return ForumPostUpdateSerializer
        return ForumPostDetailSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset().select_related('author', 'category').prefetch_related('tags')
        
        # Filter by status
        status_filter = self.request.query_params.get('status', 'published')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by category
        category_id = self.request.query_params.get('category')
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        
        # Filter by tag
        tag_id = self.request.query_params.get('tag')
        if tag_id:
            queryset = queryset.filter(tags__id=tag_id)
        
        # Filter by search query
        search = self.request.query_params.get('search', '')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | Q(content__icontains=search)
            )
        
        # Filter by pinned
        pinned = self.request.query_params.get('pinned')
        if pinned is not None:
            queryset = queryset.filter(is_pinned=pinned.lower() == 'true')
        
        # Filter by featured
        featured = self.request.query_params.get('featured')
        if featured is not None:
            queryset = queryset.filter(is_featured=featured.lower() == 'true')
        
        # Filter by author
        author_id = self.request.query_params.get('author')
        if author_id:
            queryset = queryset.filter(author_id=author_id)
        
        # Public visibility filter
        if not self.request.user.is_authenticated:
            queryset = queryset.filter(is_public_visible=True)
        
        return queryset.distinct()
    
    def retrieve(self, request, *args, **kwargs):
        """Retrieve post and increment view count"""
        instance = self.get_object()
        instance.increment_view_count()
        serializer = self.get_serializer(instance, context={'request': request})
        return Response(serializer.data)
    
    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
        # Extract mentions and create notifications
        post = serializer.instance
        mentioned_usernames = extract_mentions(post.title + ' ' + post.content)
        if mentioned_usernames:
            create_mentions(mentioned_usernames, post.author, post=post)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def like(self, request, pk=None):
        """Like or unlike a post"""
        post = self.get_object()
        user = request.user
        
        like, created = ForumLike.objects.get_or_create(
            user=user,
            post=post,
            defaults={'like_type': 'post'}
        )
        
        if not created:
            # Unlike: delete the like
            like.delete()
            post.like_count = post.likes.count()
            post.save(update_fields=['like_count'])
            return Response({'liked': False, 'like_count': post.like_count})
        
        # Update like count
        post.like_count = post.likes.count()
        post.save(update_fields=['like_count'])
        return Response({'liked': True, 'like_count': post.like_count})
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdminOrReadOnly])
    def pin(self, request, pk=None):
        """Pin or unpin a post (admin only)"""
        post = self.get_object()
        post.is_pinned = not post.is_pinned
        if post.is_pinned:
            post.pinned_at = timezone.now()
        else:
            post.pinned_at = None
        post.save(update_fields=['is_pinned', 'pinned_at'])
        return Response({'pinned': post.is_pinned})
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdminOrReadOnly])
    def feature(self, request, pk=None):
        """Feature or unfeature a post (admin only)"""
        post = self.get_object()
        post.is_featured = not post.is_featured
        post.save(update_fields=['is_featured'])
        return Response({'featured': post.is_featured})


class ForumReplyViewSet(ModelViewSet):
    """ViewSet for ForumReply"""
    queryset = ForumReply.objects.all()
    permission_classes = [ForumPublicOrAuthenticatedReadOnly]
    pagination_class = ForumPagination
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ForumReplyCreateSerializer
        elif self.action == 'update' or self.action == 'partial_update':
            return ForumReplyUpdateSerializer
        return ForumReplySerializer
    
    def get_queryset(self):
        queryset = super().get_queryset().select_related('author', 'post', 'parent_reply', 'quoted_reply')
        
        # Filter by post
        post_id = self.request.query_params.get('post')
        if post_id:
            queryset = queryset.filter(post_id=post_id)
        
        # Filter by parent reply (for nested replies)
        parent_id = self.request.query_params.get('parent')
        if parent_id:
            queryset = queryset.filter(parent_reply_id=parent_id)
        
        # Public visibility filter
        if not self.request.user.is_authenticated:
            queryset = queryset.filter(is_public_visible=True)
        
        return queryset
    
    def perform_create(self, serializer):
        reply = serializer.save(author=self.request.user)
        # Extract mentions and create notifications
        mentioned_usernames = extract_mentions(reply.content)
        if mentioned_usernames:
            create_mentions(mentioned_usernames, reply.author, post=reply.post, reply=reply)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def like(self, request, pk=None):
        """Like or unlike a reply"""
        reply = self.get_object()
        user = request.user
        
        like, created = ForumLike.objects.get_or_create(
            user=user,
            reply=reply,
            defaults={'like_type': 'reply'}
        )
        
        if not created:
            # Unlike: delete the like
            like.delete()
            reply.like_count = reply.likes.count()
            reply.save(update_fields=['like_count'])
            return Response({'liked': False, 'like_count': reply.like_count})
        
        # Update like count
        reply.like_count = reply.likes.count()
        reply.save(update_fields=['like_count'])
        return Response({'liked': True, 'like_count': reply.like_count})


class ForumAttachmentViewSet(generics.ListCreateAPIView):
    """ViewSet for ForumAttachment"""
    queryset = ForumAttachment.objects.all()
    serializer_class = ForumAttachmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = ForumPagination
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by post
        post_id = self.request.query_params.get('post')
        if post_id:
            queryset = queryset.filter(post_id=post_id)
        
        # Filter by reply
        reply_id = self.request.query_params.get('reply')
        if reply_id:
            queryset = queryset.filter(reply_id=reply_id)
        
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def forum_notifications(request):
    """Get user's forum notifications"""
    notifications = ForumNotification.objects.filter(
        recipient=request.user
    ).select_related('actor', 'post', 'reply').order_by('-created_at')
    
    # Filter by read status
    is_read = request.query_params.get('read')
    if is_read is not None:
        notifications = notifications.filter(is_read=is_read.lower() == 'true')
    
    # Pagination
    paginator = ForumPagination()
    page = paginator.paginate_queryset(notifications, request)
    
    if page is not None:
        serializer = ForumNotificationSerializer(page, many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data)
    
    serializer = ForumNotificationSerializer(notifications, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def mark_notification_read(request, notification_id):
    """Mark a notification as read"""
    notification = get_object_or_404(
        ForumNotification,
        id=notification_id,
        recipient=request.user
    )
    notification.is_read = True
    notification.save(update_fields=['is_read'])
    return Response({'success': True})


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def mark_all_notifications_read(request):
    """Mark all user notifications as read"""
    count = ForumNotification.objects.filter(
        recipient=request.user,
        is_read=False
    ).update(is_read=True)
    return Response({'success': True, 'count': count})


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def unread_notification_count(request):
    """Get count of unread notifications"""
    count = ForumNotification.objects.filter(
        recipient=request.user,
        is_read=False
    ).count()
    return Response({'count': count})


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def forum_mentions(request):
    """Get user's mentions"""
    mentions = ForumMention.objects.filter(
        mentioned_user=request.user
    ).select_related('mentioned_by', 'post', 'reply').order_by('-created_at')
    
    # Filter by read status
    is_read = request.query_params.get('read')
    if is_read is not None:
        mentions = mentions.filter(is_read=is_read.lower() == 'true')
    
    # Pagination
    paginator = ForumPagination()
    page = paginator.paginate_queryset(mentions, request)
    
    if page is not None:
        serializer = ForumMentionSerializer(page, many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data)
    
    serializer = ForumMentionSerializer(mentions, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def mark_mention_read(request, mention_id):
    """Mark a mention as read"""
    mention = get_object_or_404(
        ForumMention,
        id=mention_id,
        mentioned_user=request.user
    )
    mention.is_read = True
    mention.save(update_fields=['is_read'])
    return Response({'success': True})

