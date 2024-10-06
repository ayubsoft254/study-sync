from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.http import JsonResponse
from django.db.models import Q
from .models import StudySession, ChatRoom, Resource, Course, StudentProfile, ChatRoom, University
from .forms import ResourceUploadForm, ResourceCommentForm

# Create your views here.
def home(request):


    return render(request, 'course/home.html', {})

@login_required
def dashboard(request):
    user_profile = request.user.studentprofile
    upcoming_sessions = StudySession.objects.filter(
        Q(mentor=user_profile) | Q(students=user_profile),
        status='scheduled'
    ).order_by('scheduled_time')
    
    context = {
        'upcoming_sessions': upcoming_sessions,
        'enrolled_courses': user_profile.courses.all(),
        'mentor_rating': user_profile.mentor_rating,
    }
    return render(request, 'course/dashboard.html', context)

@login_required
def create_study_session(request):
    if request.method == 'POST':
        course_id = request.POST.get('course_id')
        course = get_object_or_404(Course, id=course_id)
        
        session = StudySession.objects.create(
            course=course,
            mentor=request.user.studentprofile,
            title=request.POST.get('title'),
            description=request.POST.get('description'),
            scheduled_time=request.POST.get('scheduled_time'),
            duration=request.POST.get('duration'),
            max_participants=request.POST.get('max_participants')
        )
        return redirect('session_detail', session_id=session.id)
    
    courses = request.user.studentprofile.courses.all()
    return render(request, 'course/create_session.html', {'courses': courses})

@login_required
def join_session(request, session_id):
    session = get_object_or_404(StudySession, id=session_id)
    if request.method == 'POST':
        if session.students.count() < session.max_participants:
            session.students.add(request.user.studentprofile)
            return JsonResponse({'status': 'success'})
        return JsonResponse({'status': 'full'}, status=400)
    return JsonResponse({'status': 'error'}, status=405)

@login_required
#\\create a view for creating a chat room from the chatroom  model





def chat_room(request, room_id):
    room = get_object_or_404(ChatRoom, id=room_id)
    messages = room.messages.all().select_related('sender__user')[:100]
    
    context = {
        'room': room,
        'messages': messages,
    }
    return render(request, 'course/chat.html', context)

@login_required
def create_public_chat(request):
    chat_room = ChatRoom.objects.create(
        name="Public Room",
        room_type='public'
    )
    return redirect('chat_room', room_id=chat_room.id)


@login_required
def create_private_chat(request, student_id):
    other_student = get_object_or_404(StudentProfile, id=student_id)
    user_profile = request.user.studentprofile
    
    # Check if chat already exists
    existing_chat = ChatRoom.objects.filter(
        room_type='private',
        participants=user_profile
    ).filter(
        participants=other_student
    ).first()
    
    if existing_chat:
        return redirect('studysync:chat_room', room_id=existing_chat.id)
    
    # Create new chat room
    chat_room = ChatRoom.objects.create(
        name=f"Chat between {user_profile.user.username} and {other_student.user.username}",
        room_type='private'
    )
    chat_room.participants.add(user_profile, other_student)
    
    return redirect('studysync:chat_room', room_id=chat_room.id)

@login_required
def resource_list(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    resources = Resource.objects.filter(course=course).order_by('-created_at')
    
    context = {
        'course': course,
        'resources': resources,
    }
    return render(request, 'studysync/resource_list.html', context)

@login_required
def upload_resource(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    
    if request.method == 'POST':
        form = ResourceUploadForm(request.POST, request.FILES)
        if form.is_valid():
            resource = form.save(commit=False)
            resource.course = course
            resource.uploaded_by = request.user.studentprofile
            resource.save()
            messages.success(request, 'Resource uploaded successfully!')
            return redirect('resource_list', course_id=course_id)
    else:
        form = ResourceUploadForm()
    
    return render(request, 'studysync/upload_resource.html', {
        'form': form,
        'course': course
    })

@login_required
def resource_detail(request, resource_id):
    resource = get_object_or_404(Resource, id=resource_id)
    
    # Increment view count
    resource.views += 1
    resource.save()
    
    if request.method == 'POST':
        comment_form = ResourceCommentForm(request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.resource = resource
            comment.author = request.user.studentprofile
            comment.save()
            messages.success(request, 'Comment added successfully!')
            return redirect('resource_detail', resource_id=resource_id)
    else:
        comment_form = ResourceCommentForm()
    
    context = {
        'resource': resource,
        'comments': resource.comments.all().order_by('-created_at'),
        'comment_form': comment_form,
    }
    return render(request, 'studysync/resource_detail.html', context)

@login_required
def session_detail(request):
    return render(request, 'studysync/resource_detail.html')