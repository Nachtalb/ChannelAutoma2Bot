import json
from typing import List

from cached_property import cached_property_ttl
from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django_extensions.db.models import TimeStampedModel
from telegram import Chat
from telegram.error import Unauthorized, BadRequest


from bot.utils.internal import bot_not_running_protect
from bot.utils.media import Fonts


class ChannelSettings(TimeStampedModel):
    channel_id = models.fields.BigIntegerField(primary_key=True)
    channel_username = models.fields.CharField(max_length=200, blank=True, null=True)
    channel_title = models.fields.CharField(max_length=200, blank=True, null=True)

    added_by = models.ForeignKey('UserSettings', on_delete=models.DO_NOTHING)
    users = models.ManyToManyField('UserSettings', related_name='channels', blank=True)

    forward_to = models.ForeignKey('ChannelSettings',
            related_name='forward_from',
            on_delete=models.DO_NOTHING,
            blank=True,
            null=True)
    caption = models.fields.TextField(blank=True, null=True)
    image_caption = models.fields.TextField(blank=True, null=True)
    image_caption_font = models.fields.TextField(
        default='default', help_text=f'Available fonts: {", ".join(map(lambda font: f"<code>{font}</code>", Fonts))}')
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
            ('ne', 'North-east'),
            ('c', 'Center'),
        ],
        max_length=2
    )
    _reactions = models.fields.TextField(blank=True, null=True)
    zombie = models.fields.BooleanField(default=False)

    def __int__(self):
        return self.channel_id

    def __str__(self):
        return f'{self.channel_id}:{self.name}'

    @property
    def name(self) -> str:
        if self.channel_username:
            return f'@{self.channel_username}'
        elif self.channel_title:
            return self.channel_title
        return str(self.channel_id)

    @property
    @bot_not_running_protect
    def chat(self) -> Chat:
        if self.zombie:
            return None
        from bot.telegrambot import my_bot
        try:
            return my_bot.bot.get_chat(self.channel_id)
        except (Unauthorized, BadRequest):
            self.zombie = True
            self.save(update_fields=['zombie'])
            print('{} | "{}" marked as zombie'.format(self.channel_id, self.channel_title))
            return None
        except:
            return None

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

    def partial_reset(self):
        self.image_caption = None
        self.caption = None
        self.image_caption_direction = 'nw'
        self.image_caption_font = 'default'
        self.save()

    @cached_property_ttl(ttl=3600)
    @bot_not_running_protect
    def link(self) -> str:
        link = self.chat.link or self.chat.invite_link or self.chat.bot.export_chat_invite_link(self.chat.id)
        return f'<a href="{link}">{self.name}</a>'


@receiver(pre_save)
def fill_user_if_necessary(sender, instance, *args, **kwargs):
    if isinstance(instance, ChannelSettings) and (getattr(instance, 'added_by', None) and not instance.users):
        instance.users.add(instance.added_by)
