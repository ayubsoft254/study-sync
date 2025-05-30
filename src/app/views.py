from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, CreateView, DetailView
from django.http import JsonResponse, HttpResponseForbidden
from django.utils import timezone
from django.contrib import messages
from django.db.models import Avg, Count
from django.core.exceptions import PermissionDenied
from .models import Chat, Message, Mentor, User, MentorSession, SessionAttendance, MentorRating, Resource, Call, Mentee
import uuid
from typing import Dict, Any
from django.urls import reverse
from .forms import *
from .utils import generate_agora_token  # Import the function if it's defined in utils.py

class DashboardMixin:
    """Mixin to handle common dashboard functionality"""
    def get_dashboard_context(self, user: User) -> Dict[str, Any]:
        """Get basic context for dashboard"""
        return {
            'user': user,
            'notifications': user.notifications.filter(read=False)[:5],  # Assuming you add notifications
        }
    
def home(request):
    return render(request, 'app/home.html')

@login_required
def dashboard(request, username):
    """
    Enhanced dashboard view with better error handling and optimized queries
    """
    profile_user = get_object_or_404(User.objects.select_related('mentee', 'mentor'), 
                                    username=username)
    
    # Security check with custom error message
    if request.user != profile_user:
        messages.warning(request, "You can only access your own dashboard.")
        return redirect('app:dashboard', username=request.user.username)
    
    context = DashboardMixin().get_dashboard_context(profile_user)
    
    try:
        if hasattr(profile_user, 'mentee'):
            mentee = profile_user.mentee  # Get the Mentee instance
            
            # Optimize queries with select_related and prefetch_related
            upcoming_sessions = (MentorSession.objects
                .filter(participants=mentee,  # Use the mentee instance here
                        scheduled_time__gt=timezone.now())
                .select_related('mentor', 'call')
                .prefetch_related('participants'))
            
            # Use the mentee instance directly
            attended_sessions = (SessionAttendance.objects
                .filter(mentee=mentee)  # Ensure this uses the Mentee instance
                .select_related('session', 'session__mentor')
                .order_by('-session__scheduled_time'))
            
            resources = (Resource.objects
                .filter(course=mentee.course)
                .select_related('course', 'uploaded_by'))
            
            context.update({
                'role': 'mentee',
                'resources': resources,
                'upcoming_sessions': upcoming_sessions,
                'attended_sessions': attended_sessions,
                'course_progress': mentee.get_course_progress(),
            })
            
        elif hasattr(profile_user, 'mentor'):
            mentor = profile_user.mentor
            
            mentor_stats = (MentorSession.objects
                .filter(mentor=mentor)
                .aggregate(
                    avg_rating=Avg('ratings__rating'),
                    total_sessions=Count('id'),
                    unique_participants=Count('participants', distinct=True)
                ))
            
            created_sessions = (MentorSession.objects
                .filter(mentor=mentor)
                .prefetch_related('participants')
                .order_by('-scheduled_time'))
            
            recent_ratings = (MentorRating.objects
                .filter(mentor=mentor)
                .select_related('mentee', 'session')
                .order_by('-created_at')[:5])
            
            context.update({
                'role': 'mentor',
                'created_sessions': created_sessions,
                'recent_ratings': recent_ratings,
                'stats': mentor_stats,
            })
            
        else:
            messages.info(request, "Please complete your profile setup to access the dashboard.")
            return redirect('app:account_profile')
            
    except Exception as e:
        messages.error(request, f"An error occurred while loading the dashboard: {str(e)}")
        # Log the error here
    
    return render(request, 'app/dashboard.html', context)


def login_redirect(request):
    if request.user.is_authenticated:
        # Use the namespaced URL name
        return redirect('app:dashboard', username=request.user.username)
    return redirect('account_login')

class MentorSessionCreate(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = MentorSession
    fields = ['title', 'description', 'scheduled_time', 'duration', 'max_participants']
    template_name = 'app/mentor_session_form.html'
    
    def test_func(self):
        return hasattr(self.request.user, 'mentor')
    
    def form_valid(self, form):
        try:
            form.instance.mentor = self.request.user.mentor
            form.instance.call = Call.objects.create(
                call_type='conference',
                room_id=f"session_{uuid.uuid4().hex[:10]}"
            )
            response = super().form_valid(form)
            messages.success(self.request, "Session created successfully!")
            return response
        except Exception as e:
            messages.error(self.request, f"Failed to create session: {str(e)}")
            return self.form_invalid(form)
    
    def get_success_url(self):
        # Replace 'dashboard' with the name of the URL pattern for your dashboard
        return reverse('app:dashboard', kwargs={'username': self.request.user.username})           
        
        

@login_required
def start_one_to_one_call(request, user_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        other_user = get_object_or_404(User, id=user_id)
        
        # Check if there's already an active call
        existing_call = Call.objects.filter(
            call_type='one_to_one',
            participants__in=[request.user, other_user],
            ended_at__isnull=True
        ).first()
        
        if existing_call:
            return JsonResponse({'room_id': existing_call.room_id})
        
        # Create new call
        call = Call.objects.create(
            call_type='one_to_one',
            room_id=f"call_{uuid.uuid4().hex[:10]}"
        )
        call.participants.add(request.user, other_user)
        
        return JsonResponse({
            'room_id': call.room_id,
            'message': 'Call created successfully'
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def rate_mentor(request, session_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        session = get_object_or_404(MentorSession, id=session_id)
        
        # Verify the user attended the session
        if not SessionAttendance.objects.filter(
            session=session,
            mentee=request.user.mentee
        ).exists():
            return JsonResponse({'error': 'You must attend the session to rate it'}, status=403)
        
        # Check if user already rated this session
        if MentorRating.objects.filter(
            session=session,
            mentee=request.user.mentee
        ).exists():
            return JsonResponse({'error': 'You have already rated this session'}, status=400)
        
        rating = int(request.POST.get('rating'))
        if not 1 <= rating <= 5:
            return JsonResponse({'error': 'Rating must be between 1 and 5'}, status=400)
        
        MentorRating.objects.create(
            mentor=session.mentor,
            mentee=request.user.mentee,
            session=session,
            rating=rating,
            comment=request.POST.get('comment', '')
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Rating submitted successfully'
        })
        
    except ValueError:
        return JsonResponse({'error': 'Invalid rating value'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

class ResourceCreate(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Resource
    fields = ['title', 'description', 'file', 'course']
    template_name = 'app/resource_form.html'
    
    def test_func(self):
        return hasattr(self.request.user, 'mentor')
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if hasattr(self.request.user, 'mentor'):
            # Limit course choices to mentor's courses
            form.fields['course'].queryset = self.request.user.mentor.courses.all()
        return form
    
    def form_valid(self, form):
        try:
            form.instance.uploaded_by = self.request.user
            response = super().form_valid(form)
            messages.success(self.request, "Resource created successfully!")
            return response
        except Exception as e:
            messages.error(self.request, f"Failed to create resource: {str(e)}")
            return self.form_invalid(form)
        
@login_required
def profile_setup(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST)
        if form.is_valid():
            role = form.cleaned_data['role']
            user = request.user
            
            try:
                if role == 'mentor':
                    mentor = Mentor.objects.create(
                        user=user,
                        expertise=form.cleaned_data['expertise'],
                        available=True
                    )
                    # Add selected courses to the mentor
                    mentor.courses.set(form.cleaned_data['courses'])
                    
                else:  # mentee
                    Mentee.objects.create(
                        user=user,
                        school=form.cleaned_data['school'],
                        course=form.cleaned_data['course'],
                        enrollment_date=timezone.now()
                    )
                
                messages.success(request, "Profile setup completed successfully!")
                return redirect('app:dashboard', username=user.username)
                
            except Exception as e:
                messages.error(request, f"An error occurred while setting up your profile: {str(e)}")
    else:
        form = ProfileForm()
    
    return render(request, 'app/profile_setup.html', {'form': form})

@login_required
def sessions_view(request):
    user = request.user

    # Check if the user is a mentee or mentor
    if hasattr(user, 'mentee'):
        mentee = user.mentee
        # Filter sessions where the mentee is a participant
        sessions = MentorSession.objects.filter(
            participants=mentee  # Use the mentee instance here
        ).select_related('mentor').prefetch_related('participants')
        # Get all users in the same course as the mentee
        course_members = User.objects.filter(
            mentee__course=mentee.course
        ).select_related('mentee', 'mentor')
    elif hasattr(user, 'mentor'):
        mentor = user.mentor
        # Filter sessions created by the mentor
        sessions = MentorSession.objects.filter(
            mentor=mentor
        ).select_related('mentor').prefetch_related('participants')
        # Get all users in the courses taught by the mentor
        course_members = User.objects.filter(
            mentee__course__in=mentor.courses.all()
        ).select_related('mentee', 'mentor')
    else:
        # Handle case where the user is neither a mentee nor a mentor
        sessions = MentorSession.objects.none()
        course_members = User.objects.none()
        messages.info(request, "Please complete your profile setup to access sessions.")

    context = {
        'sessions': sessions,
        'course_members': course_members,
        'role': 'mentor' if hasattr(request.user, 'mentor') else 'mentee',
        'currentUserId': request.user.id,
        'now': timezone.now(),
    }
    return render(request, 'app/sessions.html', context)

@login_required
def send_message(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

    recipient_id = request.POST.get('recipient')
    message_content = request.POST.get('message')

    if not recipient_id or not message_content:
        return JsonResponse({'status': 'error', 'message': 'Invalid data'}, status=400)

    # Validate recipient_id is a valid integer
    try:
        recipient_id = int(recipient_id)
    except (ValueError, TypeError):
        return JsonResponse({'status': 'error', 'message': 'Invalid recipient ID'}, status=400)

    try:
        recipient = User.objects.get(id=recipient_id)
        
        # Check if sender has a profile
        if not (hasattr(request.user, 'mentee') or hasattr(request.user, 'mentor')):
            return JsonResponse({'status': 'error', 'message': 'Please complete your profile setup'}, status=403)
        
        # Check if recipient has a profile
        if not (hasattr(recipient, 'mentee') or hasattr(recipient, 'mentor')):
            return JsonResponse({'status': 'error', 'message': 'Recipient has not completed profile setup'}, status=403)
        
        # Ensure the recipient is part of the same course
        valid_recipient = False
        
        if hasattr(request.user, 'mentee') and hasattr(recipient, 'mentee'):
            # Both are mentees - check same course
            if request.user.mentee.course == recipient.mentee.course:
                valid_recipient = True
        elif hasattr(request.user, 'mentor') and hasattr(recipient, 'mentee'):
            # Sender is mentor, recipient is mentee
            if recipient.mentee.course in request.user.mentor.courses.all():
                valid_recipient = True
        elif hasattr(request.user, 'mentee') and hasattr(recipient, 'mentor'):
            # Sender is mentee, recipient is mentor
            if request.user.mentee.course in recipient.mentor.courses.all():
                valid_recipient = True
        elif hasattr(request.user, 'mentor') and hasattr(recipient, 'mentor'):
            # Both are mentors - check if they share any courses
            sender_courses = set(request.user.mentor.courses.all())
            recipient_courses = set(recipient.mentor.courses.all())
            if sender_courses.intersection(recipient_courses):
                valid_recipient = True
        
        if not valid_recipient:
            return JsonResponse({'status': 'error', 'message': 'You can only message users in your courses'}, status=403)

        # Get or create private chat between users
        chat = Chat.objects.filter(
            chat_type='private',
            participants=request.user
        ).filter(
            participants=recipient
        ).first()
        
        if not chat:
            chat = Chat.objects.create(chat_type='private')
            chat.participants.add(request.user, recipient)
        
        # Create the message
        message = Message.objects.create(
            chat=chat,
            sender=request.user,
            content=message_content.strip()
        )
        
        # Update chat's updated_at timestamp
        chat.updated_at = timezone.now()
        chat.save(update_fields=['updated_at'])
        
        return JsonResponse({
            'status': 'success',
            'message_id': message.id,
            'timestamp': message.created_at.isoformat()
        })
        
    except User.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Recipient not found'}, status=404)
    except Exception as e:
        # Log the error in production
        print(f"Error in send_message: {str(e)}")
        return JsonResponse({'status': 'error', 'message': 'An unexpected error occurred'}, status=500)

@login_required
def get_messages(request, user_id):
    try:
        # Validate user_id
        try:
            user_id = int(user_id)
        except (ValueError, TypeError):
            return JsonResponse({'error': 'Invalid user ID'}, status=400)
        
        other_user = User.objects.get(id=user_id)
        
        # Check if current user has a profile
        if not (hasattr(request.user, 'mentee') or hasattr(request.user, 'mentor')):
            return JsonResponse({'error': 'Please complete your profile setup'}, status=403)
        
        # Check if other user has a profile
        if not (hasattr(other_user, 'mentee') or hasattr(other_user, 'mentor')):
            return JsonResponse({'error': 'User has not completed profile setup'}, status=403)
        
        # Verify users can chat (same course validation as in send_message)
        valid_chat = False
        
        if hasattr(request.user, 'mentee') and hasattr(other_user, 'mentee'):
            if request.user.mentee.course == other_user.mentee.course:
                valid_chat = True
        elif hasattr(request.user, 'mentor') and hasattr(other_user, 'mentee'):
            if other_user.mentee.course in request.user.mentor.courses.all():
                valid_chat = True
        elif hasattr(request.user, 'mentee') and hasattr(other_user, 'mentor'):
            if request.user.mentee.course in other_user.mentor.courses.all():
                valid_chat = True
        elif hasattr(request.user, 'mentor') and hasattr(other_user, 'mentor'):
            sender_courses = set(request.user.mentor.courses.all())
            recipient_courses = set(other_user.mentor.courses.all())
            if sender_courses.intersection(recipient_courses):
                valid_chat = True
        
        if not valid_chat:
            return JsonResponse({'error': 'You can only chat with users in your courses'}, status=403)
        
        # Fetch chat between the current user and the other user
        chat = Chat.objects.filter(
            chat_type='private',
            participants=request.user
        ).filter(
            participants=other_user
        ).first()
        
        if chat:
            messages = chat.messages.select_related('sender').values(
                'id', 'sender__id', 'sender__username', 'content', 'created_at'
            ).order_by('created_at')
            
            # Mark messages as read (optional - you might want to add this later)
            # chat.messages.filter(sender=other_user, is_read=False).update(is_read=True)
            
            return JsonResponse(list(messages), safe=False)
        else:
            return JsonResponse([], safe=False)
            
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)
    except Exception as e:
        # Log the error in production
        print(f"Error in get_messages: {str(e)}")
        return JsonResponse({'error': 'An unexpected error occurred'}, status=500)

@login_required
def join_session(request, session_id):
    if not hasattr(request.user, 'mentee'):
        return JsonResponse({'status': 'error', 'message': 'Only mentees can join sessions'}, status=403)

    try:
        session = get_object_or_404(MentorSession, id=session_id)
        
        # Check if mentee is already in the session
        existing_attendance = SessionAttendance.objects.filter(
            session=session,
            mentee=request.user.mentee
        ).first()
        
        if existing_attendance:
            # Already joined, return existing token
            token = generate_agora_token(session.call.room_id)
            return JsonResponse({
                'status': 'success',
                'token': token,
                'channel': session.call.room_id,
                'message': 'Already joined session'
            })
        
        if session.is_full:
            return JsonResponse({'status': 'error', 'message': 'Session is full'}, status=400)
        
        # Check if session hasn't started yet or is still active
        if not session.can_start and session.call.is_active:
            return JsonResponse({'status': 'error', 'message': 'Session has not started yet'}, status=400)
        
        # Create attendance record
        SessionAttendance.objects.create(
            session=session,
            mentee=request.user.mentee
        )
        
        token = generate_agora_token(session.call.room_id)
        return JsonResponse({
            'status': 'success',
            'token': token,
            'channel': session.call.room_id,
            'message': 'Successfully joined session'
        })
        
    except Exception as e:
        print(f"Error in join_session: {str(e)}")
        return JsonResponse({'status': 'error', 'message': 'Failed to join session'}, status=500)