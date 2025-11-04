from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    ForumCategory, ForumTag, ForumPost, ForumReply, ForumAttachment,
    ForumLike, ForumMention, ForumNotification, ForumPostTag
)

User = get_user_model()


class UserBasicSerializer(serializers.ModelSerializer):
    """Basic user serializer for nested data"""
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'avatar']
        read_only_fields = fields


class ForumCategorySerializer(serializers.ModelSerializer):
    """Serializer for ForumCategory"""
    post_count = serializers.IntegerField(source='posts.count', read_only=True)
    
    class Meta:
        model = ForumCategory
        fields = ['id', 'name', 'description', 'icon', 'sort_order', 'is_public_visible', 
                  'allow_public_post', 'is_active', 'post_count', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


class ForumTagSerializer(serializers.ModelSerializer):
    """Serializer for ForumTag"""
    class Meta:
        model = ForumTag
        fields = ['id', 'name', 'color', 'usage_count', 'created_at']
        read_only_fields = ['usage_count', 'created_at']


class ForumAttachmentSerializer(serializers.ModelSerializer):
    """Serializer for ForumAttachment"""
    uploaded_by = UserBasicSerializer(read_only=True)
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = ForumAttachment
        fields = ['id', 'file', 'filename', 'file_size', 'uploaded_by', 'uploaded_at', 'file_url']
        read_only_fields = ['uploaded_by', 'uploaded_at']
    
    def get_file_url(self, obj):
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None


class ForumReplySerializer(serializers.ModelSerializer):
    """Serializer for ForumReply"""
    author = UserBasicSerializer(read_only=True)
    quoted_reply = serializers.SerializerMethodField()
    child_replies = serializers.SerializerMethodField()
    attachments = ForumAttachmentSerializer(many=True, read_only=True)
    is_liked = serializers.SerializerMethodField()
    mention_count = serializers.IntegerField(source='mentions.count', read_only=True)
    
    class Meta:
        model = ForumReply
        fields = ['id', 'content', 'author', 'post', 'parent_reply', 'quoted_reply', 
                  'child_replies', 'attachments', 'is_public_visible', 'like_count', 
                  'is_liked', 'mention_count', 'created_at', 'updated_at']
        read_only_fields = ['author', 'like_count', 'created_at', 'updated_at']
    
    def get_quoted_reply(self, obj):
        if obj.quoted_reply:
            return ForumReplySerializer(obj.quoted_reply, context=self.context).data
        return None
    
    def get_child_replies(self, obj):
        child_replies = obj.child_replies.all()
        return ForumReplySerializer(child_replies, many=True, context=self.context).data
    
    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return ForumLike.objects.filter(user=request.user, reply=obj).exists()
        return False


class ForumPostListSerializer(serializers.ModelSerializer):
    """Serializer for ForumPost in list view"""
    author = UserBasicSerializer(read_only=True)
    category = ForumCategorySerializer(read_only=True)
    tags = ForumTagSerializer(many=True, read_only=True)
    last_reply_author = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    
    class Meta:
        model = ForumPost
        fields = ['id', 'title', 'author', 'category', 'tags', 'status', 'is_pinned', 
                  'is_featured', 'is_public_visible', 'view_count', 'like_count', 
                  'reply_count', 'last_reply_at', 'last_reply_author', 'is_liked', 
                  'created_at', 'updated_at']
        read_only_fields = ['view_count', 'like_count', 'reply_count', 'created_at', 
                           'updated_at', 'last_reply_at']
    
    def get_last_reply_author(self, obj):
        last_reply = obj.replies.order_by('-created_at').first()
        if last_reply:
            return UserBasicSerializer(last_reply.author).data
        return None
    
    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return ForumLike.objects.filter(user=request.user, post=obj).exists()
        return False


class ForumPostDetailSerializer(serializers.ModelSerializer):
    """Serializer for ForumPost in detail view"""
    author = UserBasicSerializer(read_only=True)
    category = ForumCategorySerializer(read_only=True)
    tags = ForumTagSerializer(many=True, read_only=True)
    replies = ForumReplySerializer(many=True, read_only=True)
    attachments = ForumAttachmentSerializer(many=True, read_only=True)
    is_liked = serializers.SerializerMethodField()
    
    class Meta:
        model = ForumPost
        fields = ['id', 'title', 'content', 'author', 'category', 'tags', 'status', 
                  'is_pinned', 'is_featured', 'is_public_visible', 'allow_public_reply',
                  'view_count', 'like_count', 'reply_count', 'replies', 'attachments',
                  'is_liked', 'created_at', 'updated_at', 'last_reply_at']
        read_only_fields = ['author', 'view_count', 'like_count', 'reply_count', 
                           'created_at', 'updated_at', 'last_reply_at']
    
    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return ForumLike.objects.filter(user=request.user, post=obj).exists()
        return False


class ForumPostCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating ForumPost"""
    tag_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )
    
    class Meta:
        model = ForumPost
        fields = ['title', 'content', 'category', 'tag_ids', 'is_public_visible', 
                  'allow_public_reply', 'status']
    
    def create(self, validated_data):
        tag_ids = validated_data.pop('tag_ids', [])
        post = ForumPost.objects.create(**validated_data)
        if tag_ids:
            tags = ForumTag.objects.filter(id__in=tag_ids)
            for tag in tags:
                ForumPostTag.objects.create(post=post, tag=tag)
                tag.usage_count += 1
                tag.save()
        return post


class ForumPostUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating ForumPost"""
    tag_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )
    
    class Meta:
        model = ForumPost
        fields = ['title', 'content', 'category', 'tag_ids', 'is_public_visible', 
                  'allow_public_reply', 'status']
    
    def update(self, instance, validated_data):
        tag_ids = validated_data.pop('tag_ids', None)
        
        # Update basic fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Update tags if provided
        if tag_ids is not None:
            # Remove old tags
            ForumPostTag.objects.filter(post=instance).delete()
            # Add new tags
            if tag_ids:
                tags = ForumTag.objects.filter(id__in=tag_ids)
                for tag in tags:
                    ForumPostTag.objects.create(post=instance, tag=tag)
                    tag.usage_count += 1
                    tag.save()
        
        instance.save()
        return instance


class ForumReplyCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating ForumReply"""
    class Meta:
        model = ForumReply
        fields = ['content', 'post', 'parent_reply', 'quoted_reply', 'is_public_visible']
    
    def validate(self, data):
        # Ensure either parent_reply or post is set
        if not data.get('post') and not data.get('parent_reply'):
            raise serializers.ValidationError("Either 'post' or 'parent_reply' must be provided")
        
        # If parent_reply is set, use its post
        if data.get('parent_reply'):
            data['post'] = data['parent_reply'].post
        
        return data


class ForumReplyUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating ForumReply"""
    class Meta:
        model = ForumReply
        fields = ['content', 'is_public_visible']


class ForumLikeSerializer(serializers.ModelSerializer):
    """Serializer for ForumLike"""
    user = UserBasicSerializer(read_only=True)
    
    class Meta:
        model = ForumLike
        fields = ['id', 'user', 'like_type', 'post', 'reply', 'created_at']
        read_only_fields = ['user', 'created_at']


class ForumMentionSerializer(serializers.ModelSerializer):
    """Serializer for ForumMention"""
    mentioned_user = UserBasicSerializer(read_only=True)
    mentioned_by = UserBasicSerializer(read_only=True)
    
    class Meta:
        model = ForumMention
        fields = ['id', 'mentioned_user', 'mentioned_by', 'post', 'reply', 
                  'is_read', 'created_at']
        read_only_fields = ['is_read', 'created_at']


class ForumNotificationSerializer(serializers.ModelSerializer):
    """Serializer for ForumNotification"""
    actor = UserBasicSerializer(read_only=True)
    post_title = serializers.CharField(source='post.title', read_only=True)
    
    class Meta:
        model = ForumNotification
        fields = ['id', 'notification_type', 'actor', 'post', 'post_title', 'reply', 
                  'is_read', 'created_at']
        read_only_fields = ['is_read', 'created_at']

