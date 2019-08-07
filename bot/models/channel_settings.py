import json
from typing import List

from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django_extensions.db.models import TimeStampedModel
from telegram import Chat

from bot.utils.internal import bot_not_running_protect


class ChannelSettings(TimeStampedModel):
    channel_id = models.fields.BigIntegerField(primary_key=True)
    channel_username = models.fields.CharField(max_length=200, blank=True, null=True)
    channel_title = models.fields.CharField(max_length=200, blank=True, null=True)

    added_by = models.ForeignKey('UserSettings', on_delete=models.DO_NOTHING)
    users = models.ManyToManyField('UserSettings', related_name='channels', blank=True)

    caption = models.fields.TextField(blank=True, null=True)
    image_caption = models.fields.TextField(blank=True, null=True)
    image_caption_direction = models.fields.CharField(
        default='nw',
        choices=[
            ('n', 'North'),
            ('nw', 'North-west'),
            ('w', 'West'),
            ('sw', 'South-west'),
            ('s', 'South'),
            ('se', 'South-east'),
            ('e', 'East'),
            ('ne', 'North-east')
        ],
        max_length=2
    )
    _reactions = models.fields.TextField(blank=True, null=True)

    def __str__(self):
        return f'{self.channel_id}:{self.name}'

    @property
    def name(self) -> str:
        if self.channel_title:
            return self.channel_title
        elif self.channel_username:
            return f'@{self.channel_username}'
        return str(self.channel_id)

    @property
    @bot_not_running_protect
    def chat(self) -> Chat:
        from bot.telegrambot import my_bot
        return my_bot.bot.get_chat(self.channel_id)

    def save(self, **kwargs):
        if kwargs.get('auto_update', False):
            self.auto_update_values(save=False)
            kwargs.pop('auto_update')
        super().save(**kwargs)

    def auto_update_values(self, chat: Chat = None, save=True) -> bool:
        chat = chat or self.chat
        if chat:
            self.channel_username = chat.username
            self.channel_title = chat.title

            if save:
                self.save()
            return True
        return False

    @property
    def reactions(self) -> List[str]:
        return json.loads(self._reactions or '[]')

    @reactions.setter
    def reactions(self, value: List[str]):
        self._reactions = json.dumps(value or [])


@receiver(pre_save)
def fill_user_if_necessary(sender, instance, *args, **kwargs):
    if isinstance(instance, ChannelSettings) and (instance.added_by and not instance.users):
        instance.users.add(instance.added_by)
