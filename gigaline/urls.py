from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from django.shortcuts import render
from applications.tariff.models import Tariff
from gigaline import settings


schema_view = get_schema_view(
    openapi.Info(

        title = "Authentication API",
        default_version = 'v1',
        description = 'SomeDescription'
    ),
    public=True
)

def home_view(request):
    tariffs = Tariff.objects.all()
    return render(request, 'index.html', {'tariffs': tariffs})

urlpatterns = [
    path("", home_view, name="index"),
    path("swagger/", schema_view.with_ui()),
    path('admin/', admin.site.urls),
    path('account/', include('applications.account.urls')),
    path('tariff/', include('applications.tariff.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
