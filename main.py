from time import struct_time
from datetime import datetime
from typing import List, Tuple
from collections import defaultdict
from pyrogram import Client
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from open_weather_api import OpenWeatherApi, Weather
from visualizer import get_weather_chart, get_weather_boxplot

navras = 424166845
family = -1001274663590

api_token = '661048849:AAGciZcO2kf5xbCmo6mCOw4jYEZigG9yW6U'
api_id = '2880911'
api_hash = 'c35fedf80a22745acf13f3b23cbf4b4c'

app = Client(
    session_name='notifier',
    bot_token=api_token,
    api_id=api_id,
    api_hash=api_hash
)
space = '&nbsp;'

open_weather_api_key = 'b5a14aa055cb8b3a3f52b36006d49cd7'
open_weather = OpenWeatherApi(open_weather_api_key, 'челябинск')

scheduler = AsyncIOScheduler()


@app.on_message()
async def hello(client, message):
    if 'прогноз' in message.text.lower():
        await send_hourly_forecast(message.chat.id)

    if 'неделя' in message.text.lower():
        await send_daily_forecast(message.chat.id)

    if 'погода' in message.text.lower():
        await send_current_weather(message.chat.id)


async def send_current_weather(chat_id):
    weather = await open_weather.get_current_weather()
    message = (
        f'**ПОГОДА:**\n'
        f'{weather.icon} &nbsp; {weather.description}\n'
        f'🌡 &nbsp; {weather.temperature} | {weather.perceived_temperature} ℃\n'
        f'🌬 &nbsp; {weather.wind_speed} м/с'
    )
    await app.send_message(chat_id, message)


async def send_hourly_forecast(chat_id):
    weathers = await open_weather.get_hourly_forecast()
    caption = form_message_for_today_and_yesterday(weathers)
    weathers = [w for i, w in enumerate(weathers[4:]) if i % 3 == 0]
    await app.send_photo(chat_id, get_weather_chart(weathers), caption=caption)


async def send_daily_forecast(chat_id):
    daily_forecast = await open_weather.get_daily_forecast()
    walking_days, warmest_day = find_walking_days(daily_forecast)
    if walking_days:
        caption = f"можно погулять в {', '.join(walking_days)}"
    else:
        caption = f'самый теплый день {warmest_day[0]}({warmest_day[1]})'
    # TODO: график сложноват, может просто 3 линии для утра/дня
    await app.send_photo(chat_id, get_weather_boxplot(daily_forecast), caption=f'Прогноз на 7 дней\n{caption}')


# TODO: refactor and rename
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
    # TODO: топ дня пригодных для прогулок
    '''
    можно еще дожди сильные ветра предупреждать
    '''
    today = datetime.today().weekday()
    weathers = [
        (date.tm_wday, weather.temperature)
        for date, weather in weathers if date.tm_mday != today and date.tm_hour == 13
    ]

    walking_days = filter(lambda x: x[1] > -15, weathers)
    number_to_weekday = dict(zip(range(7), ['ПН', 'ВТ', 'СР', 'ЧТ', 'ПТ', 'СБ', 'ВС']))
    walking_days = [number_to_weekday[day] for day, temp in walking_days]
    warmest_day = max(weathers, key=lambda x: x[1])

    return walking_days, (number_to_weekday[warmest_day[0]], warmest_day[1])


scheduler.add_job(app.send_message, 'cron', hour=8, minute=10, args=[family, 'Утро доброе!'])
scheduler.add_job(send_current_weather, 'cron', hour=8, minute=10, args=[family])
scheduler.add_job(send_hourly_forecast, 'cron', hour=8, minute=10, args=[family])
scheduler.add_job(send_daily_forecast, 'cron', hour=15, day_of_week=5, args=[family])
scheduler.start()

app.run()


# TODO: add config file
# TODO: рефакторинг -> commit/push
# анализ запросов рынка




