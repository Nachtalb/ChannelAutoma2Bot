from django.contrib import admin

from bot.models.usersettings import UserSettings


class UserSettingsAdmin(admin.ModelAdmin):
    list_display = ['user_id', 'name', 'link']


admin.site.register(UserSettings, UserSettingsAdmin)
