from cached_property import cached_property_ttl
from django.db import models
from django_extensions.db.models import TimeStampedModel
from telegram import User
from telegram.error import Unauthorized, BadRequest

from bot.utils.internal import bot_not_running_protect, first


class UserSettings(TimeStampedModel):
    SET_REACTIONS_MENU = 'set reactions menu'
    SET_REACTIONS = 'set reactions'
    IDLE = 'idle'
    SET_CAPTION_MENU = 'set caption menu'
    SET_CAPTION = 'set caption'
    SET_IMAGE_CAPTION_MENU = 'set image caption menu'
    SET_IMAGE_CAPTION = 'set image caption'
    SET_IMAGE_CAPTION_NEXT = 'set image caption next'
    SET_IMAGE_CAPTION_ALPHA = 'set image caption alpha'
    SET_FORWARDER_MENU = 'set forwarder menu'
    SET_FORWARDER_TO = 'set forwarder to'
    SETTINGS_MENU = 'settings menu'
    CHANNEL_SETTINGS_MENU = 'channel settings menu'
    PRE_REMOVE_CHANNEL = 'pre remove channel'

    STATES = (IDLE, SET_CAPTION_MENU, SET_CAPTION, SETTINGS_MENU, CHANNEL_SETTINGS_MENU, PRE_REMOVE_CHANNEL,
              SET_REACTIONS_MENU, SET_REACTIONS, SET_IMAGE_CAPTION_MENU, SET_IMAGE_CAPTION, SET_IMAGE_CAPTION_NEXT,
              SET_FORWARDER_MENU, SET_FORWARDER_TO, SET_IMAGE_CAPTION_ALPHA)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user_id', 'bot_token'],
                                    name='user_bot_unique')
        ]

    user_id = models.fields.BigIntegerField()
    _user: User = None  # Actual telegram User object

    bot_token = models.fields.CharField(max_length=200)

    current_channel = models.ForeignKey('ChannelSettings',
                                        related_name='current_user',
                                        on_delete=models.DO_NOTHING,
                                        blank=True,
                                        null=True)

    _user_state = models.fields.CharField(max_length=100,
                                          choices=map(lambda s: (s, s), STATES),
                                          default=IDLE,
                                          verbose_name='State')

    username = models.fields.CharField(max_length=200, blank=True, null=True)
    user_fullname = models.fields.CharField(max_length=200)

    zombie = models.fields.BooleanField(default=False)

    def __str__(self):
        return f'{self.name} ({self.user_id})'

    @property
    def name(self) -> str:
        if self.username:
            return f'@{self.username}'
        elif self.user_fullname:
            return self.user_fullname
        return str(self.user_id)

    def save(self, **kwargs):
        if kwargs.get('auto_update', False):
            self.auto_update_values(save=False)
            kwargs.pop('auto_update')
        super().save(**kwargs)

    @property
    def state(self):
        return self._user_state

    @state.setter
    def state(self, value):
        if value not in self.STATES:
            raise KeyError('State does no exists')

        self._user_state = value
        self.save()

    def auto_update_values(self, user: User = None, save=True) -> bool:
        user = user or self.user
        if user:
            self.username = user.username
            self.user_fullname = user.full_name

            if save:
                self.save()
            return True
        return False

    @cached_property_ttl(ttl=3600)
    @bot_not_running_protect
    def link(self) -> str:
        return self.user.link

    @property
    @bot_not_running_protect
    def user(self) -> User:
        from bot.telegrambot import my_bot
        if not self._user:
            try:
                bot = my_bot.get_bot(self.bot_token)
                self._user = bot.get_chat(self.user_id)

                if self.zombie:
                    self.zombie = False
                    self.save(update_fields=['zombie'])
                    print(f'Unmarked {self.name}[{self.user_id}] as a zombie')
            except (Unauthorized, BadRequest):
                if not self.zombie:
                    self.zombie = True
                    self.save(update_fields=['zombie'])
                    print(f'Marked {self.name}[{self.user_id}] as a zombie')
                return None
            except Exception:
                return None
        return self._user
