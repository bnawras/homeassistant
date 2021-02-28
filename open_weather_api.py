import time
import httpx


class Weather:
    def __init__(self, temperature, perceived_temperature, wind_speed, description, icon):
        self.temperature = temperature
        self.perceived_temperature = perceived_temperature
        self.wind_speed = wind_speed
        self.description = description
        self.icon = icon


class OpenWeatherApi:
    def __init__(self, api_key, default_city):
        self._api_key = api_key
        self._default_city = default_city
        self._http_client = httpx.AsyncClient()

    async def get_current_weather(self, city=None):
        city = city if city else self._default_city
        url = f'https://api.openweathermap.org/data/2.5/weather?q={city}&appid={self._api_key}&lang=ru&units=metric'
        response = await self._http_client.get(url)
        weather_data = response.json()
        return Weather(
            temperature=round(weather_data['main']['temp']),
            perceived_temperature=round(weather_data['main']['feels_like']),
            wind_speed=weather_data['wind']['speed'],
            description=weather_data['weather'][0]['description'],
            icon=self._get_emoji(weather_data['weather'][0]['icon'])
        )

    async def get_hourly_forecast(self):
        exclude = ','.join(['current', 'minutely', 'daily', 'alerts'])
        url = f'https://api.openweathermap.org/data/2.5/onecall?lat=55.17264&lon=61.28517&appid={self._api_key}&exclude={exclude}&lang=ru&units=metric'
        response = await self._http_client.get(url)
        forecast_data = response.json()['hourly']

        return [(time.localtime(hour_data['dt']), Weather(
            temperature=round(hour_data['temp']),
            perceived_temperature=round(hour_data['feels_like']),
            wind_speed=round(hour_data['wind_speed']),
            description=hour_data['weather'][0]['description'],
            icon=self._get_emoji(hour_data['weather'][0]['icon'])
        ))
            for hour_data in forecast_data
        ]

    async def get_daily_forecast(self):
        exclude = ','.join(['current', 'minutely', 'hourly', 'alerts'])
        url = f'https://api.openweathermap.org/data/2.5/onecall?lat=55.17264&lon=61.28517&appid={self._api_key}&exclude={exclude}&lang=ru&units=metric'
        response = await self._http_client.get(url)

        daily_forecast = []
        for day_data in response.json()['daily']:
            emoji = self._get_emoji(day_data['weather'][0]['icon'])
            description = day_data['weather'][0]['description']
            keys_data = [(7, 'morn'), (13, 'day'), (18, 'eve'), (22, 'night')]
            for hour, key in keys_data:
                forecast_date = time.localtime(day_data['dt'])
                forecast = Weather(
                    temperature=day_data['temp'][key],
                    perceived_temperature=day_data['feels_like'][key],
                    wind_speed=day_data['wind_speed'],
                    description=description,
                    icon=emoji
                )
                forecast_date = list(forecast_date)
                forecast_date[3] = hour
                forecast_date = tuple(forecast_date)
                forecast_date = time.struct_time(forecast_date)
                daily_forecast.append((forecast_date, forecast))

        return daily_forecast

    def _get_emoji(self, icon_code):
        icon_to_emoji = {
            '01': '☀',
            '02': '🌤',
            '03': '🌥',
            '04': '☁',
            '09': '🌧',
            '10': '🌧',
            '11': '🌩',
            '13': '🌨',
            '50': '🌫',
        }

        emoji = icon_to_emoji.get(icon_code[:-1])
        return emoji if emoji else f'[{icon_code}] '




