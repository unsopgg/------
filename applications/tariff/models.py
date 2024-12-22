from django.db import models
from ..account.models import *

class Tariff(models.Model):
    title = models.CharField(max_length=50)
    description = models.TextField(max_length=500)
    price = models.IntegerField()

class Request(models.Model):
    STATUS_CHOICES = [
        ('WAITING', 'waiting'),
        ('APPROVED', 'approved'),
        ('DECLINED', 'declined'),
    ]
    PRICE_STATUS_CHOICES = [
        ('PAID', 'paid'),
        ('UNPAID', 'unpaid'),
    ]
    tarif = models.ForeignKey(Tariff, on_delete=models.CASCADE, related_name="tarif")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="tarif")
    date_of_application = models.DateField()
    status = models.CharField(max_length=15, choices=STATUS_CHOICES)
    adress = models.CharField(max_length=50)
    price_status = models.CharField(max_length=15, choices=PRICE_STATUS_CHOICES)

