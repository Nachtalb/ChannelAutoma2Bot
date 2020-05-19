import os
from io import BytesIO
from typing import Generator, Tuple
from time import sleep

from telegram import File, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto, ParseMode, PhotoSize
from telegram.ext import Filters, MessageHandler
from telegram.error import TimedOut, RetryAfter

from bot.commands import BaseCommand
from bot.filters import Filters as OwnFilters
from bot.models.reactions import Reaction
from bot.utils.media import watermark_text


class AutoEdit(BaseCommand):

    @BaseCommand.command_wrapper(MessageHandler, filters=OwnFilters.in_channel & (Filters.text | OwnFilters.is_media),
                                 is_async=True)
    def auto_edit(self):
        if not self.channel_settings or (
                not self.channel_settings.caption and
                not self.channel_settings.image_caption and
                not self.channel_settings.reactions
        ):
            self.forward_message()
            return
        new_caption = self.new_caption()
        new_reply_markup = self.new_reply_buttons()

        if self.needs_new_image():
            method = self.message.edit_media
            params = dict(media=self.new_image(self.new_caption(), ParseMode.HTML), reply_markup=new_reply_markup, timeout=60, isgroup=self.channel_settings.channel_id)
        elif not self.message.effective_attachment:
            method = self.message.edit_text
            params = dict(text=new_caption, parse_mode=ParseMode.HTML, reply_markup=new_reply_markup, timeout=60, isgroup=self.channel_settings.channel_id)
        else:
            method = self.message.edit_caption
            params = dict(caption=new_caption, parse_mode=ParseMode.HTML, reply_markup=new_reply_markup, timeout=60, isgroup=self.channel_settings.channel_id)

        new_message = None
        while True:
            try:
                promis = method(**params)
                new_message = promis.result()
            except TimedOut:
                continue
            except RetryAfter as e:
                sleep(e.retry_after)
                continue
            break

        self.forward_message(new_message)

    @BaseCommand.command_wrapper(MessageHandler, filters=OwnFilters.in_channel & (~ (Filters.text | OwnFilters.is_media)),
                                 is_async=True)
    def forward_message(self, message=None):
        if not self.channel_settings or not self.channel_settings.forward_to:
            return
        message = message or self.message
        while True:
            try:
                message.forward(int(self.channel_settings.forward_to))
            except TimedOut:
                continue
            except RetryAfter as e:
                sleep(e.retry_after)
                continue
            break

    def new_caption(self) -> str or None:
        caption = (self.channel_settings.caption or '').strip()
        text = (self.message.text_html or self.message.caption_html or '').strip()

        if text.endswith(caption):
            return text
        return f'{text}\n\n{caption}'

    def needs_new_image(self) -> bool:
        if not self.message.effective_attachment or not isinstance(self.message.effective_attachment, list):
            return False
        attachment = (self.message.effective_attachment or [None])[-1]
        return self.channel_settings.image_caption and isinstance(attachment, PhotoSize)

    def new_image(self, caption: str = None, parse_mode: str = None) -> InputMediaPhoto or None:
        if not self.channel_settings.image_caption:
            return
        attachment = (self.message.effective_attachment or [None])[-1]
        if isinstance(attachment, PhotoSize):
            return InputMediaPhoto(self.watermark_photo(attachment), caption=caption, parse_mode=parse_mode)

    def watermark_photo(self, photo: PhotoSize) -> BytesIO:
        direction = self.channel_settings.image_caption_direction
        image_caption = self.channel_settings.image_caption
        file: File = photo.get_file()

        extension = os.path.splitext(file.file_path)[1].strip('.')

        image_in = BytesIO()
        image_out = BytesIO()
        file.download(out=image_in)

        watermark_text(
            in_image=image_in,
            out_buffer=image_out,
            text=image_caption,
            file_extension=extension,
            pos=direction,
            font=self.channel_settings.image_caption_font,
        )

        return image_out

    def new_reply_buttons(self) -> InlineKeyboardMarkup or None:
        if not self.channel_settings.reactions:
            return

        buttons = []
        for emoji, total in self.get_reactions():
            buttons.append(InlineKeyboardButton(
                f'{emoji} {total or ""}'.strip(),
                callback_data=f'reaction:{self.message.message_id}:{emoji}'
            ))

        return InlineKeyboardMarkup([buttons])

    def get_reactions(self) -> Generator[Tuple[str, int], None, None]:
        for emoji in self.channel_settings.reactions:
            reaction = Reaction.objects.get_or_create(
                reaction=emoji,
                message=self.message.message_id,
                channel=self.channel_settings
            )[0]

            yield (emoji, reaction.users.count())
