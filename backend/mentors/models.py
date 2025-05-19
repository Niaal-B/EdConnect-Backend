
from django.db import models
from django.conf import settings

class MentorDetails(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    expertise = models.JSONField(default=list)
    experience_years = models.IntegerField()
    availability = models.JSONField(default=list)
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False) 
    verification_document = models.FileField(upload_to='mentor_documents/', null=True, blank=True)

    def __str__(self):
        return self.user.email