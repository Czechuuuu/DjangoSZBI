from django.db import models
from django.contrib.auth.models import User

class Document(models.Model):
    STATUS = [
        ('draft', 'Draft'),
        ('review', 'In Review'),
        ('approval', 'Awaiting Approval'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(User, on_delete=models.PROTECT)
    status = models.CharField(max_length=20, choices=STATUS, default='draft')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.status})"


class DocumentVersion(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='versions')
    version_number = models.CharField(max_length=20)
    file = models.FileField(upload_to='documents/')
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    change_description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.document.title} v{self.version_number}"


class DocumentLog(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    timestamp = models.DateTimeField(auto_now_add=True)
    action = models.CharField(max_length=255)
    description = models.TextField()

    def __str__(self):
        return f"{self.document.title} - {self.action}"
