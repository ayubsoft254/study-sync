from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid

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

    def __str__(self):
        return f"{self.session.title} - {self.rating}"

class ChatRoom(models.Model):
    ROOM_TYPES = [
        ('session', 'Study Session Chat'),
        ('course', 'Course Discussion'),
        ('private', 'Private Chat'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    room_type = models.CharField(max_length=20, choices=ROOM_TYPES)
    participants = models.ManyToManyField(StudentProfile, related_name='chat_rooms')
    study_session = models.OneToOneField(
        StudySession,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='chat_room'
    )
    course = models.ForeignKey(
        Course,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='chat_rooms'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} ({self.room_type})"

class Message(models.Model):
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_system_message = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['timestamp']
    
    def __str__(self):
        return f"{self.sender.user.username}: {self.content[:50]}"
    
class University(models.Model):
    name = models.CharField(max_length=255)
    domain = models.CharField(max_length=100, unique=True)  # e.g., 'harvard.edu'
    description = models.TextField()
    logo = models.ImageField(upload_to='university_logos/', null=True, blank=True)
    verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "universities"

    def __str__(self):
        return self.name

class Department(models.Model):
    university = models.ForeignKey(University, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=10)  # e.g., 'CS', 'MATH'

    def __str__(self):
        return f"{self.code} - {self.name} ({self.university.name})"

# Extend previous StudentProfile model
class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    university = models.ForeignKey(University, on_delete=models.CASCADE)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    student_id = models.CharField(max_length=50)
    year_of_study = models.IntegerField()
    bio = models.TextField(blank=True)
    courses = models.ManyToManyField('Course', related_name='students')
    mentor_rating = models.FloatField(default=0.0)
    is_available_as_mentor = models.BooleanField(default=False)
    email_verified = models.BooleanField(default=False)
    profile_picture = models.ImageField(upload_to='profile_pics/', null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.university.name}"

class Resource(models.Model):
    RESOURCE_TYPES = [
        ('document', 'Document'),
        ('video', 'Video'),
        ('link', 'External Link'),
        ('quiz', 'Quiz'),
        ('notes', 'Study Notes'),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField()
    course = models.ForeignKey('Course', on_delete=models.CASCADE, related_name='resources')
    resource_type = models.CharField(max_length=20, choices=RESOURCE_TYPES)
    uploaded_by = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    file = models.FileField(
        upload_to='resources/',
        null=True,
        blank=True,
        validators=[FileExtensionValidator(
            allowed_extensions=['pdf', 'doc', 'docx', 'ppt', 'pptx', 'txt', 'mp4']
        )]
    )
    external_link = models.URLField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    views = models.IntegerField(default=0)
    likes = models.ManyToManyField(StudentProfile, related_name='liked_resources')
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.title} ({self.resource_type})"

class ResourceComment(models.Model):
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Comment by {self.author.user.username} on {self.resource.title}"
    