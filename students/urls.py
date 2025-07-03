from django.urls import path
from . import views

urlpatterns = [
    path('', views.course_list, name='course_list'),
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('enroll/<int:course_id>/', views.enroll_course, name='enroll_course'),
    path('my-courses/', views.my_courses, name='my_courses'),
    path('upload-file/<int:course_id>/', views.upload_file, name='upload_file'),
    path('files/<int:file_id>/download/', views.download_file, name='download_file'),
    path('files/<int:file_id>/delete/', views.delete_file, name='delete_file'),
]
