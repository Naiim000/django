from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, Http404
from django.conf import settings
import os

from .models import Course, Student, Enrollment, FileUpload
from .forms import RegisterForm, FileUploadForm
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User

def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            Student.objects.create(user=user)  # Create Student profile
            messages.success(request, "Registration successful. Please login.")
            return redirect('login')
    else:
        form = RegisterForm()
    return render(request, 'students/register.html', {'form': form})

def user_login(request):
    if request.user.is_authenticated:
        return redirect('course_list')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            return redirect('course_list')
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()
    return render(request, 'students/login.html', {'form': form})

@login_required
def user_logout(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('login')

@login_required
def course_list(request):
    courses = Course.objects.all()
    student = get_object_or_404(Student, user=request.user)
    enrolled_courses = Enrollment.objects.filter(student=student).values_list('course_id', flat=True)
    return render(request, 'students/course_list.html', {'courses': courses, 'enrolled_courses': enrolled_courses})

@login_required
def enroll_course(request, course_id):
    student = get_object_or_404(Student, user=request.user)
    course = get_object_or_404(Course, id=course_id)
    enrollments_count = Enrollment.objects.filter(student=student).count()

    if enrollments_count >= 5:
        messages.error(request, "You cannot enroll in more than 5 courses.")
        return redirect('course_list')

    enrollment, created = Enrollment.objects.get_or_create(student=student, course=course)
    if created:
        messages.success(request, f"You have enrolled in {course.name}.")
    else:
        messages.info(request, "You are already enrolled in this course.")
    return redirect('course_list')

@login_required
def my_courses(request):
    student = get_object_or_404(Student, user=request.user)
    enrollments = Enrollment.objects.filter(student=student).select_related('course')
    return render(request, 'students/my_courses.html', {'enrollments': enrollments})

@login_required
def upload_file(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    student = get_object_or_404(Student, user=request.user)
    # Only enrolled students can upload files
    if not Enrollment.objects.filter(student=student, course=course).exists():
        messages.error(request, "You must be enrolled in the course to upload files.")
        return redirect('course_list')

    if request.method == 'POST':
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            file_upload = form.save(commit=False)
            file_upload.uploaded_by = request.user
            file_upload.course = course
            file_upload.save()
            messages.success(request, "File uploaded successfully.")
            return redirect('my_courses')
    else:
        form = FileUploadForm()
    return render(request, 'students/upload_file.html', {'form': form, 'course': course})

@login_required
def download_file(request, file_id):
    file_obj = get_object_or_404(FileUpload, id=file_id)
    file_path = file_obj.file.path

    if os.path.exists(file_path):
        with open(file_path, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type="application/octet-stream")
            response['Content-Disposition'] = f'attachment; filename={os.path.basename(file_path)}'
            return response
    raise Http404

@login_required
def delete_file(request, file_id):
    file_obj = get_object_or_404(FileUpload, id=file_id)

    # Only uploader or admin can delete the file
    if request.user != file_obj.uploaded_by and not request.user.is_staff:
        messages.error(request, "You do not have permission to delete this file.")
        return redirect('my_courses')

    if request.method == 'POST':
        file_obj.file.delete()
        file_obj.delete()
        messages.success(request, "File deleted successfully.")
        return redirect('my_courses')

    return render(request, 'students/confirm_delete.html', {'file': file_obj})
