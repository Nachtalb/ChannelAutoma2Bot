from cached_property import cached_property_ttl
from django.db import models
from telegram import User

from bot.telegrambot import my_bot
from bot.utils.internal import bot_not_running_protect


class UserSettings(models.Model):
    IDLE = 'idle'
    SET_CAPTION_MENU = 'set caption menu'
    SET_CAPTION = 'set caption'
    SETTINGS_MENU = 'settings menu'
    CHANNEL_SETTINGS_MENU = 'channel settings menu'
    PRE_REMOVE_CHANNEL = 'pre remove channel'

    STATES = (IDLE, SET_CAPTION_MENU, SET_CAPTION, SETTINGS_MENU, CHANNEL_SETTINGS_MENU, PRE_REMOVE_CHANNEL)

    user_id = models.fields.BigIntegerField(primary_key=True)
    _user: User = None  # Actual telegram User object

    current_channel = models.ForeignKey('ChannelSettings',
                                        related_name='current_user',
                                        on_delete=models.DO_NOTHING,
                                        blank=True,
                                        null=True)

    _user_state = models.fields.CharField(max_length=100,
                                          choices=map(lambda s: (s, s), STATES),
                                          default=IDLE,
                                          verbose_name='State')

    @property
    def state(self):
        return self._user_state

    @state.setter
    def state(self, value):
        if value not in self.STATES:
            raise KeyError('State does no exists')

        self._user_state = value
        self.save()

    @cached_property_ttl(ttl=3600)
    @bot_not_running_protect
    def name(self) -> str:
        return self.user.username or self.user.full_name

    @cached_property_ttl(ttl=3600)
    @bot_not_running_protect
    def link(self) -> str:
        return self.user.link

    @property
    @bot_not_running_protect
    def user(self) -> User:
        if not self._user:
            self._user = my_bot.updater.bot.get_chat(self.user_id)
        return self._user
