from django.db import models
from django.conf import settings

class StudentDetails(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    education_level = models.CharField(max_length=255)
    interests = models.JSONField(default=list)

    def __str__(self):
        return self.user.email
