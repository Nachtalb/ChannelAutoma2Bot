from typing import List, Tuple

import emoji as emoji
from django.template.loader import get_template
from telegram import Bot, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, Filters, MessageHandler

from bot.commands import BaseCommand
from bot.filters import Filters as OwnFilters
from bot.models.channel_settings import ChannelSettings
from bot.models.reactions import Reaction
from bot.models.usersettings import UserSettings
from bot.utils.chat import build_menu, channel_selector_menu


class AutoReaction(BaseCommand):
    BaseCommand.register_start_button('Reactions')

    @BaseCommand.command_wrapper(MessageHandler, filters=OwnFilters.in_channel & (Filters.text | OwnFilters.is_media))
    def auto_reaction(self):
        if not self.channel_settings or not self.channel_settings.reactions:
            return

        reactions = self.get_reactions(self.channel_settings)
        buttons = []
        for emoji, total in reactions:
            if not total:
                text = emoji
            else:
                text = f'{emoji} {total}'
            buttons.append(InlineKeyboardButton(text, callback_data=f'reaction:{self.message.message_id}:{emoji}'))
        self.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup([buttons]))

    def get_reactions(self, channel: ChannelSettings) -> List[Tuple[str, int]]:
        result = []
        for emoji in channel.reactions:
            try:
                reaction = Reaction.objects.get(reaction=emoji, message=self.message.message_id, channel=self.channel_settings)
            except Reaction.DoesNotExist:
                reaction = Reaction.objects.create(reaction=emoji, message=self.message.message_id, channel=self.channel_settings)
            result.append((emoji, reaction.users.count()))
        return result

    @BaseCommand.command_wrapper(CallbackQueryHandler, pattern='^reaction:.*')
    def update_reaction(self):
        query: CallbackQuery = self.update.callback_query
        data = query.data
        _, message_id, emoji = data.split(':')
        try:
            reactions = Reaction.objects.filter(message=message_id, channel=self.channel_settings)

            clicked = reactions.get(reaction=emoji)
        except Exception:
            query.answer('Sorry, something went wrong.')
            return

        if clicked.users.filter(pk=self.user_settings.pk).exists():
            query.answer('You have already reacted with this.')
            return

        for reaction in reactions.filter(users=self.user_settings).all():
            reaction.users.remove(self.user_settings)
            reaction.save()

        clicked.users.add(self.user_settings)
        clicked.save()
        query.answer(f'You reacted with {emoji}')
        self.auto_reaction()

    @BaseCommand.command_wrapper(MessageHandler,
                                 filters=OwnFilters.text_is('Reactions') & OwnFilters.state_is(UserSettings.IDLE))
    def caption_menu(self):
        menu = channel_selector_menu(self.user_settings, 'change_reactions')
        message = get_template('commands/auto_reactions/main.html').render()

        if not menu:
            self.message.reply_text(message)
            self.message.reply_text('No channels added yet.')
            return

        self.user_settings.state = UserSettings.SET_REACTIONS_MENU
        self.message.reply_html(message, reply_markup=ReplyKeyboardMarkup([['Cancel']]))
        self.message.reply_text('Channels:', reply_markup=menu)

    @BaseCommand.command_wrapper(CallbackQueryHandler, pattern='^change_reactions:.*$')
    def pre_set_reaction(self):
        channel_id = int(self.update.callback_query.data.split(':')[1])
        member = self.bot.get_chat_member(chat_id=channel_id, user_id=self.user.id)

        if not member.can_change_info and not member.status == member.CREATOR:
            self.message.reply_text('You must have change channel info permissions to change the reactions.')
            return

        self.user_settings.current_channel = ChannelSettings.objects.get(channel_id=channel_id)
        self.user_settings.state = UserSettings.SET_REACTIONS

        self.update.callback_query.answer()
        self.message.delete()

        reactions = self.user_settings.current_channel.reactions
        reaction_str = None
        if reactions:
            reaction_str = ', '.join(reactions)

        message = get_template('commands/auto_reactions/new.html').render({
            'channel_name': self.user_settings.current_channel.name,
            'current_reactions': reaction_str,
        })

        self.message.reply_html(message, reply_markup=ReplyKeyboardMarkup(build_menu('Clear', 'Cancel')))

    @BaseCommand.command_wrapper(MessageHandler, filters=OwnFilters.state_is(UserSettings.SET_REACTIONS))
    def set_reactions(self):
        text = self.message.text_markdown

        if not text:
            self.message.reply_text('You have to send me some emojis.')
            return
        elif text in ['Cancel', 'Home']:
            return
        elif text == 'Clear':
            reactions = None
        else:
            emojis = emoji.emoji_lis(self.message.text)
            reactions = [reaction['emoji'] for reaction in emojis]

        if reactions is None:
            self.user_settings.current_channel.reactions = None
            message = f'Reactions for {self.user_settings.current_channel.name} cleared'
        elif not reactions:
            message = f'No reactions given. You have to give me emojis as reactions.'
        else:
            message = f'Reactions of {self.user_settings.current_channel.name} were set to:\n{", ".join(reactions)}'
            self.user_settings.current_channel.reactions = reactions
        self.user_settings.current_channel.save()

        self.message.reply_markdown(message, reply_markup=ReplyKeyboardMarkup([['Clear', 'Home']]))
