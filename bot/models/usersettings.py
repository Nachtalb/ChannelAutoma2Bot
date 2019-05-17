from cached_property import cached_property_ttl
from django.db import models
from telegram import User

from bot.telegrambot import my_bot
from bot.utils import bot_not_running_protect


class UserSettings(models.Model):
    user_id = models.fields.BigIntegerField(primary_key=True)
    _user: User = None  # Actual telegram User object

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
