from django.db.models.signals import pre_save
from django.dispatch import receiver
from telegram import Chat

from django.db import models

from bot.telegrambot import my_bot
from bot.utils import bot_not_running_protect


class ChannelSettings(models.Model):
    channel_id = models.fields.BigIntegerField(primary_key=True)
    channel_username = models.fields.CharField(max_length=200, blank=True, null=True)
    channel_title = models.fields.CharField(max_length=200, blank=True, null=True)

    added_by = models.ForeignKey('UserSettings', on_delete=models.DO_NOTHING)
    users = models.ManyToManyField('UserSettings', related_name='channels', blank=True)

    caption = models.fields.TextField(blank=True, null=True)

    def update_from_chat(self, chat: Chat):
        self.channel_username = chat.username
        self.channel_title = chat.title

    @property
    def name(self) -> str:
        return self.channel_title or '@' + self.channel_username

    @property
    @bot_not_running_protect
    def chat(self) -> Chat:
        return my_bot.updater.bot.get_chat(self.channel_id)

    @bot_not_running_protect
    def auto_update_values(self, save=True):
        self.update_from_chat(self.chat)
        if save:
            self.save()


@receiver(pre_save)
def fill_user_if_necessary(sender, instance, *args, **kwargs):
    if isinstance(instance, ChannelSettings) and (instance.added_by and not instance.users):
        instance.users.add(instance.added_by)
