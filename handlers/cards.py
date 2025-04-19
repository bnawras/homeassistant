import json
import random

from telethon import events, Button, TelegramClient
from telethon.events.newmessage import NewMessage


class CardsReader:
    def __init__(self, dictionary_path):
        with open(dictionary_path) as file:
            self._words = json.load(file)

        self._sides = dict()

    def __iter__(self):
        random.shuffle(self._words)
        for word_forms in self._words:
            front_side = random.choice(word_forms)
            back_side = ' - '.join(word_forms)
            self._sides[front_side] = back_side
            self._sides[back_side] = front_side
            yield front_side

    def __getitem__(self, side):
        return self._sides[side]


def get_next_card(dictionary_path):
    with open(dictionary_path) as file:
        words = json.load(file)

    while True:
        random.shuffle(words)
        for word_forms in words:
            front_side = random.choice(word_forms)
            yield front_side, '; '.join(word_forms)


def register_irregular_en_verb_cards(client: TelegramClient):
    cards_session = {}
    cards_reader = CardsReader('irregular verbs.json')

    def next_card():
        while True:
            for card in cards_reader:
                yield card

    cards_iterator = next_card()

    @client.on(events.NewMessage(pattern='.*неправильные глаголы.*'))
    async def cards(event: NewMessage.Event):
        buttons = [[Button.inline("Let's start!", 'card-next')]]
        await client.send_message(
            entity=event.chat_id,
            message='Irregular verbs',
            buttons=buttons,
        )

    @client.on(events.CallbackQuery(pattern='card-next'))
    async def answer(event: NewMessage.Event):
        front_side = next(cards_iterator)
        cards_session[event.message_id] = front_side

        buttons = [
            [Button.inline(front_side, 'card-next')],
            [Button.inline('turn card', 'card-turn')],
        ]

        await event.edit(buttons=buttons)
        await event.answer()

    @client.on(events.CallbackQuery(pattern='card-turn'))
    async def answer(event: NewMessage.Event):
        front_side = cards_session[event.message_id]
        other_side = cards_reader[front_side]

        buttons = [
            [Button.inline(other_side, 'card-next')],
            [Button.inline('turn card', 'card-turn')],
        ]
        await event.edit(buttons=buttons)
        await event.answer()

        cards_session[event.message_id] = other_side