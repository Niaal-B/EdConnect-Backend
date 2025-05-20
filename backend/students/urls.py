from django.urls import path
from students.views import StudentLoginView 

urlpatterns = [
    path('login/',StudentLoginView.as_view(),name="student-login")
]