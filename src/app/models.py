from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import uuid

def generate_room_id():
    return str(uuid.uuid4())

class School(models.Model):
    name = models.CharField(max_length=200)
    location = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']

class Course(models.Model):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=50, unique=True)
    schools = models.ManyToManyField(School, related_name='courses')
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.code} - {self.name}"

    class Meta:
        ordering = ['code']

class Profile(models.Model):
    ROLE_CHOICES = [
        ('mentor', 'Mentor'),
        ('mentee', 'Mentee'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    bio = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.role}"

    @property
    def is_mentor(self):
        return self.role == 'mentor'

    @property
    def is_mentee(self):
        return self.role == 'mentee'

class Mentee(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='mentee')
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='mentees')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='mentees')
    enrollment_date = models.DateField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.get_full_name() or self.user.username

    def get_course_progress(self):
        # Calculate course progress based on attended sessions
        total_sessions = self.attendances.count()
        completed_sessions = self.attendances.filter(left_at__isnull=False).count()
        return (completed_sessions / total_sessions * 100) if total_sessions > 0 else 0

class Mentor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='mentor')
    courses = models.ManyToManyField(Course, related_name='mentors')
    expertise = models.TextField()
    available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.get_full_name() or self.user.username

    def get_average_rating(self):
        return self.ratings_received.aggregate(
            avg_rating=models.Avg('rating')
        )['avg_rating'] or 0.0

    def get_total_students(self):
        return SessionAttendance.objects.filter(
            session__mentor=self
        ).values('mentee').distinct().count()

class Resource(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    file = models.FileField(upload_to='resources/%Y/%m/')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='resources')
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='uploaded_resources')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-created_at']

class Call(models.Model):
    CALL_TYPES = [
        ('one_to_one', 'One to One'),
        ('conference', 'Conference'),
    ]
    call_type = models.CharField(max_length=20, choices=CALL_TYPES)
    room_id = models.CharField(max_length=100, unique=True, default=generate_room_id)
    participants = models.ManyToManyField(User, related_name='calls')
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.call_type} Call - {self.room_id}"

    @property
    def is_active(self):
        return self.started_at is not None and self.ended_at is None

class MentorSession(models.Model):
    mentor = models.ForeignKey(Mentor, on_delete=models.CASCADE, related_name='sessions')
    title = models.CharField(max_length=200)
    description = models.TextField()
    scheduled_time = models.DateTimeField()
    duration = models.IntegerField(
        help_text="Duration in minutes",
        validators=[MinValueValidator(15), MaxValueValidator(180)]
    )
    max_participants = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(50)]
    )
    call = models.OneToOneField(Call, on_delete=models.CASCADE, related_name='session')
    participants = models.ManyToManyField(Mentee, through='SessionAttendance')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-scheduled_time']

    @property
    def is_full(self):
        return self.participants.count() >= self.max_participants

    @property
    def can_start(self):
        return timezone.now() >= self.scheduled_time and not self.call.is_active

class SessionAttendance(models.Model):
    session = models.ForeignKey(MentorSession, on_delete=models.CASCADE, related_name='attendances')
    mentee = models.ForeignKey(Mentee, on_delete=models.CASCADE, related_name='attendances')
    joined_at = models.DateTimeField(auto_now_add=True)
    left_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.mentee} - {self.session}"

    class Meta:
        unique_together = ['session', 'mentee']

class MentorRating(models.Model):
    mentor = models.ForeignKey(Mentor, on_delete=models.CASCADE, related_name='ratings_received')
    mentee = models.ForeignKey(Mentee, on_delete=models.CASCADE, related_name='ratings_given')
    session = models.ForeignKey(MentorSession, on_delete=models.CASCADE, related_name='ratings')
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Rating for {self.mentor} by {self.mentee}"

    class Meta:
        unique_together = ['mentee', 'session']
        ordering = ['-created_at']

class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('session_reminder', 'Session Reminder'),
        ('session_started', 'Session Started'),
        ('new_rating', 'New Rating'),
        ('new_resource', 'New Resource'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.type} for {self.user}"

    class Meta:
        ordering = ['-created_at']

class Chat(models.Model):
    """
    Chat system for mentors and mentees.
    """
    CHAT_TYPES = (
        ('private', 'Private'),
        ('public', 'Public'),
    )
    chat_type = models.CharField(max_length=10, choices=CHAT_TYPES)
    participants = models.ManyToManyField(User, related_name='chats')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Chat ({self.chat_type})"