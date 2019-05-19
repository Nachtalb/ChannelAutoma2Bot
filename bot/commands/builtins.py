from django.template.loader import get_template

from bot.commands import BaseCommand


class Builtins(BaseCommand):
    @BaseCommand.command_wrapper()
    def help(self):
        self.message.reply_html(get_template('commands/builtins/help.html').render())
