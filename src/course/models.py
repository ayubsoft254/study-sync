from django.db import models

# Create your models here.
from django.contrib.auth.models import User
from django.utils import timezone

class Subject(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Course(models.Model):
    name = models.CharField(max_length=200)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    description = models.TextField()
    university = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.university}"

class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    university = models.CharField(max_length=200)
    major = models.CharField(max_length=100)
    bio = models.TextField(blank=True)
    courses = models.ManyToManyField(Course, related_name='students')
    mentor_rating = models.FloatField(default=0.0)
    is_available_as_mentor = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - {self.university}"

class StudySession(models.Model):
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    mentor = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='mentor_sessions')
    students = models.ManyToManyField(StudentProfile, related_name='student_sessions')
    title = models.CharField(max_length=200)
    description = models.TextField()
    scheduled_time = models.DateTimeField()
    duration = models.DurationField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    max_participants = models.IntegerField(default=5)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.scheduled_time}"

class SessionFeedback(models.Model):
    session = models.ForeignKey(StudySession, on_delete=models.CASCADE)
    from_user = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='feedback_given')
    to_user = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='feedback_received')
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['session', 'from_user', 'to_user']