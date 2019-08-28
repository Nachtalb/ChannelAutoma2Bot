import inspect
import logging
from functools import wraps
from typing import Callable, Type

bot_not_running_protect_logger = logging.getLogger('bot_not_running_protect')


def bot_not_running_protect(func):
    """Prevent a function call if bot is not running
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        from bot.telegrambot import my_bot
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
            if cls.__dict__.get(meth.__name__, ) is meth:
                return cls
        meth = meth.__func__  # fallback to __qualname__ parsing
    if inspect.isfunction(meth):
        cls = getattr(inspect.getmodule(meth),
                      meth.__qualname__.split('.<locals>', 1)[0].rsplit('.', 1)[0])
        if isinstance(cls, type):
            return cls
    return None
