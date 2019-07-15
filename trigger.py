import datetime
import json
import logging
import requests

from config import AppConfig
from weather_log import WeatherLog, Weather
from logging.handlers import TimedRotatingFileHandler



BASETIME = 180
INC_TIME_PER_DEGREE = 15


def extract_tag(data, tag):
    if isinstance(tag, list):
        out = data
        for t in tag:
            out = out[t]
    else:
        out = data[tag]
    return out['Metric']['Value']

def create_timed_rotating_log(path):
    logger = logging.getLogger("Rotating Log")
    logger.setLevel(logging.INFO)
 
    handler = TimedRotatingFileHandler(path,
                                       when="d",
                                       interval=1,
                                       backupCount=7)
    logger.addHandler(handler)
    return logger

def get_past_weather(logger=None, dummy=False):
    if dummy:
        with open('sample_rsp.json', 'r') as f:
            out = json.load(f)
    else:
        rsp = requests.get(AppConfig.ACCUWEATHER_QUERY)
        out = rsp.json()[0]
        if logger is not None:
            logger.info(out)
        weather = Weather(
                precipitation=extract_tag(out, ['PrecipitationSummary', 'Past24Hours']),
                curr_temp=extract_tag(out, 'Temperature'),
                hi_temp=extract_tag(out, ['TemperatureSummary', 'Past24HourRange', 'Maximum']),
                low_temp=extract_tag(out, ['TemperatureSummary', 'Past24HourRange', 'Minimum'])
                )
        log = WeatherLog(
                dt=datetime.datetime.utcnow(),
                precipitation=weather.precipitation,
                temp_curr=weather.curr_temp,
                temp_hi=weather.hi_temp,
                temp_low=weather.low_temp,
                raw_info=json.dumps(out)
                )
        log.save()
    return out

def get_hi_temp(data):
    return extract_tag(data, ['TemperatureSummary', 'Past24HourRange', 'Maximum'])

def get_precipitation(data):
    return extract_tag(data, ['PrecipitationSummary', 'Past24Hours'])

def get_watering_time(rainfall_mm, hi_temp):
    time = 0
    shortfall = BASETIME - BASETIME / 5 * rainfall_mm + max(hi_temp - 24, 0) * INC_TIME_PER_DEGREE
    if shortfall > 0:
        time = int(shortfall)
    return time

def start_water(secs):
    uri = AppConfig.WATERING_API + '/start/' + str(secs)
    print(uri)
    requests.get(uri, auth=('t2o2', 'omdurman'))

print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
print('creating logger')
logger = create_timed_rotating_log('weather_hist/accuweather.json')
print('getting weather data')
data = get_past_weather(logger)
print('getting precipitation and high temperature')
rainfall = get_precipitation(data)
hi_temp = get_hi_temp(data)
print('rainfall (mm): {}'.format(rainfall))
time = get_watering_time(rainfall, hi_temp)
print('water time (s): {}'.format(time))
start_water(time)
print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
print('finished for the day')

