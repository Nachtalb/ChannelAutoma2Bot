from typing import Iterator

from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import SafeText, mark_safe
from telegram import Bot

from bot.models.channel_settings import ChannelSettings
from bot.models.reactions import Reaction
from bot.models.usersettings import UserSettings
from bot import telegrambot as tb

link_template = '<a href="{link}" target={target}>{text}</a>'


class AdminHelper:
    _cached_bots = {}

    def resolve_bot_name(self, bot_token: str):
        if bot_token not in self._cached_bots and tb.my_bot:
            bot: Bot = next(iter([bot for bot in tb.my_bot.bots if bot.token == bot_token]), None)
            if bot:
                me = bot.get_me()
                self._cached_bots[bot_token] = (me.full_name, me.link)
        return self._cached_bots.get(bot_token, (None, None))

    def bot_link(self, obj: ChannelSettings or UserSettings) -> SafeText:
        name, url = self.resolve_bot_name(obj.bot_token)
        if not name or not url:
            return ''
        return format_html(link_template, link=url, text=name, target='_blank')

    def channel_link(self, channel: ChannelSettings) -> SafeText:
        url = reverse(f'admin:bot_channelsettings_change', args=(channel.id,))
        return format_html(link_template, link=url, text=channel.name, target='_self')

    def user_link(self, user: UserSettings) -> SafeText:
        url = reverse(f'admin:bot_usersettings_change', args=(user.id,))
        return format_html(link_template, link=url, text=user.name, target='_self')

    channel_link.short_description = "Channel"
    user_link.short_description = "User"
    bot_link.short_description = 'Bot'


class UserSettingsAdmin(admin.ModelAdmin, AdminHelper):
    fieldsets = (
        ('Infos', {
            'fields': ('user_id', 'username', 'user_fullname')
        }),
        ('Bot State', {
            'fields': ('_user_state', 'current_channel'),
        }),
        ('Misc', {
            'fields': ('channel__names_list', 'bot_link'),
        }),
    )

    readonly_fields = ['channel__names_list', 'bot_link']

    list_display = ['user_id', 'username_tg', 'user_fullname', 'channel__names', 'bot_link', 'current_channel__link',
                    'modified', 'created']
    list_filter = ['channels']

    def current_channel__link(self, obj: UserSettings) -> SafeText or None:
        if obj.current_channel:
            return self.channel_link(obj.current_channel)
        return

    def username_tg(self, obj: UserSettings) -> SafeText or str:
        # if obj.user and obj.user.link:
        #     return format_html(link_template, link=obj.user.link, text=obj.name, target='_blank')
        return obj

    def resolved_channels(self, obj: UserSettings) -> Iterator[SafeText]:
        return map(self.channel_link, obj.channels.all())

    def channel__names(self, obj: UserSettings) -> SafeText:
        return mark_safe(', '.join(self.resolved_channels(obj)))

    def channel__names_list(self, obj: UserSettings) -> SafeText:
        return mark_safe(
            '<ul>{}<ul/>'.format(
                ''.join([f'<li>{link}</li>' for link in self.resolved_channels(obj)])
            )
        )

    channel__names.short_description = channel__names_list.short_description = 'Channels'


admin.site.register(UserSettings, UserSettingsAdmin)


class ChannelSettingsAdmin(admin.ModelAdmin, AdminHelper):
    fieldsets = (
        ('Infos', {
            'fields': ('channel_id', 'channel_username', 'channel_title')
        }),
        ('User', {
            'fields': ('resolved_added_by_user', 'resolved_users'),
        }),
        ('Reaction', {
            'fields': ('_reactions',),
        }),
        ('Captions', {
            'fields': ('caption', 'image_caption', 'image_caption_font', 'image_caption_direction'),
        }),
    )

    readonly_fields = ['resolved_added_by_user', 'resolved_users']

    list_display = [
        'channel_id', 'channel_tg', 'channel_title', 'resolved_added_by_user', 'caption_small', 'image_caption_small',
        'bot_link', 'reactions', 'modified', 'created'
    ]

    def channel_tg(self, obj: ChannelSettings) -> SafeText or str:
        if obj.chat and obj.chat.link:
            return format_html(link_template, link=obj.chat.link, text=obj.name, target='_blank')
        return obj.name

    def resolved_added_by_user(self, obj: ChannelSettings) -> SafeText or str:
        return self.user_link(obj.added_by)

    def resolved_users(self, obj: ChannelSettings) -> SafeText or str:
        return SafeText(','.join(map(self.user_link, obj.users.all())))

    def caption_small(self, obj):
        if not obj.caption or len(obj.caption) <= 100:
            return obj.caption
        return f'{obj.caption[:100]} ...'

    def image_caption_small(self, obj):
        if not obj.image_caption or len(obj.image_caption) <= 100:
            return obj.image_caption
        return f'{obj.image_caption[:100]} ...'

    resolved_added_by_user.short_description = 'Added By'
    resolved_users.short_description = 'Administrated by'


admin.site.register(ChannelSettings, ChannelSettingsAdmin)


class ReactionsAdmin(admin.ModelAdmin, AdminHelper):
    list_display = ['reaction', 'message', 'resolved_channel_link', 'users__count', 'created']
    list_filter = ['channel']

    def resolved_channel_link(self, obj: Reaction) -> SafeText:
        return self.channel_link(obj.channel)

    def users__count(self, obj):
        return obj.users.count()

    users__count.admin_order_field = 'users__count'


admin.site.register(Reaction, ReactionsAdmin)
