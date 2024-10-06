from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q, Avg
from .models import *


# Create your views here.
def home_view(request):


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
    return render(request, 'studysync/dashboard.html', context)

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
    return render(request, 'studysync/create_session.html', {'courses': courses})

@login_required
def join_session(request, session_id):
    session = get_object_or_404(StudySession, id=session_id)
    if request.method == 'POST':
        if session.students.count() < session.max_participants:
            session.students.add(request.user.studentprofile)
            return JsonResponse({'status': 'success'})
        return JsonResponse({'status': 'full'}, status=400)
    return JsonResponse({'status': 'error'}, status=405)
