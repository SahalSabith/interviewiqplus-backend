from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.hashers import make_password

class UserProfile(models.Model):
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
        ('prefer_not_to_say', 'Prefer not to say'),
    ]

    STATUS_CHOICES = [
        ('student', 'Student'),
        ('working_professional', 'Working Professional'),
    ]

    full_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    mobile = models.CharField(max_length=15, unique=True)
    password = models.CharField(max_length=128)
    age = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(120)])
    dob = models.DateField()
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES)
    current_status = models.CharField(max_length=30, choices=STATUS_CHOICES)
    job_role = models.CharField(max_length=100, blank=True, null=True)
    career_interest = models.CharField(max_length=200)
    target_company = models.CharField(max_length=100, blank=True, null=True)
    confident_skills = models.CharField(max_length=200)
    face_encoding = models.BinaryField()

    def save(self, *args, **kwargs):
        if not self.password.startswith('pbkdf2_'):
            self.password = make_password(self.password)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.full_name