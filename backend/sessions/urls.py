from django.urls import path
from . import views

urlpatterns = [
    path('agora/get-token/', views.get_agora_token, name='get_agora_token'),
]