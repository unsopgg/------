from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Tariff, Request
from .serializers import *
from django.contrib.auth import get_user_model
from .tasks import *
import datetime
User = get_user_model()

def tariff_list_view(request):
    if request.method == 'GET':
        tariffs = Tariff.objects.all()
        tariff_id = request.GET.get('edit')
        tariff_to_edit = None
        if tariff_id:
            try:
                tariff_to_edit = Tariff.objects.get(id=tariff_id)
            except Tariff.DoesNotExist:
                return JsonResponse({"detail": "Тариф не найден."}, status=404)

        context = {"tariffs": tariffs, "tariff_to_edit": tariff_to_edit}
        return render(request, 'tariff_list.html', context)

    elif request.method == 'POST':
        if not request.user.is_staff:
            return JsonResponse({"detail": "Доступ запрещен."}, status=403)

        # Проверка для создания/обновления тарифа
        tariff_id = request.POST.get('tariff_id')
        if 'delete_tariff' in request.POST:
            # Удаление тарифа
            try:
                tariff = Tariff.objects.get(id=tariff_id)
                tariff.delete()
                return redirect('tariff_list')
            except Tariff.DoesNotExist:
                return JsonResponse({"detail": "Тариф не найден."}, status=404)
        
        # Если это создание или обновление
        title = request.POST.get('title')
        description = request.POST.get('description')
        price = request.POST.get('price')
        
        if not all([title, description, price]):
            return JsonResponse({"detail": "Все поля обязательны."}, status=400)

        if tariff_id:
            try:
                tariff = Tariff.objects.get(id=tariff_id)
                tariff.title = title
                tariff.description = description
                tariff.price = price
                tariff.save()
                return redirect('tariff_list')
            except Tariff.DoesNotExist:
                return JsonResponse({"detail": "Тариф не найден."}, status=404)
        else:
            Tariff.objects.create(title=title, description=description, price=price)
            return redirect('tariff_list')


@login_required
def request_view(request):
    user_request = Request.objects.filter(user=request.user).first()
    # Если заявка уже существует, перенаправляем на страницу детального просмотра
    if user_request:
        return redirect('request_detail', pk=user_request.id)

    if request.method == 'POST':
        tarif_id = request.POST.get('tarif')
        adress = request.POST.get('adress')

        if not all([tarif_id, adress]):
            return JsonResponse({"detail": "Тариф и адрес обязательны."}, status=400)

        try:
            tarif = Tariff.objects.get(id=tarif_id)
        except Tariff.DoesNotExist:
            return JsonResponse({"detail": "Указанный тариф не найден."}, status=404)

        # Создаем новую заявку, если её нет
        new_request = Request.objects.create(
            user=request.user,
            tarif=tarif,
            adress=adress,
            date_of_application=datetime.date.today(),
            status='WAITING',
            price_status='unpaid'
        )
        send_request_mail(User.objects.filter(is_staff=True).values_list('email', flat=True))  # Уведомление администраторов

        # Перенаправляем на страницу детального просмотра новой заявки
        return redirect('request_detail', pk=new_request.id)


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

    return render(
        request,
        "request_admin.html",
        {
            "requests": requests,
            "status_choices": Request.STATUS_CHOICES,
            "price_status_choices": Request.PRICE_STATUS_CHOICES,
        },
    )

@login_required
def request_detail(request, pk):
    user_request = Request.objects.filter(id=pk).first()
    admin_emails = User.objects.filter(is_staff=True).values_list('email', flat=True)
    if not user_request:
        return redirect('request_list')  # Если заявка не найдена, перенаправляем

    # Для администратора данные заявки должны отображаться, но не изменяться
    if request.user == user_request.user or request.user.is_staff:
        if request.method == 'POST':
            # Обработать POST-запрос (для пользователя и администратора)
            tarif_id = request.POST.get('tarif')
            adress = request.POST.get('adress')
            pod = request.POST.get('pod')
            kvar = request.POST.get('kvar')
            phnumber = request.POST.get('phnumber')

            # Проверка, что все обязательные поля заполнены
            if not all([tarif_id, adress, pod, kvar, phnumber]):
                return JsonResponse({"detail": "Все поля обязательны."}, status=400)

            try:
                tarif = Tariff.objects.get(id=tarif_id)
            except Tariff.DoesNotExist:
                return JsonResponse({"detail": "Указанный тариф не найден."}, status=404)

            # Независимо от изменений данных, сбрасываем статус на 'waiting'
            user_request.status = 'waiting'

            # Обновляем поля заявки
            user_request.tarif = tarif
            user_request.adress = adress
            user_request.pod = pod
            user_request.kvar = kvar
            user_request.phnumber = phnumber

            # Сохраняем изменения
            user_request.save()

            # Отправка уведомления администратору о изменении заявки
            send_update_request_mail(list(admin_emails))    

            return redirect('request_list')  # Перенаправляем на список заявок после сохранения изменений

        tariffs = Tariff.objects.all()  # Получаем список всех тарифов для отображения

        # Для администратора форма будет доступна, но без редактирования
        return render(request, 'request_detail.html', {'user_request': user_request, 'tariffs': tariffs})
    else:
        # Для неадминистратора и не владельца заявки показываем только данные
        return render(request, 'request_detail.html', {'user_request': user_request})

def payment_view(request, pk):
    request_obj = get_object_or_404(Request, pk=pk, user=request.user)

    if request_obj.price_status == 'PAID':
        return JsonResponse({"detail": "Заявка уже оплачена."}, status=400)

    request_obj.price_status = 'PAID'
    request_obj.save()

    return JsonResponse({"detail": "Оплата успешно завершена."}, status=200)