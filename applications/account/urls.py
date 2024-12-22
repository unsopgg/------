from django.urls import path
from .views import *

urlpatterns = [
    path('register/', RegistrationView.as_view(), name='register'),
    path('activate/<str:activation_code>/', ActivationView.as_view(), name='activate'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('forgot_password/', ForgotPasswordView.as_view(), name='forgot_password'),
    path('forgot_password_complete/<str:verification_code>/', ForgotPasswordCompleteView.as_view()),
    path('debug/', HomeView.as_view()),
    path('test/', ProtectedView.as_view()),
]