from django.urls import path,include
from .views import hello_api

urlpatterns = [
    path('hello/', hello_api),
    path('user/',include('users.urls')),
    path('mentors/', include('mentors.urls')),
    path('students/',include('students.urls')),
    path('auth/',include('auth.urls')),
    path('admin/',include('admin.urls')),
    path('connections/',include('connections.urls')),
    path('chat/',include('chat_app.urls')),
    path('bookings/',include('bookings.urls'))
    


]
