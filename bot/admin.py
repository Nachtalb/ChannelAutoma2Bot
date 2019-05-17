from django.contrib import admin

from bot.models.channel_settings import ChannelSettings
from bot.models.usersettings import UserSettings


class UserSettingsAdmin(admin.ModelAdmin):
    list_display = ['user_id', 'name', 'link']


admin.site.register(UserSettings, UserSettingsAdmin)


class ChannelSettingsAdmin(admin.ModelAdmin):
    pass


admin.site.register(ChannelSettings, ChannelSettingsAdmin)
