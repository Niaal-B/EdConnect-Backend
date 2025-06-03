from django.db import models
from django.conf import settings
import datetime

class StudentDetails(models.Model):

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='student_profile'
    )
    education_level = models.CharField(
        max_length=50,
        default='high_school'
    )
    fields_of_interest = models.JSONField(
        default=list,
        help_text="List of fields the student is interested in (e.g., Computer Science, Business)"
    )
    mentorship_preferences = models.JSONField(
        default=list,
        help_text="List of preferred mentorship types"
    )
    preferred_countries = models.JSONField(
        default=list,
        help_text="List of preferred study countries"
    )
    interested_universities = models.JSONField(
        default=list,
        help_text="List of universities the student is interested in"
    )
    additional_notes = models.TextField(
        blank=True,
        null=True,
        help_text="Any additional notes or preferences"
    )

    profile_picture = models.ImageField(upload_to='student_profile_pics/', blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email} - {self.get_education_level_display()}"

    class Meta:
        verbose_name = "Student Detail"
        verbose_name_plural = "Student Details"