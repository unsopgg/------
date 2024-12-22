from django.urls import path
from .views import *

urlpatterns = [
    path('tariffs/', tariff_list_view, name='tariff_list'),
    path('tariffs/admin/', TariffAdminView.as_view(), name='tariff_admin'),
    path('requests/', RequestView.as_view(), name='request_list'),
    path('requests/create/', RequestCreateView.as_view(), name='create_request'),
    path('requests/admin/<int:pk>/', RequestAdminView.as_view(), name='request_admin'),
    path('payment/<int:pk>/', PaymentView.as_view(), name='payment'),
]
