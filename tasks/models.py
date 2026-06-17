from django.db import models
from django.conf import settings

from projects.models import SubActivity, Project


class Task(models.Model):
    PRIORITY_CHOICES = (
        ('LOW', 'Faible'),
        ('MEDIUM', 'Moyenne'),
        ('HIGH', 'Haute'),
    )
    STATUS_CHOICES = (
        ('TODO', 'À faire'),
        ('INPROGRESS', 'En cours'),
        ('DONE', 'Terminée'),
        ('BLOCKED', 'Bloquée'),
    )

    sub_activity = models.ForeignKey(SubActivity, on_delete=models.CASCADE, null=True, blank=True, related_name='tasks')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, null=True, blank=True, related_name='tasks')

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='assigned_tasks')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='created_tasks')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='MEDIUM')
    due_date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='TODO')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} (assignée à {self.assigned_to.username})"

    def is_project_task(self):
        return self.sub_activity is not None

