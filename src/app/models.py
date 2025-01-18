from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator

class User(AbstractUser):
    """
    Custom User model with additional fields for mentors and mentees.
    """
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
    """
    Represents a school associated with mentees and courses.
    """
    name = models.CharField(max_length=200)
    location = models.CharField(max_length=200)

    def __str__(self):
        return self.name

class Course(models.Model):
    """
    Represents a course, which can be associated with multiple schools.
    """
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=50)
    schools = models.ManyToManyField(School, related_name='courses')
    description = models.TextField()

    def __str__(self):
        return f"{self.code} - {self.name}"

class Mentee(models.Model):
    """
    Mentee-specific data extending the base User model.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='mentee_profile')
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='mentees')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='mentees')
    enrollment_date = models.DateField()

    def __str__(self):
        return f"{self.user.username} - {self.course.name}"

class Mentor(models.Model):
    """
    Mentor-specific data extending the base User model.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='mentor_profile')
    expertise = models.ManyToManyField(Course, related_name='mentors')
    available = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.username} - Mentor"

class Resource(models.Model):
    """
    Resources uploaded for a specific course.
    """
    title = models.CharField(max_length=200)
    description = models.TextField()
    file = models.FileField(upload_to='resources/')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='resources')
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='uploaded_resources')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

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

class Message(models.Model):
    """
    Messages within a chat.
    """
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='messages_sent')
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.sender.username}"

class Call(models.Model):
    """
    Call system for one-to-one or conference calls.
    """
    CALL_TYPES = (
        ('one_to_one', 'One to One'),
        ('conference', 'Conference'),
    )
    call_type = models.CharField(max_length=20, choices=CALL_TYPES)
    participants = models.ManyToManyField(User, related_name='calls')
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    room_id = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return f"Call ({self.call_type})"

class MentorSession(models.Model):
    """
    Represents mentoring sessions hosted by mentors.
    """
    mentor = models.ForeignKey(Mentor, on_delete=models.CASCADE, related_name='sessions')
    title = models.CharField(max_length=200)
    description = models.TextField()
    scheduled_time = models.DateTimeField()
    duration = models.IntegerField(help_text="Duration in minutes")
    max_participants = models.IntegerField()
    call = models.OneToOneField(Call, on_delete=models.CASCADE)

    def __str__(self):
        return self.title

class SessionAttendance(models.Model):
    """
    Tracks attendance of mentees in mentor sessions.
    """
    session = models.ForeignKey(MentorSession, on_delete=models.CASCADE, related_name='attendances')
    mentee = models.ForeignKey(Mentee, on_delete=models.CASCADE, related_name='attendances')
    joined_at = models.DateTimeField(auto_now_add=True)
    left_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Attendance for {self.session.title} - {self.mentee.user.username}"

class MentorRating(models.Model):
    """
    Allows mentees to rate mentors after sessions.
    """
    mentor = models.ForeignKey(Mentor, on_delete=models.CASCADE, related_name='ratings_received')
    mentee = models.ForeignKey(Mentee, on_delete=models.CASCADE, related_name='ratings_given')
    session = models.ForeignKey(MentorSession, on_delete=models.CASCADE, related_name='ratings')
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Rating for {self.mentor.user.username} by {self.mentee.user.username}"