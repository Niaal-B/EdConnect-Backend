from django.urls import path

from students.views import (StudentDashboardStatsView, StudentLoginView,
                            StudentProfileView)

urlpatterns = [
    path('login/',StudentLoginView.as_view(),name="student-login"),
    path('profile/', StudentProfileView.as_view(), name='student-profile'),
    path('dashboard/',StudentDashboardStatsView.as_view(),name='student-dashboard'),

]