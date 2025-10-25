from django.db import models
from django.utils import timezone
from users.models import User


class KnowledgeDocument(models.Model):
    """Knowledge base documents for AI training"""
    
    DOCUMENT_TYPE_CHOICES = [
        ('pdf', 'PDF'),
        ('doc', 'Word Document'),
        ('txt', 'Text File'),
        ('html', 'HTML'),
        ('markdown', 'Markdown'),
        ('url', 'URL'),
        ('manual', 'Manual Entry'),
    ]
    
    STATUS_CHOICES = [
        ('uploaded', 'Uploaded'),
        ('processing', 'Processing'),
        ('indexed', 'Indexed'),
        ('failed', 'Failed'),
        ('archived', 'Archived'),
    ]
    
    title = models.CharField(max_length=200)
    content = models.TextField(blank=True)
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPE_CHOICES)
    file_path = models.CharField(max_length=500, blank=True)
    file_size = models.BigIntegerField(null=True, blank=True)  # Bytes
    url = models.URLField(blank=True)
    
    # Processing status
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='uploaded')
    processing_started = models.DateTimeField(null=True, blank=True)
    processing_completed = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    
    # Metadata
    tags = models.JSONField(default=list, blank=True)
    categories = models.JSONField(default=list, blank=True)
    language = models.CharField(max_length=10, default='en')
    
    # AI processing
    embedding_vector = models.JSONField(null=True, blank=True)  # Store vector embeddings
    chunk_count = models.IntegerField(default=0)
    
    # Ownership
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='uploaded_documents')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'knowledge_documents'
        verbose_name = 'Knowledge Document'
        verbose_name_plural = 'Knowledge Documents'
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['document_type', 'status']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.get_status_display()}"


class DocumentChunk(models.Model):
    """Chunks of documents for vector search"""
    
    document = models.ForeignKey(KnowledgeDocument, on_delete=models.CASCADE, related_name='chunks')
    chunk_index = models.IntegerField()
    content = models.TextField()
    embedding_vector = models.JSONField()  # Vector embedding for this chunk
    metadata = models.JSONField(default=dict, blank=True)  # Additional metadata
    
    class Meta:
        db_table = 'document_chunks'
        verbose_name = 'Document Chunk'
        verbose_name_plural = 'Document Chunks'
        unique_together = ('document', 'chunk_index')
        indexes = [
            models.Index(fields=['document', 'chunk_index']),
        ]
    
    def __str__(self):
        return f"{self.document.title} - Chunk {self.chunk_index}"


class ChatSession(models.Model):
    """AI chat sessions"""
    
    SESSION_TYPE_CHOICES = [
        ('general', 'General'),
        ('troubleshooting', 'Troubleshooting'),
        ('maintenance', 'Maintenance'),
        ('training', 'Training'),
    ]
    
    title = models.CharField(max_length=200, blank=True)
    session_type = models.CharField(max_length=20, choices=SESSION_TYPE_CHOICES, default='general')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_sessions')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'chat_sessions'
        verbose_name = 'Chat Session'
        verbose_name_plural = 'Chat Sessions'
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['session_type', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.title or 'Session'} - {self.user.username}"


class ChatMessage(models.Model):
    """Individual messages in chat sessions"""
    
    MESSAGE_TYPE_CHOICES = [
        ('user', 'User'),
        ('assistant', 'Assistant'),
        ('system', 'System'),
    ]
    
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPE_CHOICES)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # AI response metadata
    ai_model_used = models.CharField(max_length=100, blank=True)
    response_time = models.FloatField(null=True, blank=True)  # Seconds
    tokens_used = models.IntegerField(null=True, blank=True)
    confidence_score = models.FloatField(null=True, blank=True)
    
    # Source citations
    sources = models.JSONField(default=list, blank=True)  # List of source documents/chunks
    
    class Meta:
        db_table = 'chat_messages'
        verbose_name = 'Chat Message'
        verbose_name_plural = 'Chat Messages'
        indexes = [
            models.Index(fields=['session', 'timestamp']),
            models.Index(fields=['message_type', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.session.title} - {self.get_message_type_display()} - {self.timestamp}"


class AIModel(models.Model):
    """AI model configurations"""
    
    MODEL_TYPE_CHOICES = [
        ('llm', 'Large Language Model'),
        ('embedding', 'Embedding Model'),
        ('classification', 'Classification Model'),
    ]
    
    MODEL_MODE_CHOICES = [
        ('performance', 'Performance Mode'),
        ('lightweight', 'Lightweight Mode'),
    ]
    
    name = models.CharField(max_length=200)
    model_type = models.CharField(max_length=20, choices=MODEL_TYPE_CHOICES)
    model_path = models.CharField(max_length=500)
    model_config = models.JSONField(default=dict)  # Model configuration parameters
    
    # Performance settings
    mode = models.CharField(max_length=15, choices=MODEL_MODE_CHOICES, default='performance')
    max_tokens = models.IntegerField(default=2048)
    temperature = models.FloatField(default=0.7)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    
    # Metadata
    version = models.CharField(max_length=50, blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'ai_models'
        verbose_name = 'AI Model'
        verbose_name_plural = 'AI Models'
        indexes = [
            models.Index(fields=['model_type', 'is_active']),
            models.Index(fields=['mode', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.get_model_type_display()}"


class AIConversationTemplate(models.Model):
    """Predefined conversation templates for different scenarios"""
    
    TEMPLATE_TYPE_CHOICES = [
        ('troubleshooting', 'Troubleshooting'),
        ('maintenance', 'Maintenance'),
        ('training', 'Training'),
        ('general', 'General'),
    ]
    
    name = models.CharField(max_length=200)
    template_type = models.CharField(max_length=20, choices=TEMPLATE_TYPE_CHOICES)
    description = models.TextField()
    system_prompt = models.TextField()
    example_messages = models.JSONField(default=list)  # Example conversation flow
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'ai_conversation_templates'
        verbose_name = 'AI Conversation Template'
        verbose_name_plural = 'AI Conversation Templates'
    
    def __str__(self):
        return f"{self.name} - {self.get_template_type_display()}"


class AIUsageLog(models.Model):
    """Log of AI model usage for analytics"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ai_usage_logs')
    model = models.ForeignKey(AIModel, on_delete=models.CASCADE, related_name='usage_logs')
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='usage_logs')
    
    # Usage metrics
    tokens_used = models.IntegerField()
    response_time = models.FloatField()  # Seconds
    model_mode = models.CharField(max_length=15, choices=AIModel.MODEL_MODE_CHOICES)
    
    # Request details
    request_type = models.CharField(max_length=50)  # chat, embedding, classification
    input_length = models.IntegerField()
    output_length = models.IntegerField()
    
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'ai_usage_logs'
        verbose_name = 'AI Usage Log'
        verbose_name_plural = 'AI Usage Logs'
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['model', 'timestamp']),
            models.Index(fields=['model_mode', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.model.name} - {self.timestamp}"
