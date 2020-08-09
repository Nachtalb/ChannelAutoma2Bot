import logging
import threading
from typing import Callable, List, Type

from django_telegrambot.apps import DjangoTelegramBot
from telegram import Bot, TelegramError, Update, User
from telegram.ext import CallbackQueryHandler, CommandHandler, Filters, Handler, MessageHandler, Dispatcher

from bot.utils.internal import set_thread_locals, first

# Patch dispatcher
original__process_update = Dispatcher.process_update


def process_update(self, update: Update):
    set_thread_locals(self, update)
    return original__process_update(self, update)


Dispatcher.process_update = process_update


class MyBot:
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(logging.INFO)

        self.logger.info('Loading handlers for telegram bot')

        self.dispatchers: List[Dispatcher] = DjangoTelegramBot.dispatchers
        self.bots: List[Bot] = [dp.bot for dp in self.dispatchers]
        self.threadlocal = threading.local()

        for bot in self.bots:
            self.logger.info('Bot {} [{}] up'.format(bot.get_me().username, bot.token))

        self.add_command(func=self.error, is_error=True)

    def error(self, bot: Bot, update: Update, error: TelegramError):
        self.logger.warning(f'Update "{update}" caused error "{error}"')

    def me(self) -> User:
        return self.bot.get_me()

    def get_bot(self, token):
        return first([bot for bot in self.bots if bot.token == token])

    @property
    def bot(self):
        return getattr(self.dispatcher, 'bot', None)

    @property
    def token(self):
        return getattr(self.bot, 'token', None)

    @property
    def dispatcher(self):
        return getattr(self.threadlocal, 'dispatcher', None)

    @property
    def update(self):
        return getattr(self.threadlocal, 'update', None)

    def _add_handler(self, *args, **kwargs):
        for dispatcher in self.dispatchers:
            dispatcher.add_handler(*args, **kwargs)

    def _add_error_handler(self, *args, **kwargs):
        for dispatcher in self.dispatchers:
            dispatcher.add_error_handler(*args, **kwargs)

    def add_command(self, handler: Type[Handler] or Handler = None, names: str or List[str] = None,
                    func: Callable = None, is_error: bool = False, group: int = 0, **kwargs):
        if is_error and not func:
            self.logger.fatal('You must give func if you add an error handler.')
            exit(1)
        elif is_error and func:
            if handler or names or kwargs:
                self.logger.warning('When adding an error handler all arguments except func will be ignored.')
            self._add_error_handler(func)
            return

        handler = handler or CommandHandler

        if isinstance(handler, Handler):
            self._add_handler(handler=handler, group=group)
        elif handler == MessageHandler:
            self._add_handler(handler=handler(kwargs.get('filters', Filters.all), func), group=group)
        elif handler == CallbackQueryHandler:
            self._add_handler(handler=handler(func, **kwargs), group=group)
        else:
            if not names:
                names = [func.__name__]
            elif not isinstance(names, List):
                names = [names]

            for name in names:
                self._add_handler(handler=handler(name, func, **kwargs), group=group)


# noinspection PyTypeChecker
my_bot: MyBot = None


def main():
    global my_bot
    my_bot = MyBot()
    # noinspection PyUnresolvedReferences
    from . import commands
