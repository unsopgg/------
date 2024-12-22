from django.urls import path
from . import views

urlpatterns = [
    path('tariffs/', views.TariffListView.as_view(), name='tariff_list'),
    path('requests/', views.RequestListView.as_view(), name='request_list'),
    path('create-request/', views.RequestCreateView.as_view(), name='create_request'),
    path('admin/requests/<int:pk>/', views.RequestAdminView.as_view(), name='request_admin'),
    path('payment/<int:pk>/', views.PaymentView.as_view(), name='payment'),
]