from django.template.loader import get_template
from telegram import Chat, ChatMember, InlineKeyboardButton, ReplyKeyboardMarkup
from telegram.error import Unauthorized
from telegram.ext import CallbackQueryHandler, Filters, MessageHandler

from bot.commands import BaseCommand
from bot.filters import Filters as OwnFilters
from bot.models.channel_settings import ChannelSettings
from bot.models.usersettings import UserSettings
from bot.telegrambot import my_bot
from bot.utils.chat import build_menu, channel_selector_menu


class ChannelManager(BaseCommand):
    @BaseCommand.command_wrapper(MessageHandler, is_async=True, filters=Filters.forwarded & (~ OwnFilters.in_channel))
    def add_channel(self):
        possible_channel = self.message.forward_from_chat

        if not possible_channel or possible_channel.type != Chat.CHANNEL or self.chat.type != Chat.PRIVATE:
            return

        try:
            member = possible_channel.get_member(my_bot.me().id)
        except Unauthorized:
            member = None

        if not member or member.status == member.LEFT:
            self.message.reply_text('I have to be a member of this chat to function')
            return

        user_member: ChatMember = possible_channel.get_member(self.user.id)

        if user_member.status not in [user_member.ADMINISTRATOR, user_member.CREATOR]:
            self.message.reply_text('You must be an admin yourself to use me.')
        else:
            message = 'Channel was updated'
            try:
                channel = ChannelSettings.objects.get(channel_id=possible_channel.id)
            except ChannelSettings.DoesNotExist:
                message = 'Channel was added'
                channel = ChannelSettings.objects.create(channel_id=possible_channel.id,
                                                         added_by=self.user_settings)

            if self.user_settings not in channel.users.all():
                channel.users.add(self.user_settings)

            channel.update_from_chat(possible_channel)
            channel.save()
            self.message.reply_text(message)

    @BaseCommand.command_wrapper(CallbackQueryHandler, pattern='^(home|cancel)$')
    @BaseCommand.command_wrapper(MessageHandler, filters=OwnFilters.text_is(['cancel', 'home', 'reset'], lower=True))
    @BaseCommand.command_wrapper(names=['start', 'reset', 'cancel'])
    def start(self):
        if self.update.callback_query:
            self.update.callback_query.answer()
            self.message.delete()

        elif 'start' in self.message.text:
            self.message.reply_html(get_template('commands/manager/start.html').render())

        if self.message.text.lower() in ['cancel', 'home', 'reset'] and self.user_settings.state != UserSettings.IDLE:
            self.message.reply_text('Current action was cancelled')

        self.user_settings.current_channel = None
        self.user_settings.state = UserSettings.IDLE

        buttons = build_menu('Auto Caption', 'Reactions', footer_buttons=['Settings'])
        self.message.reply_text('What do you want to do?', reply_markup=ReplyKeyboardMarkup(buttons))

    @BaseCommand.command_wrapper(MessageHandler,
                                 filters=(OwnFilters.text_is('Settings') & OwnFilters.state_is(UserSettings.IDLE)) |
                                         (OwnFilters.text_is('Back') & OwnFilters.state_is(UserSettings.CHANNEL_SETTINGS_MENU)))
    def settings_menu(self):
        footer_buttons = [InlineKeyboardButton('Update Channels', callback_data='update_channels'),
                          InlineKeyboardButton('Back', callback_data='cancel')]
        menu = channel_selector_menu(self.user_settings, 'change_settings_menu', footer_buttons=footer_buttons)

        if not menu:
            self.message.reply_text('No channels added yet. To add one forward any message from that channel.')
            return

        self.user_settings.state = UserSettings.SETTINGS_MENU
        self.message.reply_text('Here you can find global settings.', reply_markup=ReplyKeyboardMarkup([['Cancel']]))
        self.message.reply_text('What do you want to do?', reply_markup=menu)

    @BaseCommand.command_wrapper(CallbackQueryHandler, pattern='^update_channels$')
    def update_channels(self):
        channels = self.user_settings.channels.all()
        if not channels:
            self.message.reply_text('No channels added yet.')
            return

        for channel in channels:
            channel.auto_update_values()

        self.update.callback_query.answer()
        self.message.reply_text('Channels updated')

    @BaseCommand.command_wrapper(CallbackQueryHandler, pattern='^change_settings_menu:.*$')
    def channel_settings_menu(self):
        channel_id = int(self.update.callback_query.data.split(':')[1])
        self.message.delete()

        self.user_settings.current_channel_id = channel_id
        self.user_settings.state = UserSettings.CHANNEL_SETTINGS_MENU

        buttons = ReplyKeyboardMarkup(build_menu('Remove', footer_buttons=['Back', 'Cancel']))
        self.message.reply_text(f'Settings for {self.user_settings.current_channel.name}', reply_markup=buttons)

    @BaseCommand.command_wrapper(MessageHandler, filters=OwnFilters.text_is('R  emove') &
                                                         OwnFilters.state_is(UserSettings.CHANNEL_SETTINGS_MENU))
    def remove_channel_confirm_dialog(self):
        self.user_settings.state = UserSettings.PRE_REMOVE_CHANNEL
        self.message.reply_text(f'Are you sure you want to remove: {self.user_settings.current_channel.name}?',
                                reply_markup=ReplyKeyboardMarkup(build_menu('Yes', 'No')))

    @BaseCommand.command_wrapper(MessageHandler, filters=OwnFilters.state_is(UserSettings.PRE_REMOVE_CHANNEL))
    def remove_channel_confirmation(self):
        if self.message.text.lower() == 'yes':
            self.user_settings.channels.remove(self.user_settings.current_channel)
            self.message.reply_text('Channel was removed')
        elif self.message.text.lower() != 'no':
            self.message.reply_text('Either hit yes or no')
            return
        self.start()
