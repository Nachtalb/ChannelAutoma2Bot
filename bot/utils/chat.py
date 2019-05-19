import logging
from typing import List

from telegram import Animation, Audio, Document, Message, PhotoSize, Video, Voice, InlineKeyboardButton, \
    InlineKeyboardMarkup

from bot.models.usersettings import UserSettings

bot_not_running_protect_logger = logging.getLogger('bot_not_running_protect')


def build_menu(*buttons: any,
               cols: int = None,
               header_buttons: List[any] = None,
               footer_buttons: List[any] = None) -> List[List[any]]:
    """Build a simple list of lists with max columns width

    https://github.com/python-telegram-bot/python-telegram-bot/wiki/Code-snippets#build-a-menu-with-buttons
    """
    cols = cols or 2
    buttons = list(buttons)
    menu = [buttons[i:i + cols] for i in range(0, len(buttons), cols)]

    if header_buttons:
        menu.insert(0, header_buttons)
    if footer_buttons:
        menu.append(footer_buttons)

    return menu


def is_media_message(msg: Message) -> bool:
    media_types = tuple([Audio, Animation, Document, PhotoSize, Video, Voice])
    attachment = msg.effective_attachment

    is_media = isinstance(attachment, media_types)
    if not is_media and isinstance(attachment, list) and attachment:
        is_media = isinstance(attachment[0], media_types)

    return is_media


def channel_selector_menu(user: UserSettings, prefix: str,
                          header_buttons: List[InlineKeyboardButton] = None,
                          footer_buttons: List[InlineKeyboardButton] = None) -> InlineKeyboardMarkup or None:
    if not user.channels:
        return
    buttons = []
    for channel in user.channels.all():
        buttons.append(InlineKeyboardButton(channel.name, callback_data=f'{prefix}:{channel.channel_id}'))
    return InlineKeyboardMarkup(build_menu(*buttons, header_buttons=header_buttons, footer_buttons=footer_buttons))
