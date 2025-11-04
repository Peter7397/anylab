import re
from typing import List, Set
from django.contrib.auth import get_user_model

User = get_user_model()


def extract_mentions(text: str) -> Set[str]:
    """
    Extract @mentions from text
    Returns a set of usernames mentioned
    Pattern: @username or @username 
    """
    if not text:
        return set()
    
    # Pattern to match @username (alphanumeric and underscores)
    pattern = r'@([a-zA-Z0-9_]+)'
    matches = re.findall(pattern, text)
    return set(matches)


def create_mentions(mentioned_usernames: Set[str], mentioned_by, post=None, reply=None):
    """
    Create ForumMention records for mentioned users
    """
    if not mentioned_usernames:
        return []
    
    from .models import ForumMention
    
    mentions = []
    for username in mentioned_usernames:
        try:
            mentioned_user = User.objects.get(username=username)
            if mentioned_user != mentioned_by:  # Don't mention yourself
                mention = ForumMention.objects.create(
                    mentioned_user=mentioned_user,
                    mentioned_by=mentioned_by,
                    post=post,
                    reply=reply
                )
                mentions.append(mention)
        except User.DoesNotExist:
            # User doesn't exist, skip
            continue
    
    return mentions


def create_notification(recipient, notification_type, actor=None, post=None, reply=None):
    """
    Create a ForumNotification record
    """
    from .models import ForumNotification
    
    notification = ForumNotification.objects.create(
        recipient=recipient,
        notification_type=notification_type,
        actor=actor,
        post=post,
        reply=reply
    )
    return notification


def parse_quoted_content(content: str) -> str:
    """
    Parse quoted content from reply text
    This is a simple implementation - can be enhanced with rich text support
    """
    # Pattern for quoted text: > quote text
    lines = content.split('\n')
    quoted_lines = []
    regular_lines = []
    in_quote = False
    
    for line in lines:
        if line.strip().startswith('>'):
            quoted_lines.append(line)
            in_quote = True
        else:
            if in_quote and line.strip() == '':
                in_quote = False
            regular_lines.append(line)
    
    return '\n'.join(quoted_lines) if quoted_lines else None

