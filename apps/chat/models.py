from django.db import models
from django.utils import timezone
from apps.registration.models import Student


class Message(models.Model):
    sent_at = models.DateTimeField(default=timezone.now)
    from_user = models.ForeignKey(Student, null=True, on_delete=models.CASCADE)
    to_chat = models.ForeignKey('Chat', on_delete=models.CASCADE, related_name='+')
    message = models.CharField(max_length=500, blank=False)


class Chat(models.Model):
    participants = models.ManyToManyField(Student)
    messages = models.ManyToManyField(Message, blank=True)
    last_message = models.ForeignKey('Message', on_delete=models.CASCADE, blank=True, null=True, related_name='+')
    is_closed = models.BooleanField(default=False)
    is_feedback = models.BooleanField(default=False)
    is_assigned = models.BooleanField(default=False)
