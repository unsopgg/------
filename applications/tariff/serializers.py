from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import Tariff, Request
import datetime

User = get_user_model()

class TariffSerializer(serializers.ModelSerializer):
    title = serializers.CharField(
        required=True,
        min_length=2,
        max_length=50,
        error_messages={
            "required": "Имя тарифа обязательно для заполнения.",
            "min_length": "Имя тарифа должно содержать минимум 2 символа.",
            "max_length": "Имя тарифа не должно превышать 50 символов."
        },
    )

    class Meta:
        model = Tariff
        fields = ('id', 'title', 'description', 'price')

    def validate_title(self, title):
        if Tariff.objects.filter(title=title).exists():
            raise serializers.ValidationError('Такой тариф уже существует.')
        return title

    def create(self, validated_data):
        return Tariff.objects.create(**validated_data)

class RequestSerializer(serializers.ModelSerializer):
    tarif = serializers.PrimaryKeyRelatedField(queryset=Tariff.objects.all())
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    date_of_application = serializers.HiddenField(default=datetime.date.today)
    status = serializers.HiddenField(default='WAITING')
    price_status = serializers.HiddenField(default='unpaid')

    class Meta:
        model = Request
        fields = (
            'id', 'tarif', 'user', 'date_of_application', 'status', 'adress', 'price_status'
        )

    def validate(self, data):
        if data['status'] not in dict(Request.STATUS_CHOICES):
            raise serializers.ValidationError({"status": "Некорректный статус заявки."})

        return data

    def create(self, validated_data):
        return Request.objects.create(**validated_data)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if instance.price_status == 'unpaid':
            if instance.status == 'APPROVED':
                representation['price_status'] = "Заявка одобрена, пожалуйста проведите оплату."
            elif instance.status == 'DECLINED':
                representation['status'] = "Заявка не одобрена."
            elif instance.status == 'WAITING':
                representation['status'] = "Заявка рассматривается, ожидайте пожалуйста."
        return representation
