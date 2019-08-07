from django.contrib import admin

from bot.models.channel_settings import ChannelSettings
from bot.models.reactions import Reaction
from bot.models.usersettings import UserSettings


class UserSettingsAdmin(admin.ModelAdmin):
    list_display = ['user_id', 'username', 'user_fullname', 'channel__names', 'modified', 'created']
    list_filter = ['channels']

    def channel__names(self, obj):
        return list(map(lambda o: o.name, obj.channels.all()))


admin.site.register(UserSettings, UserSettingsAdmin)


class ChannelSettingsAdmin(admin.ModelAdmin):
    list_display = [
        'channel_id', 'name', 'added_by', 'caption_small', 'image_caption_small', 'reactions', 'modified', 'created'
    ]

    def caption_small(self, obj):
        if not obj.caption:
            return None
        return f'{obj.caption[:100]}...'

    def image_caption_small(self, obj):
        if not obj.image_caption:
            return None
        return f'{obj.image_caption[:100]}...'


admin.site.register(ChannelSettings, ChannelSettingsAdmin)


class ReactionsAdmin(admin.ModelAdmin):
    list_display = ['reaction', 'message', 'channel__name', 'users__count', 'created']
    list_filter = ['message', 'channel']

    def channel__name(self, obj):
        return obj.channel.name

    channel__name.admin_order_field = 'channel__name'

    def users__count(self, obj):
        return obj.users.count()

    users__count.admin_order_field = 'users__count'


admin.site.register(Reaction, ReactionsAdmin)
