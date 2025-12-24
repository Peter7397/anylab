from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from .models import ForumPost, ForumReply, ForumLike, ForumNotification
from .utils import extract_mentions, create_mentions, create_notification


@receiver(post_save, sender=ForumPost)
def forum_post_saved(sender, instance, created, **kwargs):
    """Handle forum post creation/update"""
    if created:
        # Extract mentions from content
        mentioned_usernames = extract_mentions(instance.title + ' ' + instance.content)
        if mentioned_usernames:
            create_mentions(mentioned_usernames, instance.author, post=instance)
    else:
        # Update last_reply_at if status changed
        if instance.status == 'published':
            # Check if we need to update pinned_at
            if instance.is_pinned and not instance.pinned_at:
                instance.pinned_at = timezone.now()
                instance.save(update_fields=['pinned_at'])


@receiver(post_save, sender=ForumReply)
def forum_reply_saved(sender, instance, created, **kwargs):
    """Handle forum reply creation"""
    if created:
        # Update post reply count and last_reply_at
        post = instance.post
        post.reply_count = post.replies.count()
        post.last_reply_at = timezone.now()
        post.save(update_fields=['reply_count', 'last_reply_at'])
        
        # Create notification for post author (if not replying to own post)
        if post.author != instance.author:
            create_notification(
                recipient=post.author,
                notification_type='new_reply',
                actor=instance.author,
                post=post,
                reply=instance
            )
        
        # Create notification for parent reply author (if nested reply)
        if instance.parent_reply and instance.parent_reply.author != instance.author:
            create_notification(
                recipient=instance.parent_reply.author,
                notification_type='new_reply',
                actor=instance.author,
                post=post,
                reply=instance
            )
        
        # Create notification for quoted reply author
        if instance.quoted_reply and instance.quoted_reply.author != instance.author:
            create_notification(
                recipient=instance.quoted_reply.author,
                notification_type='quote',
                actor=instance.author,
                post=post,
                reply=instance
            )
        
        # Extract and create mentions
        mentioned_usernames = extract_mentions(instance.content)
        if mentioned_usernames:
            create_mentions(mentioned_usernames, instance.author, post=instance.post, reply=instance)


@receiver(post_save, sender=ForumLike)
def forum_like_saved(sender, instance, created, **kwargs):
    """Handle forum like creation"""
    if created:
        # Update like count
        if instance.post:
            instance.post.like_count = instance.post.likes.count()
            instance.post.save(update_fields=['like_count'])
            
            # Create notification for post author (if not liking own post)
            if instance.post.author != instance.user:
                create_notification(
                    recipient=instance.post.author,
                    notification_type='like',
                    actor=instance.user,
                    post=instance.post
                )
        elif instance.reply:
            instance.reply.like_count = instance.reply.likes.count()
            instance.reply.save(update_fields=['like_count'])
            
            # Create notification for reply author (if not liking own reply)
            if instance.reply.author != instance.user:
                create_notification(
                    recipient=instance.reply.author,
                    notification_type='like',
                    actor=instance.user,
                    reply=instance.reply
                )


@receiver(pre_save, sender=ForumPost)
def forum_post_pre_save(sender, instance, **kwargs):
    """Handle forum post before save"""
    # If post is being pinned, set pinned_at
    if instance.is_pinned and not instance.pinned_at:
        instance.pinned_at = timezone.now()
    elif not instance.is_pinned:
        instance.pinned_at = None

