from django.urls import path
from .views import *

urlpatterns = [
    path('tariffs/', tariff_list_view, name='tariff_list'),  # Обновлено на функциональное представление
    path('requests/', request_view, name='request_list'),  # Обновлено на функциональное представление
    path('request/<int:pk>/', request_detail, name='request_detail'),
    path('admin/requests/', request_admin_view, name='request_admin'),  # Обновлено на функциональное представление
    path('payment/<int:pk>/', payment_view, name='payment'),  # Обновлено на функциональное представление
]
