
from django.db import models
from django.conf import settings

class MentorDetails(models.Model):
    VERIFICATION_STATUS = [
        ('pending', 'Pending'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('needs_revision', 'Needs Revision'),
    ]
    
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='mentor_profile')
    bio = models.TextField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    expertise = models.JSONField(default=list)
    experience_years = models.IntegerField(default=0)
    is_verified = models.BooleanField(default=False)
    verification_status = models.CharField(
        max_length=15,
        choices=VERIFICATION_STATUS,
        default='pending'
    )
    profile_picture = models.ImageField(upload_to='mentor_profile_pics/', blank=True, null=True)
    rejection_reason = models.TextField(blank=True, null=True)
    last_status_update = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.email

class Education(models.Model):
    mentor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='educations')
    degree = models.CharField(max_length=100)
    institution = models.CharField(max_length=200)
    start_year = models.IntegerField()
    end_year = models.IntegerField(null=True, blank=True) 
    is_current = models.BooleanField(default=False)


class VerificationDocument(models.Model):
    mentor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='documents')
    DOCUMENT_TYPES = [
        ('ID', 'Government ID'),
        ('TRANSCRIPT', 'Transcript'),
        ('ENROLLMENT', 'Enrollment Proof'),  
    ]
    document_type = models.CharField(max_length=15, choices=DOCUMENT_TYPES)
    file = models.FileField(upload_to='verification_docs/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_approved = models.BooleanField(default=False)