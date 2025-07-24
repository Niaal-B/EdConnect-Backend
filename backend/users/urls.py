from django.urls import path
from .views import UserRegistrationView,VerifyEmailView,LogoutView

urlpatterns = [
    path("register/", UserRegistrationView.as_view(), name="register"),
    path("verify-email/<str:token>/", VerifyEmailView.as_view(), name="verify_email"),
    path("logout/",LogoutView.as_view(),name="logout")
    
    ]
