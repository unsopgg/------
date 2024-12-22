from django.shortcuts import render, redirect
from rest_framework import status, generics
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Tariff, Request
from .serializers import TariffSerializer, RequestSerializer
from django.contrib.auth import get_user_model
from rest_framework.generics import get_object_or_404
from .tasks import *
import datetime

User = get_user_model()

class TariffView(APIView):
    def get(self, request):
        tariffs = Tariff.objects.all()
        serializer = TariffSerializer(tariffs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class TariffAdminView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request):
        data = request.data
        serializer = TariffSerializer(data=data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response('Тариф добавлен!', status=status.HTTP_201_CREATED)

    def get(self, request):
        tariffs = Tariff.objects.all()
        serializer = TariffSerializer(tariffs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class RequestView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.is_staff:
            requests = Request.objects.filter(user=request.user)
            serialized_requests = []
            for req in requests:
                serialized_data = RequestSerializer(req).data
                if req.price_status == 'PAID':
                    serialized_data['message'] = 'Ожидайте подключения'
                serialized_requests.append(serialized_data)
            return Response(serialized_requests, status=status.HTTP_200_OK)
        else:
            requests = Request.objects.all()
            serializer = RequestSerializer(requests, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

class RequestCreateView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Request.objects.all()
    serializer_class = RequestSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user, date_of_application=datetime.date.today(), status='WAITING', price_status='unpaid')
        admin_emails = User.objects.filter(is_staff=True).values_list('email', flat=True)
        send_request_mail(list(admin_emails))

class RequestAdminView(APIView):
    permission_classes = [IsAdminUser]

    def patch(self, request, pk):
        request_obj = get_object_or_404(Request, pk=pk)
        status_update = request.data.get('status')
        if status_update not in dict(Request.STATUS_CHOICES):
            return Response({"error": "Некорректный статус."}, status=status.HTTP_400_BAD_REQUEST)
        request_obj.status = status_update
        request_obj.save()
        if request_obj.user and request_obj.user.email:
            send_status_mail(request_obj.user.email)
        return Response('Статус заявки обновлен!', status=status.HTTP_200_OK)

class PaymentView(APIView): 
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        request_obj = get_object_or_404(Request, pk=pk, user=request.user)
        if request_obj.price_status == 'PAID':
            return Response('Заявка уже оплачена.', status=status.HTTP_400_BAD_REQUEST)
        request_obj.price_status = 'PAID'
        request_obj.save()
        return Response('Оплата проведена успешно!', status=status.HTTP_200_OK)

def tariff_list_view(request):
    tariffs = Tariff.objects.all()
    
    # Check if the user is an admin and has submitted the form
    if request.method == 'POST' and request.user.is_staff:
        # Handle tariff creation
        title = request.POST.get('title')
        description = request.POST.get('description')
        price = request.POST.get('price')
        
        if title and description and price:
            new_tariff = Tariff.objects.create(title=title, description=description, price=price)
            return redirect('tariff_list')  # Redirect after creating a new tariff
    
    return render(request, 'tariff_list.html', {'tariffs': tariffs})
