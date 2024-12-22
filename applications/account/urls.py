from django.urls import path
from .views import *

urlpatterns = [
    path('register/', registration_view, name='register'),  # Обновлено на функциональное представление
    path('activate/<str:activation_code>/', activation_view, name='activate'),  # Обновлено на функциональное представление
    path('login/', login_view, name='login'),  # Обновлено на функциональное представление
    path('logout/', logout_view, name='logout'),  # Обновлено на функциональное представление
]
