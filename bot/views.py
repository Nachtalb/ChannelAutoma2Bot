from django import forms
from django.shortcuts import redirect
from django.shortcuts import render
from django.views.generic import FormView
from django.db import transaction
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import StreamingHttpResponse

from bot.models.usersettings import UserSettings
from bot.models.channel_settings import ChannelSettings
from bot.models.reactions import Reaction
from bot import telegrambot as tb
from bot.utils.internal import first


def redirect_to_admin_view(request):
    return redirect('/admin')


class MigrateToBotForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(MigrateToBotForm, self).__init__(*args, **kwargs)
        self.fields['new_bot_token'] = forms.ChoiceField(label='Migrate to',
                                                         choices=self.choices_from_bots())

    def choices_from_bots(self):
        for bot in tb.my_bot.bots:
            me = bot.get_me()
            yield (bot.token, f'{me.full_name} [@{me.username}] ({bot.token})')


class MigrateToBotView(LoginRequiredMixin, FormView):
    form_class = MigrateToBotForm
    template_name = 'migrate.html'

    def get(self, *args, **kwargs):
        ids = list(filter(None, self.request.GET.get('ids', '').split(',')))
        channel_objs = ChannelSettings.objects.filter(pk__in=ids)
        if not channel_objs:
            return 'nope'

        form = self.form_class()

        channels = {}
        for channel in channel_objs:
            bot = next(iter([bot for bot in tb.my_bot.bots if bot.token == channel.bot_token]), None)
            if not bot:
                name = f'({channel.bot_token})'
            else:
                botuser = bot.bot
                if not botuser:
                    botuser = bot.get_me()
                name = f'{botuser.full_name} [@{botuser.username}] ({bot.token})'

            channels[channel] = name

        return render(self.request, self.template_name, {'form': form, 'channels': channels})

    def post(self, *args, **kwargs):
        ids = self.request.POST.get('ids', [])
        if not isinstance(ids, list):
            ids = [ids]
        ids = filter(None, ids)
        try:
            ids = list(map(int, ids))
            if not ids:
                raise ValueError()
        except ValueError:
            return 'nope'

        channels = ChannelSettings.objects.filter(pk__in=ids)
        form = self.form_class(first(channels).bot_token, self.request.POST)

        if form.is_valid():
            return StreamingHttpResponse(self.migrate(channels, self.request.POST.get('new_bot_token')))
        return 'nope'

    def print(self, text: str) -> str:
        return text + '\n'

    def migrate(self, channels, new_bot_token) -> bool:
        yield self.print('<pre>')
        with transaction.atomic():
            for channel in channels:
                yield self.print('*' * 80)
                yield self.print(f'Working on {channel.name} ({channel.pure_link})')
                if channel.bot_token == new_bot_token:
                    yield self.print('Channel already migrated')
                    continue
                duplicate_channels = ChannelSettings.objects.filter(channel_id=channel.channel_id,
                                                                    bot_token=new_bot_token)
                yield self.print(('Has' if duplicate_channels else 'Does not have') + 'duplicate channel/s')

                channel.bot_token = new_bot_token
                creator = channel.added_by
                yield self.print(f'Migrating creator {creator.name}')

                try:
                    creator = UserSettings.objects.get(user_id=creator.user_id, bot_token=new_bot_token)
                    yield self.print('Creator exists')
                except UserSettings.DoesNotExist:
                    yield self.print('Creator does not exist')
                    creator.pk = None  # Results in a clone
                creator.bot_token = new_bot_token
                creator.save()

                channel.added_by = creator

                channel.users.clear()
                channel.users.add(creator)
                users = channel.users.exclude(pk=creator.pk)
                for user in users:
                    yield self.print(f'Migrating user {user.name}')
                    try:
                        user = UserSettings.objects.get(user_id=user.user_id, bot_token=new_bot_token)
                    except UserSettings.DoesNotExist:
                        user.pk = None  # Results in a clone
                    user.bot_token = new_bot_token
                    user.save()

                    channel.users.add(user)

                if duplicate_channels:
                    yield self.print(f'Updateing reactions on duplicate channels')
                    for index, reaction in enumerate(Reaction.objects.filter(channel=duplicate_channels), 1):
                        reaction.channel = channel
                        reaction.save()
                        if index % 50 == 0:
                            yield self.print(f'Reactions migrated {index}')
                    yield self.print(f'Update all reactions from duplicates {index}')

                for duplicate in duplicate_channels:
                    yield self.print('Removing duplicate')
                    duplicate.delete()

                yield self.print('Update channel')
                channel.save()
                yield self.print(f'Channel {channel.name} updated')
            yield self.print('Commiting transaction')
        yield self.print('</pre>')
