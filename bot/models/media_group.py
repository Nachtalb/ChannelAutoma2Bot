from django.db import models
from django_extensions.db.models import TimeStampedModel


class MediaGroup(TimeStampedModel):
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['media_group_id', 'bot_token'],
                                    name='mediagroup_bot_unique')
        ]

    media_group_id = models.fields.BigIntegerField(null=True)
    message_id = models.fields.BigIntegerField()
    edited = models.fields.BooleanField(default=False)

    bot_token = models.fields.CharField(max_length=200)

    channel = models.ForeignKey('ChannelSettings',
                                related_name='media_groups',
                                on_delete=models.DO_NOTHING,
                                blank=True,
                                null=True)

    def __int__(self):
        return self.id

    def __str__(self):
        return f'{self.channel.name}:{self.id}:{self.message_id}'
