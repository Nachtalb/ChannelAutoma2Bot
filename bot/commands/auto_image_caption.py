import os
from io import BytesIO

from django.template.loader import get_template
from telegram import File, InputMediaPhoto, ParseMode, PhotoSize, ReplyKeyboardMarkup
from telegram.ext import CallbackQueryHandler, MessageHandler

from bot.commands import BaseCommand
from bot.filters import Filters as OwnFilters
from bot.models.channel_settings import ChannelSettings
from bot.models.usersettings import UserSettings
from bot.utils.chat import build_menu, channel_selector_menu
from bot.utils.media import watermark_text


class AutoImageCaption(BaseCommand):
    BaseCommand.register_start_button('Image Caption')

    @BaseCommand.command_wrapper(MessageHandler, filters=OwnFilters.in_channel & (OwnFilters.is_media))
    def auto_caption(self):
        attachment = self.message.effective_attachment
        if isinstance(attachment, list):
            attachment = attachment[-1]

        if not self.channel_settings or \
                not self.channel_settings.image_caption or \
                not isinstance(attachment, PhotoSize):
            return

        image_caption = self.channel_settings.image_caption
        caption = self.channel_settings.caption
        file: File = attachment.get_file()

        extension = os.path.splitext(file.file_path)[1].strip('.')

        image_in = BytesIO()
        image_out = BytesIO()
        file.download(out=image_in)

        watermark_text(in_image=image_in, out_buffer=image_out, text=image_caption, file_extension=extension)

        caption_args = {}
        if caption or self.message.caption:
            caption_args['caption'] = f'{self.message.caption_html or ""}\n\n{caption}'
            caption_args['parse_mode'] = ParseMode.HTML

        self.message.edit_media(InputMediaPhoto(
            image_out,
            **caption_args
        ))

    @BaseCommand.command_wrapper(MessageHandler,
                                 filters=OwnFilters.text_is('Image Caption') & OwnFilters.state_is(UserSettings.IDLE))
    def caption_menu(self):
        menu = channel_selector_menu(self.user_settings, 'change_image_caption')
        message = get_template('commands/auto_image_caption/main.html').render()

        if not menu:
            self.message.reply_text(message)
            self.message.reply_text('No channels added yet.')
            return

        self.user_settings.state = UserSettings.SET_IMAGE_CAPTION_MENU
        self.message.reply_html(message, reply_markup=ReplyKeyboardMarkup([['Cancel']]))
        self.message.reply_text('Channels:', reply_markup=menu)

    @BaseCommand.command_wrapper(MessageHandler, filters=OwnFilters.state_is(UserSettings.SET_IMAGE_CAPTION))
    def set_caption(self):
        image_caption = self.message.text.strip()

        if not image_caption:
            self.message.reply_text('You have to send me some text.')
            return
        elif image_caption in ['Cancel', 'Home']:
            return
        elif image_caption == 'Clear':
            image_caption = None

        self.user_settings.current_channel.image_caption = image_caption
        self.user_settings.current_channel.save()

        message = f'The image caption of {self.user_settings.current_channel.name} was set to:\n{image_caption}'
        if not image_caption:
            message = f'Caption for {self.user_settings.current_channel.name} cleared'

        self.message.reply_text(message, reply_markup=ReplyKeyboardMarkup([['Home']]))

    @BaseCommand.command_wrapper(CallbackQueryHandler, pattern='^change_image_caption:.*$')
    def pre_set_caption(self):
        channel_id = int(self.update.callback_query.data.split(':')[1])
        member = self.bot.get_chat_member(chat_id=channel_id, user_id=self.user.id)

        if not member.can_change_info and not member.status == member.CREATOR:
            self.message.reply_text('You must have change channel info permissions to change the default image caption.')
            return

        self.user_settings.current_channel = ChannelSettings.objects.get(channel_id=channel_id)
        self.user_settings.state = UserSettings.SET_IMAGE_CAPTION

        self.update.callback_query.answer()
        self.message.delete()

        message = get_template('commands/auto_caption/new.html').render({
            'channel_name': self.user_settings.current_channel.name,
            'current_caption': self.user_settings.current_channel.image_caption,
        })

        self.message.reply_html(message, reply_markup=ReplyKeyboardMarkup(build_menu('Clear', 'Cancel')))
