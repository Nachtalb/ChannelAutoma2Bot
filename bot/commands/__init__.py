import inspect
import logging
import pkgutil
from functools import wraps
from typing import Callable, List, Type

from telegram import Bot, Chat, Message, Update, User
from telegram.ext import Handler, run_async

from bot.models.usersettings import UserSettings
from bot.telegrambot import my_bot
from bot.utils.internal import get_class_that_defined_method

_plugin_group_index = 0

logger = logging.getLogger('BaseCommand')


class CancelOperation(Exception):
    pass


class BaseCommand:
    user: User
    chat: Chat
    message: Message
    update: Update
    bot: Bot
    user_settings: UserSettings or None
    _start_buttons = [[], [], []]
    _home: Callable = None

    def __init__(self, bot: Bot, update: Update, *args, **kwargs):
        self.user = update.effective_user
        self.chat = update.effective_chat
        self.message = update.effective_message
        self.update = update
        self.bot = my_bot.bot

        self.user_settings = None
        if self.user:
            self.user_settings = UserSettings.objects.get_or_create(user_id=self.user.id)[0]
            self.user_settings.auto_update_values(self.user, save=True)

    @staticmethod
    def register_start_button(name: str, header: bool = False, footer: bool = False):
        if header and footer:
            raise AttributeError('header and footer are mutually exclusive')
        if header:
            logger.debug('Register start button [header]')
            BaseCommand._start_buttons[0].append(name)
        elif footer:
            logger.debug('Register start button [main]')
            BaseCommand._start_buttons[2].append(name)
        else:
            logger.debug('Register start button [footer]')
            BaseCommand._start_buttons[1].append(name)

    @staticmethod
    def register_home(method: Callable):
        if BaseCommand._home:
            logger.warning(f'Overriding home method from {BaseCommand.home} to {method}')
        BaseCommand._home = method

    @staticmethod
    def _check_home_class():
        """Check the home method to be even applicable as a home method

        This must be done after all plugins are loaded, so that the class of the method can be determined.
        """
        home = BaseCommand._home

        while hasattr(home, '__wrapped__'):
            # Get original method not wrapper functions from decorators
            home = home.__wrapped__

        logger.debug(f'Check home method {home}')
        home_class = get_class_that_defined_method(home)

        if BaseCommand not in home_class.__bases__:
            raise AttributeError('Home method must be a method of a BaseCommand inheriting class.')

        for name, parameter in inspect.signature(home).parameters.items():
            if name == 'self':
                continue
            elif parameter.default is not parameter.empty:
                continue
            raise AttributeError(f'Method must not have any required arguments: {name}')

    def home(self):
        BaseCommand._home(self.bot, self.update)

    @staticmethod
    def command_wrapper(handler: Type[Handler] or Handler = None, names: str or List[str] = None,
                        is_async: bool = False, **kwargs):
        global _plugin_group_index, _messagehandler_group_index
        logger.debug(f'Register new command: handler={handler}, names={names}, async={is_async}, kwargs={kwargs}')

        def outer_wrapper(func):
            @wraps(func)
            def wrapper(*inner_args, **inner_kwargs):
                logger.debug(
                    f'Command called: handler={handler}, names={names}, async={is_async}, kwargs={kwargs}, inner_args={inner_args}, inner_kargs={inner_kwargs}')
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

BaseCommand._check_home_class()
