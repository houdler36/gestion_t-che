from django.db import models
from django.conf import settings
from tasks.models import Task

class DailyLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='daily_logs')
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='logs')
    date = models.DateField(auto_now_add=True)
    time_spent = models.DurationField(blank=True, null=True)
    time_spent_minutes = models.IntegerField(blank=True, null=True)
    comment = models.TextField(blank=True)
    difficulties = models.TextField(blank=True)
    progress_delta = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.task.name} - {self.date}"