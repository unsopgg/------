from django.shortcuts import render, get_object_or_404, redirect
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.http import JsonResponse
from rest_framework.views import APIView
from django.contrib.auth.decorators import login_required
from .models import Tariff, Request
from .serializers import *
from django.contrib.auth import get_user_model
from .tasks import *
from rest_framework.authtoken.models import Token
import datetime
User = get_user_model()

def tariff_list_view(request):
    if request.method == 'GET':
        tariffs = Tariff.objects.all()
        context = {"tariffs": tariffs}
        return render(request, 'tariff_list.html', context)

    elif request.method == 'POST':
        # Проверка прав доступа для создания тарифов
        if not request.user.is_staff:
            return JsonResponse({"detail": "Доступ запрещен."}, status=403)

        title = request.POST.get('title')
        description = request.POST.get('description')
        price = request.POST.get('price')

        # Проверка на наличие всех обязательных полей
        if not all([title, description, price]):
            return JsonResponse({"detail": "Все поля обязательны."}, status=400)

        # Создание нового тарифа
        Tariff.objects.create(title=title, description=description, price=price)

        # Перенаправление на список тарифов после успешного создания
        return redirect('tariff_list')


@login_required
def request_list_view(request):
    if request.user.is_staff:
        status_filter = request.GET.get('status', '')
        price_status_filter = request.GET.get('price_status', '')
        requests = Request.objects.all()
        if status_filter:
            requests = requests.filter(status=status_filter)
        if price_status_filter:
            requests = requests.filter(price_status=price_status_filter)
    else:
        requests = Request.objects.filter(user=request.user)
    
    return render(request, 'request_list.html')



@login_required
def request_create_view(request):
    # Проверяем, есть ли уже заявка от текущего пользователя
    user_request = Request.objects.filter(user=request.user).first()
    if user_request:
        return render(request, 'request_create.html', {'user_request': user_request})
    
    if request.method == 'GET':
        tariffs = Tariff.objects.all()
        return render(request, 'request_create.html', {'tariffs': tariffs})
    
    elif request.method == 'POST':
        tarif_id = request.POST.get('tarif')
        adress = request.POST.get('adress')

        if not all([tarif_id, adress]):
            return JsonResponse({"detail": "Тариф и адрес обязательны."}, status=400)

        try:
            tarif = Tariff.objects.get(id=tarif_id)
        except Tariff.DoesNotExist:
            return JsonResponse({"detail": "Указанный тариф не найден."}, status=404)

        Request.objects.create(
            user=request.user,
            tarif=tarif,
            adress=adress,
            date_of_application=datetime.date.today(),
            status='WAITING',
            price_status='unpaid'
        )
        admin_emails = User.objects.filter(is_staff=True).values_list('email', flat=True)
        send_request_mail(list(admin_emails))
        return redirect('request_list')


@login_required
def request_admin_view(request):
    if not request.user.is_staff:
        return JsonResponse({"detail": "Доступ запрещен."}, status=403)

    status_filter = request.GET.get('status', '')
    price_status_filter = request.GET.get('price_status', '')

    requests = Request.objects.all()
    if status_filter:
        requests = requests.filter(status=status_filter)
    if price_status_filter:
        requests = requests.filter(price_status=price_status_filter)

    if request.method == "POST":
        pk = request.POST.get("request_id")
        status_update = request.POST.get("status")
        request_obj = get_object_or_404(Request, pk=pk)

        if status_update not in dict(Request.STATUS_CHOICES):
            return JsonResponse({"detail": "Некорректный статус."}, status=400)

        request_obj.status = status_update
        request_obj.save()
        return redirect("request_admin")

    return render(
        request,
        "request_admin.html",
        {
            "requests": requests,
            "status_choices": Request.STATUS_CHOICES,
            "price_status_choices": Request.PRICE_STATUS_CHOICES,
        },
    )


def payment_view(request, pk):
    request_obj = get_object_or_404(Request, pk=pk, user=request.user)

    if request_obj.price_status == 'PAID':
        return JsonResponse({"detail": "Заявка уже оплачена."}, status=400)

    request_obj.price_status = 'PAID'
    request_obj.save()

    return JsonResponse({"detail": "Оплата успешно завершена."}, status=200)