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


Copyright
---------

Made by `Nachtalb <https://github.com/Nachtalb>`_ | This extension licensed under the `GNU General Public License v3.0 <https://github.com/Nachtalb/DanbooruChannelBot/blob/master/LICENSE>`_.
