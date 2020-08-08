from django.conf.urls import url
from django.contrib import admin
from django.urls import include, path

from bot.views import redirect_to_admin_view, MigrateToBotView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', redirect_to_admin_view),
    path('migrate/', MigrateToBotView.as_view()),
    url(r'^', include('django_telegrambot.urls')),
]
