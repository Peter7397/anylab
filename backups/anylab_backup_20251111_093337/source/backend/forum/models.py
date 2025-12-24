from django.db import models
from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.utils import timezone


class ForumCategory(models.Model):
    """Forum category model"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True, help_text="Icon name or class")
    sort_order = models.IntegerField(default=0, db_index=True)
    is_public_visible = models.BooleanField(default=True, help_text="Visible to non-logged-in users")
    allow_public_post = models.BooleanField(default=False, help_text="Allow non-logged-in users to post")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'forum_categories'
        verbose_name = 'Forum Category'
        verbose_name_plural = 'Forum Categories'
        ordering = ['sort_order', 'name']
    
    def __str__(self):
        return self.name


class ForumTag(models.Model):
    """Forum tag model"""
    name = models.CharField(max_length=50, unique=True)
    color = models.CharField(max_length=7, default='#3B82F6', help_text="Hex color code")
    usage_count = models.IntegerField(default=0, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'forum_tags'
        verbose_name = 'Forum Tag'
        verbose_name_plural = 'Forum Tags'
        ordering = ['-usage_count', 'name']
    
    def __str__(self):
        return self.name


class ForumPost(models.Model):
    """Forum post model"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('locked', 'Locked'),
        ('deleted', 'Deleted'),
    ]
    
    title = models.CharField(max_length=255)
    content = models.TextField()
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='forum_posts')
    category = models.ForeignKey(ForumCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='posts')
    tags = models.ManyToManyField(ForumTag, through='ForumPostTag', related_name='posts', blank=True)
    
    # Status and visibility
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='published', db_index=True)
    is_public_visible = models.BooleanField(default=False, help_text="Visible to non-logged-in users")
    allow_public_reply = models.BooleanField(default=False, help_text="Allow non-logged-in users to reply")
    
    # Management fields
    is_pinned = models.BooleanField(default=False, db_index=True)
    is_featured = models.BooleanField(default=False, db_index=True, help_text="精华帖")
    pinned_at = models.DateTimeField(null=True, blank=True)
    
    # Statistics
    view_count = models.IntegerField(default=0, db_index=True)
    like_count = models.IntegerField(default=0, db_index=True)
    reply_count = models.IntegerField(default=0, db_index=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_reply_at = models.DateTimeField(null=True, blank=True, db_index=True)
    
    class Meta:
        db_table = 'forum_posts'
        verbose_name = 'Forum Post'
        verbose_name_plural = 'Forum Posts'
        ordering = ['-is_pinned', '-last_reply_at', '-created_at']
        indexes = [
            models.Index(fields=['status', 'is_pinned', '-created_at']),
            models.Index(fields=['category', 'status']),
            models.Index(fields=['is_featured', '-created_at']),
        ]
    
    def __str__(self):
        return self.title
    
    def increment_view_count(self):
        """Increment view count atomically"""
        ForumPost.objects.filter(pk=self.pk).update(view_count=models.F('view_count') + 1)
        self.refresh_from_db()


class ForumPostTag(models.Model):
    """Many-to-many relationship between ForumPost and ForumTag"""
    post = models.ForeignKey(ForumPost, on_delete=models.CASCADE, related_name='post_tags')
    tag = models.ForeignKey(ForumTag, on_delete=models.CASCADE, related_name='post_tags')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'forum_post_tags'
        unique_together = ('post', 'tag')
        verbose_name = 'Post Tag'
        verbose_name_plural = 'Post Tags'
    
    def __str__(self):
        return f"{self.post.title} - {self.tag.name}"


class ForumReply(models.Model):
    """Forum reply model"""
    content = models.TextField()
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='forum_replies')
    post = models.ForeignKey(ForumPost, on_delete=models.CASCADE, related_name='replies')
    parent_reply = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='child_replies', help_text="Nested reply")
    quoted_reply = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='quoted_in_replies', help_text="Quoted reply")
    is_public_visible = models.BooleanField(default=False, help_text="Visible to non-logged-in users")
    
    # Statistics
    like_count = models.IntegerField(default=0, db_index=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'forum_replies'
        verbose_name = 'Forum Reply'
        verbose_name_plural = 'Forum Replies'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['post', 'created_at']),
            models.Index(fields=['parent_reply', 'created_at']),
        ]
    
    def __str__(self):
        return f"Reply to {self.post.title} by {self.author.username}"


class ForumAttachment(models.Model):
    """Forum attachment model"""
    post = models.ForeignKey(ForumPost, on_delete=models.CASCADE, null=True, blank=True, related_name='attachments')
    reply = models.ForeignKey(ForumReply, on_delete=models.CASCADE, null=True, blank=True, related_name='attachments')
    file = models.FileField(
        upload_to='forum/attachments/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'txt', 'rtf', 'zip', 'rar', 'jpg', 'jpeg', 'png', 'gif', 'mp4', 'avi', 'mov'])],
    )
    filename = models.CharField(max_length=255)
    file_size = models.BigIntegerField(default=0)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'forum_attachments'
        verbose_name = 'Forum Attachment'
        verbose_name_plural = 'Forum Attachments'
        indexes = [
            models.Index(fields=['post']),
            models.Index(fields=['reply']),
        ]
    
    def __str__(self):
        return self.filename
    
    def save(self, *args, **kwargs):
        if not self.filename and self.file:
            self.filename = self.file.name
        if not self.file_size and self.file:
            try:
                self.file_size = self.file.size
            except:
                pass
        super().save(*args, **kwargs)


class ForumLike(models.Model):
    """Forum like model"""
    LIKE_TYPE_CHOICES = [
        ('post', 'Post'),
        ('reply', 'Reply'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='forum_likes')
    like_type = models.CharField(max_length=10, choices=LIKE_TYPE_CHOICES)
    post = models.ForeignKey(ForumPost, on_delete=models.CASCADE, null=True, blank=True, related_name='likes')
    reply = models.ForeignKey(ForumReply, on_delete=models.CASCADE, null=True, blank=True, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        db_table = 'forum_likes'
        verbose_name = 'Forum Like'
        verbose_name_plural = 'Forum Likes'
        unique_together = [
            ('user', 'post'),
            ('user', 'reply'),
        ]
        indexes = [
            models.Index(fields=['like_type', 'created_at']),
        ]
    
    def __str__(self):
        if self.post:
            return f"{self.user.username} liked {self.post.title}"
        elif self.reply:
            return f"{self.user.username} liked reply to {self.reply.post.title}"
        return f"{self.user.username} liked"


class ForumMention(models.Model):
    """Forum @mention model"""
    mentioned_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='forum_mentions')
    post = models.ForeignKey(ForumPost, on_delete=models.CASCADE, null=True, blank=True, related_name='mentions')
    reply = models.ForeignKey(ForumReply, on_delete=models.CASCADE, null=True, blank=True, related_name='mentions')
    mentioned_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='mentioned_others')
    is_read = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        db_table = 'forum_mentions'
        verbose_name = 'Forum Mention'
        verbose_name_plural = 'Forum Mentions'
        indexes = [
            models.Index(fields=['mentioned_user', 'is_read', '-created_at']),
            models.Index(fields=['post']),
            models.Index(fields=['reply']),
        ]
    
    def __str__(self):
        return f"{self.mentioned_by.username} mentioned {self.mentioned_user.username}"


class ForumNotification(models.Model):
    """Forum notification model"""
    NOTIFICATION_TYPE_CHOICES = [
        ('new_reply', 'New Reply'),
        ('mention', 'Mention'),
        ('like', 'Like'),
        ('quote', 'Quote'),
        ('post_locked', 'Post Locked'),
        ('post_deleted', 'Post Deleted'),
    ]
    
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='forum_notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPE_CHOICES)
    post = models.ForeignKey(ForumPost, on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    reply = models.ForeignKey(ForumReply, on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name='forum_notifications_sent', help_text="User who triggered the notification")
    is_read = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        db_table = 'forum_notifications'
        verbose_name = 'Forum Notification'
        verbose_name_plural = 'Forum Notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'is_read', '-created_at']),
            models.Index(fields=['notification_type']),
        ]
    
    def __str__(self):
        return f"{self.get_notification_type_display()} for {self.recipient.username}"

