from django.conf.urls import url
from django.contrib import admin
from django.shortcuts import redirect
from django.urls import include, path

from bot.views import redirec_to_admin_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', redirec_to_admin_view),
    url(r'^', include('django_telegrambot.urls')),
]
