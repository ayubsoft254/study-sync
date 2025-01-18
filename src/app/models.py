# models.py
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator

class User(AbstractUser):
    is_mentor = models.BooleanField(default=False)
    bio = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to='profiles/', null=True, blank=True)

    groups = models.ManyToManyField(
        'auth.Group',
        related_name='custom_user_set',  # Change the related_name
        blank=True,
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='custom_user_permissions_set',  # Change the related_name
        blank=True,
    )

class School(models.Model):
    name = models.CharField(max_length=200)
    location = models.CharField(max_length=200)
    
    def __str__(self):
        return self.name

class Course(models.Model):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=50)
    schools = models.ManyToManyField(School, related_name='courses')  # Many-to-Many Relationship
    description = models.TextField()

    def __str__(self):
        return f"{self.code} - {self.name}"

class Mentee(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    enrollment_date = models.DateField()

class Resource(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    file = models.FileField(upload_to='resources/')
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

class Chat(models.Model):
    CHAT_TYPES = (
        ('private', 'Private'),
        ('public', 'Public'),
    )
    
    chat_type = models.CharField(max_length=10, choices=CHAT_TYPES)
    participants = models.ManyToManyField(User, related_name='chats')
    created_at = models.DateTimeField(auto_now_add=True)

class Message(models.Model):
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE)
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

class Call(models.Model):
    CALL_TYPES = (
        ('one_to_one', 'One to One'),
        ('conference', 'Conference'),
    )
    
    call_type = models.CharField(max_length=20, choices=CALL_TYPES)
    participants = models.ManyToManyField(User, related_name='calls')
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    room_id = models.CharField(max_length=100, unique=True)

class MentorSession(models.Model):
    mentor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mentor_sessions')
    title = models.CharField(max_length=200)
    description = models.TextField()
    scheduled_time = models.DateTimeField()
    duration = models.IntegerField(help_text="Duration in minutes")
    max_participants = models.IntegerField()
    call = models.OneToOneField(Call, on_delete=models.CASCADE)

class SessionAttendance(models.Model):
    session = models.ForeignKey(MentorSession, on_delete=models.CASCADE)
    mentee = models.ForeignKey(User, on_delete=models.CASCADE)
    joined_at = models.DateTimeField(auto_now_add=True)
    left_at = models.DateTimeField(null=True, blank=True)

class MentorRating(models.Model):
    mentor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ratings_received')
    mentee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ratings_given')
    session = models.ForeignKey(MentorSession, on_delete=models.CASCADE)
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)