Djang Telegram Bot Base
=======================

`@DjangoTelegramBot <https://t.me/DjangoTelegramBot>`__ \|
`GitHub <https://github.com/Nachtalb/DjangoTelegramBotBase>`__

.. contents:: Table of Contents


What am I
---------

This is just the base for a Telegram Bot together with Django


Development
-----------

Get a Telegram Bot API Token ==> `@BotFather <https://t.me/BotFather>`__.

Install the requirements by:

.. code:: sh

   pip install -r requirements.txt

Define these environmental variables:

.. code::

    DJANGO_SECRET_KEY=YourDjangoSecret
    TELEGRAM_TOKEN=123456789:abcdfghijklmnopqrstuvwxyzyxwvutsrqp

Change the settings ``bot/settings/settings.py`` according to your needs.

This is needed for the first time:

.. code:: sh

    python manage.py migrate
    python manage.py createsuperuser


Start your bot.

.. code:: sh

    python manage.py runserver 8000
    # If you use polling for the bot and not a webhook you have to start this manually
    python manag.py botpolling --username=DjangoTelegramBot


Telegram Integration
--------------------

Commands in classes
~~~~~~~~~~~~~~~~~~~

Normally commands are simple functions with the bot and updated args and nothing more. Here this is not the case.
Instead of functions we use classes. Our classes are in submodules of the package bot/commands/. All submodules of this
package are automagically loaded when the bot starts. This enables a some what plug and play functionality.

These command classes additionally have some features which let's you create commands more easily without having to
care about every single detail.

Here is how we define commands the old way:

.. code:: python

    def start_command(bot, update, args):
        update.message.reply_text('This is the start message')

    def help_command(bot, update, args):
        update.message.repy_text('This is the help message')

    ...

    dispatcher.add_handler(CommandHandler('start', start_command))
    dispatcher.add_handler(CommandHandler('help', help_command))


and now the new way.

.. code:: python

    class Builtins(BaseCommand):
        @BaseCommand.command_wrapper()
        def start(self):
            self.message.reply_text('This is the start message')

        @BaseCommand.command_wrapper()
        def help(self):
            self.message.reply_text('This is the help message')


As you can see you don't have to tell that it is a CommandHandler and neither you have to have bot and upgrade in your
arguments. The CommandHandler is just the default handler used, because this is probably the one you use most.
The ``self.message`` is one of the few extracted variables which is directly available on the instance. This enables you
to run other methods on the class without always giving the update and bot back and forth.

Here a list of those variables:

.. code::

    user:       User        # update.effective_message
    chat:       Chat        # update.effective_chat
    message:    Message     # update.effective_message
    update:     Update      # update
    bot:        Bot         # bot.telegrambot.my_bot

    user_settings:  UserSettings    # bot.models.usersettings.UserSettings


You might stop two variables which stand out. The first one is the ``bot`` variable. In these classes not the bot given
by the python telegram bot update handler is used, but instead the bot which we have from the start and is always
available ``my_bot``. In this case the normal ``bot`` var could be used but is not to have consistency around the code
base. Due to the availability of ``my_bot`` you don't have to send the bot back and forth for method / functions
outside of the class.

Secondly there is this ``user_settings``. The user_settings is a pre defined Django ORM Model you can work with and
save data for users onto. Because many, many bots use such a feature (saving user based data) I have already included
that here.


Make life easier
~~~~~~~~~~~~~~~~


**@BaseCommand.command_wrapper()**
With the ``command_wrapper`` class above you can make your life easy by just using a decorator for all your commands
needs. As first argument ``handler`` takes a handler class like ``CommandHandler`` (which is the default) or
``MessageHandler`` and so on. The second argument ``names`` as it suggests is not a single name but multiple. This
means you can define multiple commands at once for a single action. So eg. you can have a command like ``/get_me_cake``
and an alias ``/gmc`` simply by adding both names in a list. You don't have to give a list though, it also accepts a
simple string or nothing at all. If nothing is given the name of the method is taken. So you can just call your method
start and the command will be ``/start``. The third argument is ``is_async`` which enables the ``@run_async`` decorator.
Last but not least we have ``**kwargs``. This will just be redirect to the ``add_command`` method we go to next.

**my_bot.add_command**
The ``add_command`` method is directly on our bot and is the gateway to add commands via the PythonTelegramBots
add_handler method. It adds various defaults and fallbacks which let's you create command easy and fast. The first two
arguments are just like the one above but instead of just accepting a handler class you can give it the whole handler
instance. This enables you to build complete command handlers on the fly and then just add it with the same command you
add all others. The third argument this time is the ``func`` which is just the function you want to be used. It's name
is taken as a default again in case you don't define a name yourself. The fourth argument ``is_error`` is a shortcut to
the ``add_error_handler`` method for the bot. If you set this to true the ``func`` you have given will be added to the
error handlers. Every other argument you might have given will be ignored. The last one are ``kwargs`` again which will
be added to the handler you have given.

**MessageHandler**
In both commands above MessageHandlers automatically get ``Filter.all`` if you don't provide one yourself.

**Additional Filters**
Next to the default filters given by the PythonTelegramBot framework I have also included two small ones. ``is_media``
whitelists all media messages (eg. Images, Videos but not Text) and ``in_channel``, which checks if a message was sent
inside a channel.

**my_bot.me**
If you want to get your bot's information just use ``my_bot.me`` which is a wrapper for ``self.updater.bot.get_me()``

**utils**
*bot_not_running_protect*
This is a decorator which can be used to prevent function calls for functions which should not be called when the bot
isn't running.

*get_class_that_defined_method*
This is used in the ``command_wrapper`` decorator and finds out what the class of method is event if it is wrapped in
decorators.

*build_menu*
A simple method to create button menus in telegram copied from `here <https://github.com/python-telegram-bot/python-telegram-bot/wiki/Code-snippets#build-a-menu-with-buttons>`_

*is_media_message*
Is used to determine if a message is a media file.

**Templates**
To easily create formatted text, Django templates can be used. Two examples can be found in ``/bot/templates/commands/builtins/``.
These templates can be used in commands like this:

.. code:: python

    self.message.reply_html(get_template('commands/builtins/foobar.html').render({'some': 'context'}))



Copyright
---------

Made by `Nachtalb <https://github.com/Nachtalb>`_ | This extension licensed under the `GNU General Public License v3.0 <https://github.com/Nachtalb/DanbooruChannelBot/blob/master/LICENSE>`_.
