from django.db import models


class Reaction(models.Model):
    reaction = models.fields.CharField(max_length=100)
    message = models.fields.BigIntegerField()
    users = models.ManyToManyField('UserSettings', related_name='reactions', blank=True)
    channel = models.ForeignKey('ChannelSettings', on_delete=models.DO_NOTHING, null=True)
