import logging
from typing import List

from telegram import Animation, Audio, Chat, ChatMember, Document, InlineKeyboardButton, InlineKeyboardMarkup, Message, PhotoSize, \
    User, Video, Voice
from telegram.error import Unauthorized

from bot.models.usersettings import UserSettings
from bot.telegrambot import my_bot

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


def check_user_permissions(user: User, channel: Chat) -> bool:
    user_member: ChatMember = channel.get_member(user.id)

    if user_member.status not in [user_member.ADMINISTRATOR, user_member.CREATOR]:
        raise Unauthorized('User is not an admin of the channel.')
    return True


def check_bot_permissions(channel: Chat) -> bool:
    try:
        member = channel.get_member(my_bot.me().id)
        if member.status == member.LEFT:
            raise Unauthorized('Not a member')
    except Unauthorized:
        raise Unauthorized('Not a member')
    return True
