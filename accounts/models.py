from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = (
        ('ADMIN', 'Administrateur'),
        ('PM', 'Chef de projet'),
        ('MEMBER', 'Membre'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='MEMBER')
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"