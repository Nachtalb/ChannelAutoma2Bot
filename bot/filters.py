from telegram import Chat
from telegram.ext import BaseFilter

from bot.utils import is_media_message


class Filters:
    class _IsMedia(BaseFilter):
        name = 'Filters.media'

        def filter(self, message):
            return is_media_message(message)

    is_media = _IsMedia()
    """:obj:`Filter`: Messages sent is a media file."""

    class _InChannel(BaseFilter):
        name = 'Filters.channel'

        def filter(self, message):
            return message.chat.type == Chat.CHANNEL

    in_channel = _InChannel()
    """:obj:`Filter`: Messages sent in a channels."""
