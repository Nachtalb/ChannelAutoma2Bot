from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import SafeText, mark_safe

from bot.models.channel_settings import ChannelSettings
from bot.models.reactions import Reaction
from bot.models.usersettings import UserSettings

link_template = '<a href="{link}" target={target}>{text}</a>'


def admin_channel_link(channel: ChannelSettings) -> SafeText:
    url = reverse(f'admin:bot_channelsettings_change', args=(channel.channel_id,))
    return format_html(link_template, link=url, text=channel.name, target='_self')


def admin_user_link(user: UserSettings) -> SafeText:
    url = reverse(f'admin:bot_usersettings_change', args=(user.user_id,))
    return format_html(link_template, link=url, text=user.name, target='_self')


class UserSettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Infos', {
            'fields': ('user_id', 'username', 'user_fullname')
        }),
        ('Bot State', {
            'fields': ('_user_state', 'current_channel'),
        }),
    )

    list_display = ['user_id', 'username_tg', 'user_fullname', 'channel__names', 'current_channel__link', 'modified', 'created']
    list_filter = ['channels']

    def current_channel__link(self, obj: UserSettings) -> SafeText or None:
        if obj.current_channel:
            return admin_channel_link(obj.current_channel)
        return

    def username_tg(self, obj: UserSettings) -> SafeText or str:
        # if obj.user and obj.user.link:
        #     return format_html(link_template, link=obj.user.link, text=obj.name, target='_blank')
        return obj

    def channel__names(self, obj: UserSettings) -> SafeText:
        return mark_safe(', '.join(map(admin_channel_link, obj.channels.all())))


admin.site.register(UserSettings, UserSettingsAdmin)


class ChannelSettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Infos', {
            'fields': ('channel_id', 'channel_username', 'channel_title')
        }),
        ('User', {
            'fields': ('added_by', 'users'),
        }),
        ('Reaction', {
            'fields': ('_reactions',),
        }),
        ('Captions', {
            'fields': ('caption', 'image_caption', 'image_caption_font', 'image_caption_direction'),
        }),
    )


    list_display = [
        'channel_id', 'channel_tg', 'channel_title', 'added_by_user', 'caption_small', 'image_caption_small', 'reactions', 'modified', 'created'
    ]

    def channel_tg(self, obj: ChannelSettings) -> SafeText or str:
        if obj.chat and obj.chat.link:
            return format_html(link_template, link=obj.chat.link, text=obj.name, target='_blank')
        return obj.name

    def added_by_user(self, obj: ChannelSettings) -> SafeText or str:
        return admin_user_link(obj.added_by)

    def caption_small(self, obj):
        if not obj.caption or len(obj.caption) <= 100:
            return obj.caption
        return f'{obj.caption[:100]} ...'

    def image_caption_small(self, obj):
        if not obj.image_caption or len(obj.image_caption) <= 100:
            return obj.image_caption
        return f'{obj.image_caption[:100]} ...'


admin.site.register(ChannelSettings, ChannelSettingsAdmin)


class ReactionsAdmin(admin.ModelAdmin):
    list_display = ['reaction', 'message', 'channel_link', 'users__count', 'created']
    list_filter = ['channel']

    def channel_link(self, obj: Reaction) -> SafeText:
        return admin_channel_link(obj.channel)

    def users__count(self, obj):
        return obj.users.count()

    users__count.admin_order_field = 'users__count'


admin.site.register(Reaction, ReactionsAdmin)
