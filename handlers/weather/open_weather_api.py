import time
import httpx

WEEKDAYS = ['ПН', 'ВТ', 'СР', 'ЧТ', 'ПТ', 'СБ', 'ВС']


class Weather:
    def __init__(self, temperature, perceived_temperature, wind_speed, description, icon):
        self.temperature = temperature
        self.perceived_temperature = perceived_temperature
        self.wind_speed = wind_speed
        self.description = description
        self.icon = icon
        self.lat = self.lon = None


class City:
    def __init__(self, name: str, lat: float, lon: float):
        self.name = name
        self.lat = lat
        self.lon = lon


class OpenWeatherApi:
    def __init__(self, api_key, default_city: City):
        self._api_key = api_key
        self._default_city = default_city
        transport = httpx.AsyncHTTPTransport(retries=3)
        self._http_client = httpx.AsyncClient(transport=transport)

    async def get_current_weather(self, city=None):
        city = city if city else self._default_city
        url = f'https://api.openweathermap.org/data/2.5/weather?q={city.name}&appid={self._api_key}&lang=ru&units=metric'
        response = await self._http_client.get(url)
        weather_data = response.json()
        return Weather(
            temperature=round(weather_data['main']['temp']),
            perceived_temperature=round(weather_data['main']['feels_like']),
            wind_speed=weather_data['wind']['speed'],
            description=weather_data['weather'][0]['description'],
            icon=self._get_emoji(weather_data['weather'][0]['icon'])
        )


    async def get_coordinates(self, city):
        url = f'http://api.openweathermap.org/geo/1.0/direct?q={city}&limit=1&appid={self._api_key}'
        response = await self._http_client.get(url)
        response.raise_for_status()
        data = response.json()
        return data[0]['lat'], data[0]['lon']

    async def get_hourly_forecast(self):
        exclude = ','.join(['current', 'minutely', 'daily', 'alerts'])
        url = f'https://api.openweathermap.org/data/3.0/onecall?lat={self._default_city.lat}&lon={self._default_city.lon}&exclude={exclude}&appid={self._api_key}&lang=ru&units=metric'
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
        url = f'https://api.openweathermap.org/data/3.0/onecall?lat={self._default_city.lat}&lon={self._default_city.lon}&exclude={exclude}&appid={self._api_key}&lang=ru&units=metric'
        response = await self._http_client.get(url)

        daily_forecast = []
        print(response)
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




# http://api.openweathermap.org/geo/1.0/direct?q=London&limit=5&appid={API key}
# нужна подписать на one callб 1000 запросов бесплатно, но надо указать карту. Такдже можно явно огранчить в настройках лимит, не больше 1000 запросов в день