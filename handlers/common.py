from telethon import TelegramClient, events
from telethon.events.newmessage import NewMessage

def register_common_handlers(client: TelegramClient):
    @client.on(events.NewMessage(pattern='/start'))
    async def welcome(event: NewMessage.Event):
        welcome_message = 'Привет!'
        await client.send_message(event.chat_id, welcome_message)
        await docs(event)


    @client.on(events.NewMessage(pattern='/help'))
    async def docs(event: NewMessage.Event):
        help_message = '''Напиши мне:
    
    - __погода__ - чтобы получить текущую погоду
    - __прогноз__ - чтобы получить прогноз погоды на сегодня и завтра
    - __неделя__ - чтобы получить прогноз погоды на неделю
    - __неправильные глаголы__ - чтоб начать учить неправильные глаголы с помощью карточек
    
    Пока это все, что мне разрешили показывать всем 😉
        '''
        return await client.send_message(event.chat_id, help_message)