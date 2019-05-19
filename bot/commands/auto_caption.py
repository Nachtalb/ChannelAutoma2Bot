from django.template.loader import get_template
from telegram import Bot, ParseMode, Update, ReplyKeyboardMarkup
from telegram.ext import Filters, MessageHandler, CallbackQueryHandler

from bot.commands import BaseCommand, CancelOperation
from bot.models.channel_settings import ChannelSettings

from bot.filters import Filters as OwnFilters
from bot.models.usersettings import UserSettings
from bot.utils.chat import is_media_message, channel_selector_menu, build_menu


class AutoCaption(BaseCommand):
    @BaseCommand.command_wrapper(MessageHandler, filters=OwnFilters.in_channel & (Filters.text | OwnFilters.is_media))
    def auto_caption(self):
        try:
            channel_settings = ChannelSettings.objects.get(channel_id=self.chat.id)
        except ChannelSettings.DoesNotExist:
            return

        if not channel_settings.caption:
            return

        caption = channel_settings.caption
        if self.message.text and not self.message.text.strip().endswith(caption):
            self.message.edit_text(f'{self.message.text_markdown}\n\n{caption}', parse_mode=ParseMode.MARKDOWN)
        if is_media_message(self.message) and (self.message.caption is None
                                               or not self.message.caption.endswith(caption)):
            self.message.edit_caption(caption=f'{self.message.caption_markdown or ""}\n\n{caption}',
                                      parse_mode=ParseMode.MARKDOWN)

    @BaseCommand.command_wrapper(MessageHandler,
                                 filters=OwnFilters.text_is('Auto Caption') & OwnFilters.state_is(UserSettings.IDLE))
    def caption_menu(self):
        menu = channel_selector_menu(self.user_settings, 'change_caption')
        message = get_template('commands/auto_caption/main.html').render()

        if not menu:
            self.message.reply_text(message)
            self.message.reply_text('No channels added yet.')
            return

        self.user_settings.state = UserSettings.SET_CAPTION_MENU
        self.message.reply_html(message, reply_markup=ReplyKeyboardMarkup([['Cancel']]))
        self.message.reply_text('Channels:', reply_markup=menu)

    @BaseCommand.command_wrapper(MessageHandler, filters=OwnFilters.state_is(UserSettings.SET_CAPTION))
    def set_caption(self):
        caption = self.message.text_markdown

        if not caption:
            self.message.reply_text('You have to send me some text.')
            return
        elif caption in ['Cancel', 'Home']:
            return
        elif caption == 'Clear':
            caption = None

        self.user_settings.current_channel.caption = caption
        self.user_settings.current_channel.save()

        message = f'The caption of {self.user_settings.current_channel.name} was set to:\n{caption}'
        if not caption:
            message = f'Caption for {self.user_settings.current_channel.name} cleared'

        self.message.reply_markdown(message, reply_markup=ReplyKeyboardMarkup([['Home']]))

    @BaseCommand.command_wrapper(CallbackQueryHandler, pattern='^change_caption:.*$')
    def pre_set_caption(self):
        channel_id = int(self.update.callback_query.data.split(':')[1])
        member = self.bot.get_chat_member(chat_id=channel_id, user_id=self.user.id)

        if not member.can_change_info and not member.status == member.CREATOR:
            self.message.reply_text('You must have change channel info permissions to change the default caption.')
            return

        self.user_settings.current_channel = ChannelSettings.objects.get(channel_id=channel_id)
        self.user_settings.state = UserSettings.SET_CAPTION

        self.update.callback_query.answer()
        self.message.delete()

        message = get_template('commands/auto_caption/new.html').render({
            'channel_name': self.user_settings.current_channel.name,
            'current_caption': self.user_settings.current_channel.caption,
        })

        self.message.reply_html(message, reply_markup=ReplyKeyboardMarkup(build_menu('Clear', 'Cancel')))
