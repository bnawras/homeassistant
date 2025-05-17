import asyncio
import logging
from time import struct_time
from typing import List, Tuple
from collections import defaultdict
from datetime import timedelta, datetime

from telethon import TelegramClient, Button, events
from telethon.events.newmessage import NewMessage

from .open_weather_api import OpenWeatherApi, Weather, WEEKDAYS, City
from .visualizer import get_weather_boxplot, get_weather_chart
from utils import delete_message, scheduler

logger = logging.getLogger(__name__)

def register_weather_handlers(client: TelegramClient, config, family):
    open_weather = OpenWeatherApi(
        api_key=config['api_token'],
        default_city=City(**config['city'])
    )

    async def send_current_weather(client, chat_id):
        weather = await open_weather.get_current_weather()
        message = (
            f'**Сейчас на улице:**\n'
            f'{weather.icon} {weather.temperature} ({weather.perceived_temperature}) ℃, {weather.wind_speed} м/с\n'
        )
        return await client.send_message(chat_id, message)

    async def send_hourly_forecast(client, chat_id):
        weathers = await open_weather.get_hourly_forecast()
        message = form_message_for_today_and_yesterday(weathers)
        buttons = [[Button.inline('Подробный график', 'hourly_forecast')]]
        return await client.send_message(
            entity=chat_id,
            message=message,
            buttons=buttons,
        )

    async def send_daily_forecast(client, chat_id):
        daily_forecast = await open_weather.get_daily_forecast()
        walking_days, warmest_day = find_walking_days(daily_forecast)
        if len(walking_days) > 6:
            caption = 'Неделя будет теплой'
        elif len(walking_days) > 3:
            caption = f"Можно погулять в {', '.join(walking_days)}"
        elif walking_days:
            caption = f"Холодно будет в {', '.join(set(WEEKDAYS) - walking_days)}"
        else:
            caption = f'Самый теплый день {warmest_day[0]}({warmest_day[1]})'

        return await client.send_photo(chat_id, get_weather_boxplot(daily_forecast), caption=caption)

    # TODO: refactor and rename
    # TODO: если погода не сильно отличает по температура и одинаковая облачность, схлопать в короткое сообщение
    def form_message_for_today_and_yesterday(weathers):
        today_weekday = datetime.today().weekday()
        tomorrow_weekday = (today_weekday + 1) % 7

        message_parts = defaultdict(list)
        for date, weather in weathers:
            if date.tm_wday == today_weekday:
                day = 'сегодня'
            elif date.tm_wday == tomorrow_weekday:
                day = 'завтра'
            else:
                break

            if date.tm_hour == 7:
                prefix = 'утром'
            elif date.tm_hour == 13:
                prefix = 'днем'
            elif date.tm_hour == 18:
                prefix = 'вечером'
            else:
                continue

            message_parts[day].append(
                f'{weather.icon} {weather.temperature:5d} {prefix}'
            )

        delimiter = '\n• '
        return '\n'.join([
            f'{day}:{delimiter}' + delimiter.join(forecasts)
            for day, forecasts in message_parts.items()
        ])

    def find_walking_days(weathers: List[Tuple[struct_time, Weather]]):
        '''
        можно еще дожди сильные ветра предупреждать
        '''
        today = datetime.today().weekday()
        weathers = [
            (date.tm_wday, weather.temperature)
            for date, weather in weathers if date.tm_mday != today and date.tm_hour == 13
        ]

        walking_days = filter(lambda x: x[1] > -15, weathers)
        number_to_weekday = dict(zip(range(7), WEEKDAYS))
        walking_days = [number_to_weekday[day] for day, temp in walking_days]
        warmest_day = max(weathers, key=lambda x: x[1])

        return walking_days, (number_to_weekday[warmest_day[0]], warmest_day[1])

    async def morning_information(client, chat_id):
        tasks = [
            client.send_message(chat_id, 'Утро доброе!'),
            send_current_weather(client, chat_id),
            # send_hourly_forecast(client, chat_id),
        ]

        tomorrow = datetime.today() + timedelta(days=1)
        for task in tasks:
            response = await task
            task = delete_message(client, tomorrow, chat_id, response.id)
            asyncio.create_task(task)

    async def weekly_information(client, chat_id):
        response = await send_daily_forecast(client, chat_id)
        next_week = datetime.today() + timedelta(days=7)
        task = delete_message(client, next_week, chat_id, response.id)
        asyncio.create_task(task)

    @client.on(events.CallbackQuery(pattern='hourly_forecast.*'))
    async def answer(event: NewMessage.Event):
        if event.data == 'hourly_forecast':
            weathers = await open_weather.get_hourly_forecast()
            today_weekday = datetime.today().weekday()
            weathers = [w for i, w in enumerate(weathers[4:]) if
                        i % 3 == 0 and w[0].tm_wday in [today_weekday, (today_weekday + 1) % 7]]

            chart = get_weather_chart(weathers)
            await client.send_photo(event.chat_id, photo=chart, caption='Подробный прогноз')
        else:
            logger.error(event.data)

    @client.on(events.NewMessage(pattern='.*прогноз.*'))
    async def hourly_forecast(event: NewMessage.Event):
        await send_hourly_forecast(client, event.chat_id)

    @client.on(events.NewMessage(pattern='.*неделя.*'))
    async def daily_forecast(event: NewMessage.Event):
        await send_daily_forecast(client, event.chat_id)

    @client.on(events.NewMessage(pattern='.*погода.*'))
    async def current_weather(event: NewMessage.Event):
        await send_current_weather(client, event.chat_id)

    scheduler.add_job(morning_information, 'cron', hour=9, minute=8, args=[client, family])
    scheduler.add_job(weekly_information, 'cron', hour=15, day_of_week=5, args=[client, family])