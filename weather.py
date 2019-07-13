#!/usr/bin/env python3

import http.client
import json
import urllib.request


class OpenWeather:
    OPEN_WEATHER_API_URL = 'http://api.openweathermap.org/data/2.5/'
    WEATHER_API_URL_PATH = 'weather?id={city_id}&APPID={app_id}'
    FORECAST_API_URL_PATH = 'forecast?id={city_id}&APPID={app_id}'

    def __init__(self, app_id, city_id):
        self.app_id = app_id
        self.city_id = city_id
        self.weather = None
        self.forecast = None

    def get_weather_json(self, url_path):
        url = self.OPEN_WEATHER_API_URL + url_path.format(
            city_id=self.city_id,
            app_id=self.app_id
        )

        response = None

        try:
            response = json.loads(urllib.request.urlopen(url).read().decode())
        except http.client.HTTPException as e:
            print('Error loading OpenWeather API: {}'.format(e))
        except ValueError:
            print('Invalid response from OpenWeather API')

        return response

    def get_weather(self):
        print('getting weather')
        if not self.app_id or not self.city_id:
            print('OpenWeather API not configured.')
            return

        self.weather = self.get_weather_json(self.WEATHER_API_URL_PATH)
        self.forecast = self.get_weather_json(self.FORECAST_API_URL_PATH)

    def current_temp(self):
        '''Returns current temperature in celsius.'''
        return int(self.weather['main']['temp'] - 273.15)

    def current_weather_icon(self):
        if 'weather' not in self.weather:
            return None

        return self.weather['weather'][0]['icon']

    def daily_minmax(self):
        minimums = {}
        maximums = {}

        for l in self.forecast['list']:
            date = l['dt_txt'].split(' ')[0]
            temp_min = l['main']['temp_min']
            temp_max = l['main']['temp_max']
            if date not in minimums or temp_min < minimums[date]:
                minimums[date] = temp_min
            if date not in maximums or temp_max > maximums[date]:
                maximums[date] = temp_max

        return [minimums, maximums]
