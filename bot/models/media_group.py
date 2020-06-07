from django.db import models
from django_extensions.db.models import TimeStampedModel


class MediaGroup(TimeStampedModel):
    id = models.fields.BigIntegerField(primary_key=True)
    message_id = models.fields.BigIntegerField()
    edited = models.fields.BooleanField(default=False)

    channel = models.ForeignKey('ChannelSettings',
                                related_name='media_groups',
                                on_delete=models.DO_NOTHING,
                                blank=True,
                                null=True)

    def __int__(self):
        return self.id

    def __str__(self):
        return f'{self.channel.name}:{self.id}:{self.message_id}'
