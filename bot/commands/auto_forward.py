import emoji
from django.template.loader import get_template
from telegram import CallbackQuery, ReplyKeyboardMarkup
from telegram.ext import CallbackQueryHandler, MessageHandler

from bot.commands import BaseCommand
from bot.commands.auto_edit import AutoEdit
from bot.filters import Filters as OwnFilters
from bot.models.channel_settings import ChannelSettings
from bot.models.reactions import Reaction
from bot.models.usersettings import UserSettings
from bot.utils.chat import build_menu, channel_selector_menu


class AutoForward(AutoEdit):
    BaseCommand.register_start_button('Forwarder')

    @BaseCommand.command_wrapper(MessageHandler,
                                 filters=OwnFilters.text_is('Forwarder') & OwnFilters.state_is(UserSettings.IDLE))
    def set_forwader_menu(self):
        menu = channel_selector_menu(self.user_settings, 'forward_from')
        message = get_template('commands/auto_forwarder/main.html').render()

        if not menu:
            self.message.reply_text(message)
            self.message.reply_text('No channels added yet.')
            return

        self.user_settings.state = UserSettings.SET_FORWARDER_MENU
        self.message.reply_html(message, reply_markup=ReplyKeyboardMarkup([['Cancel']]))
        self.message.reply_text('Forward from:', reply_markup=menu)

    @BaseCommand.command_wrapper(CallbackQueryHandler, pattern='^forward_from:.*$')
    def set_forwarder_to_menu(self):
        channel_id = int(self.update.callback_query.data.split(':')[1])
        member = self.bot.get_chat_member(chat_id=channel_id, user_id=self.user.id)

        if not member.can_change_info and not member.status == member.CREATOR:
            self.message.reply_text('You must have change channel info permissions.')
            return

        from_channel = ChannelSettings.objects.get(channel_id=channel_id)
        self.user_settings.current_channel = from_channel
        self.user_settings.state = UserSettings.SET_FORWARDER_TO

        self.update.callback_query.answer()

        menu = channel_selector_menu(self.user_settings, f'forward_to:{channel_id}')

        connections = []
        if from_channel.forward_to:
            connections.append(f'{from_channel.link} :arrow_right: {from_channel.forward_to.link}')

        for channel in from_channel.forward_from.all():
            connections.append(f'{from_channel.link} :arrow_left: {channel.link}')

        if connections:
            self.message.reply_html(emoji.emojize('Connections:\n' + '\n- '.join(connections), use_aliases=True))

        self.message.reply_html(f'Forward from {self.user_settings.current_channel.link} to', reply_markup=menu)
        self.message.delete()

    @BaseCommand.command_wrapper(CallbackQueryHandler, pattern='^forward_to:.*$')
    def set_forwarder_to_menu(self):
        channels = self.update.callback_query.data.split(':')
        channel_from_id, channel_to_id = int(channels[1]), int(channels[2])

        member_to = self.bot.get_chat_member(chat_id=channel_to_id, user_id=self.user.id)

        if not member_to.can_send_messages and not member_to.status == member_to.CREATOR:
            self.message.reply_text('You must have permissions to send messages.')
            return

        from_channel = ChannelSettings.objects.get(channel_id=channel_from_id)
        to_channel = ChannelSettings.objects.get(channel_id=channel_to_id)

        from_channel.forward_to = to_channel
        from_channel.save()

        self.message.reply_html(f'Messages from {from_channel.link} are now forwarded to {to_channel.link}')
        self.home()
