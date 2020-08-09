from functools import wraps
from typing import Callable, List, Type
import inspect
import logging
import pkgutil

from telegram import Bot, Chat, Message, Update, User
from telegram.ext import Handler

from bot.models.channel_settings import ChannelSettings
from bot.models.usersettings import UserSettings
from bot.models.media_group import MediaGroup
from bot.telegrambot import my_bot
from bot.utils.internal import get_class_that_defined_method, set_thread_locals, first

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
    channel_settings: ChannelSettings = None
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
            self.user_settings = UserSettings.objects.get_or_create(user_id=self.user.id, bot_token=self.bot.token)[0]
            self.user_settings.auto_update_values(self.user, save=True)

        try:
            self.channel_settings = ChannelSettings.objects.get(channel_id=self.chat.id, bot_token=self.bot.token)
        except ChannelSettings.DoesNotExist:
            pass

        self.media_group = None
        self.media_group_creator = None
        if self.message.media_group_id and self.channel_settings:
            try:
                self.media_group = MediaGroup.objects.get(media_group_id=self.message.media_group_id,
                                                          bot_token=self.bot.token)
                self.media_group_creator = False
            except MediaGroup.DoesNotExist:
                self.media_group = MediaGroup(media_group_id=self.message.media_group_id,
                                              message_id=self.message.message_id,
                                              channel=self.channel_settings,
                                              bot_token=self.bot.token)
                self.media_group.save()
                self.media_group_creator = True

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

        if BaseCommand not in home_class.__mro__:
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
    def _set_thread_locals_async_wrapper(func, *args, **kwargs):
        probably_self = first(args)
        if isinstance(probably_self, BaseCommand):
            bot = probably_self.bot
            update = probably_self.update
        else:
            arg_values = args + list(kwargs.values())
            bot = first([var for var in arg_values if isinstance(var, Bot)])
            update = first([var for var in arg_values if isinstance(var, Update)])

        set_thread_locals(bot, update)
        return func(*args, **kwargs)

    @staticmethod
    def command_wrapper(handler: Type[Handler] or Handler = None, names: str or List[str] = None,
                        is_async: bool = False, **kwargs):
        global _plugin_group_index
        logger.debug(f'Register new command: handler={handler}, names={names}, async={is_async}, kwargs={kwargs}')

        def outer_wrapper(func):
            @wraps(func)
            def wrapper(*inner_args, **inner_kwargs):
                logger.debug(f'Command called: handler={handler}, names={names}, async={is_async}, kwargs={kwargs}, '
                             f'inner_args={inner_args}, inner_kwargs={inner_kwargs}')
                method_class = get_class_that_defined_method(func)

                if (inner_args and isinstance(inner_args[0], method_class)) \
                        or not (len(inner_args) > 1
                                and isinstance(inner_args[0], Bot)
                                and isinstance(inner_args[1], Update)):
                    return func(*inner_args, **inner_kwargs)

                _args, _kwargs = inner_args, inner_kwargs
                if method_class and BaseCommand in method_class.__mro__:
                    try:
                        instance = method_class(*inner_args, **inner_kwargs)
                    except CancelOperation:
                        return
                    _args = [instance]
                    _kwargs = {}

                try:
                    if is_async:
                        my_bot.dispatcher.run_async(BaseCommand._set_thread_locals_async_wrapper,
                                                    func, *_args, **_kwargs)
                    else:
                        func(*_args, **_kwargs)
                except Exception as e:
                    logger.exception(e)
                    raise e

            kwargs.setdefault('group', _plugin_group_index)
            my_bot.add_command(handler=handler, names=names, func=wrapper, **kwargs)
            return wrapper

        return outer_wrapper


# Import submodules
__all__ = []

for loader, module_name, is_pkg in pkgutil.walk_packages(__path__):
    _plugin_group_index += 1
    __all__.append(module_name)
    if module_name not in globals():
        _module = loader.find_module(module_name).load_module(module_name)
        globals()[module_name] = _module

BaseCommand._check_home_class()
