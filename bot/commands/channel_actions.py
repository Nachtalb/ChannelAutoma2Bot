from telegram import Bot, ParseMode, Update
from telegram.ext import Filters, MessageHandler

from bot.commands import BaseCommand, CancelOperation
from bot.models.channel_settings import ChannelSettings

from bot.filters import Filters as OwnFilters
from bot.utils import is_media_message


class ChannelActions(BaseCommand):

    def __init__(self, bot: Bot, update: Update, *args, **kwargs):
        super().__init__(bot, update, *args, **kwargs)
        try:
            self.channel_settings = ChannelSettings.objects.get(channel_id=self.chat.id)
        except ChannelSettings.DoesNotExist:
            raise CancelOperation

    @BaseCommand.command_wrapper(MessageHandler, filters=OwnFilters.in_channel & (Filters.text | OwnFilters.is_media))
    def auto_caption(self):
        if not self.channel_settings or not self.channel_settings.caption:
            return

        caption = self.channel_settings.caption
        if self.message.text and not self.message.text.strip().endswith(caption):
            self.message.edit_text(f'{self.message.text_markdown}\n\n{caption}', parse_mode=ParseMode.MARKDOWN)
        if is_media_message(self.message) and (self.message.caption is None
                                               or not self.message.caption.endswith(caption)):
            self.message.edit_caption(caption=f'{self.message.caption_markdown or ""}\n\n{caption}',
                                      parse_mode=ParseMode.MARKDOWN)
