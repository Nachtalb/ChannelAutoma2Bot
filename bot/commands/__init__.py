import pkgutil
from functools import wraps
from typing import Type, List

from telegram import Bot, Chat, Message, Update, User

from telegram.ext import run_async, Handler, MessageHandler
from bot.models.usersettings import UserSettings
from bot.telegrambot import my_bot
from bot.utils.internal import get_class_that_defined_method

_plugin_group_index = 0


class CancelOperation(Exception):
    pass


class BaseCommand:
    user: User
    chat: Chat
    message: Message
    update: Update
    bot: Bot
    user_settings: UserSettings or None

    def __init__(self, bot: Bot, update: Update, *args, **kwargs):
        self.user = update.effective_user
        self.chat = update.effective_chat
        self.message = update.effective_message
        self.update = update
        self.bot = my_bot.bot

        self.user_settings = None
        if self.user:
            self.user_settings = UserSettings.objects.get_or_create(user_id=self.user.id)[0]

    @staticmethod
    def command_wrapper(handler: Type[Handler] or Handler = None, names: str or List[str] = None,
                        is_async: bool = False, **kwargs):
        global _plugin_group_index, _messagehandler_group_index

        def outer_wrapper(func):
            @wraps(func)
            def wrapper(*inner_args, **inner_kwargs):
                method_class = get_class_that_defined_method(func)

                if (inner_args and isinstance(inner_args[0], method_class)) \
                        or not (len(inner_args) > 1
                                and isinstance(inner_args[0], Bot)
                                and isinstance(inner_args[1], Update)):
                    return func(*inner_args, **inner_kwargs)

                _args, _kwargs = inner_args, inner_kwargs
                if method_class and BaseCommand in method_class.__bases__:
                    try:
                        instance = method_class(*inner_args, **inner_kwargs)
                    except CancelOperation:
                        return
                    _args = [instance]
                    _kwargs = {}

                if is_async:
                    run_async(func(*_args, **_kwargs))
                else:
                    func(*_args, **_kwargs)

            kwargs.setdefault('group', _plugin_group_index)
            my_bot.add_command(handler=handler, names=names, func=wrapper, **kwargs)
            return wrapper

        return outer_wrapper


# Import submodules
__all__ = []

for loader, module_name, is_pkg in pkgutil.walk_packages(__path__):
    _plugin_group_index += 1
    __all__.append(module_name)
    _module = loader.find_module(module_name).load_module(module_name)
    globals()[module_name] = _module
