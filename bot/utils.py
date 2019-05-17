import inspect
import logging
from functools import wraps
from typing import Callable, List, Type

from telegram import Animation, Audio, Document, Message, PhotoSize, Video, Voice

from bot.telegrambot import my_bot

bot_not_running_protect_logger = logging.getLogger('bot_not_running_protect')


def bot_not_running_protect(func):
    """Prevent a function call if bot is not running
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        if my_bot is None:
            bot_not_running_protect_logger.info(f'Bot not running, protected: {func}')
            return
        return func(*args, **kwargs)

    return wrapper


def get_class_that_defined_method(meth: Callable or Type) -> Type or None:
    """Get defining class of unbound method object

    full feature version
    https://stackoverflow.com/a/25959545/5699307
    """
    if inspect.ismethod(meth):
        for cls in inspect.getmro(meth.__self__.__class__):
            if cls.__dict__.get(meth.__name__) is meth:
                return cls
        meth = meth.__func__  # fallback to __qualname__ parsing
    if inspect.isfunction(meth):
        cls = getattr(inspect.getmodule(meth),
                      meth.__qualname__.split('.<locals>', 1)[0].rsplit('.', 1)[0])
        if isinstance(cls, type):
            return cls
    return None


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
