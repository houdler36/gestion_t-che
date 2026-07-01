from django.db import models
from django.conf import settings

class Project(models.Model):
    STATUS_CHOICES = (
        ('PREP', 'En préparation'),
        ('ONGOING', 'En cours'),
        ('DONE', 'Terminé'),
        ('SUSPENDED', 'Suspendu'),
    )
    
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PREP')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='projects_created')
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, through='ProjectMembership', related_name='projects')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class ProjectMembership(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'project')

class Activity(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='activities')
    name = models.CharField(max_length=200)
    responsible = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='responsible_activities')
    start_date = models.DateField()
    end_date = models.DateField()
    progress = models.IntegerField(default=0)
    manual_progress = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.project.name})"

class SubActivity(models.Model):
    STATUS_CHOICES = (
        ('TODO', 'À faire'),
        ('INPROGRESS', 'En cours'),
        ('DONE', 'Terminée'),
        ('BLOCKED', 'Bloquée'),
    )
    
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name='sub_activities')
    name = models.CharField(max_length=200)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='TODO')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.activity.name})"
