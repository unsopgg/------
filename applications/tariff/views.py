from django.shortcuts import render, get_object_or_404, redirect
from rest_framework import status, generics
from django.views.generic import ListView, DetailView
from rest_framework.permissions import IsAuthenticated
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response 
from .models import Tariff, Request
from .serializers import RequestSerializer
from django.contrib.auth import get_user_model
from .tasks import *
import datetime
User = get_user_model()

# Tariff List View (for regular users)
class TariffListView(ListView):
    model = Tariff
    template_name = 'tariff_list.html'  
    context_object_name = 'tariffs'

    def post(self, request, *args, **kwargs):
        if request.user.is_staff:
            title = request.POST.get('title')
            description = request.POST.get('description')
            price = request.POST.get('price')

            if title and description and price:
                Tariff.objects.create(title=title, description=description, price=price)
                return redirect('tariff_list')  # Redirect after creating a new tariff
        return super().post(request, *args, **kwargs)


class RequestListView(ListView):
    model = Request
    template_name = 'requests.html'
    context_object_name = 'requests'

    # Переписанный метод для получения queryset
    def get_queryset(self):
        if self.request.user.is_staff:
            # Для администраторов, фильтрация по статусу и статусу оплаты
            status_filter = self.request.GET.get('status', '')
            price_status_filter = self.request.GET.get('price_status', '')
            requests = Request.objects.all()

            if status_filter:
                requests = requests.filter(status=status_filter)
            if price_status_filter:
                requests = requests.filter(price_status=price_status_filter)

        elif self.request.user.is_authenticated:
            # Для аутентифицированных пользователей
            requests = Request.objects.filter(user=self.request.user)
        else:
            # Для анонимных пользователей, возвращаем пустой queryset
            requests = Request.objects.none()

        return requests

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tariffs'] = Tariff.objects.all()
        if not self.request.user.is_staff:
            # Для обычных пользователей, если заявка существует, передаем первую заявку в контекст
            user_request = self.get_queryset().first() if self.get_queryset().exists() else None
            context['user_request'] = user_request
        return context

class RequestCreateView(generics.CreateAPIView):
    queryset = Request.objects.all()
    serializer_class = RequestSerializer

    def perform_create(self, serializer):
        if self.request.user.is_authenticated:
            # Получение тарифов и их сохранение
            tarif_id = self.request.data.get('tarif')
            tarif = Tariff.objects.get(id=tarif_id)

            # Сохранение данных заявки
            serializer.save(
                user=self.request.user,
                tarif=tarif,
                adress=self.request.data.get('adress'),
                date_of_application=datetime.date.today(),
                status='WAITING',
                price_status='unpaid'
            )
            admin_emails = User.objects.filter(is_staff=True).values_list('email', flat=True)
            send_request_mail(list(admin_emails))
            return redirect('requests')
        else:
            return redirect('login')

# Admin Request Management
class RequestAdminView(DetailView):
    model = Request
    template_name = 'requests.html'
    context_object_name = 'request'
    
    def post(self, request, *args, **kwargs):
        # Получаем объект заявки
        request_obj = self.get_object()
        status_update = request.POST.get('status')

        if status_update not in dict(Request.STATUS_CHOICES):
            return JsonResponse({"error": "Некорректный статус."}, status=400)
        
        request_obj.status = status_update
        request_obj.save()
        
        # Отправляем email пользователю о статусе
        if request_obj.user and request_obj.user.email:
            send_status_mail(request_obj.user.email)

        return render(request, 'requests.html', {'request': request_obj})
# Payment View
class PaymentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        request_obj = get_object_or_404(Request, pk=pk, user=request.user)
        
        if request_obj.price_status == 'PAID':
            return Response('Заявка уже оплачена.', status=status.HTTP_400_BAD_REQUEST)
        
        request_obj.price_status = 'PAID'
        request_obj.save()
        
        return render(request, 'payment_success.html', {'request': request_obj})