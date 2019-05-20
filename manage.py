#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys

import dotenv


def main():
    dotenv.read_dotenv()
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bot.settings.settings')

    from configurations.management import execute_from_command_line

    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
