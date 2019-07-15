from peewee import *


db = SqliteDatabase('weather.db')


class WeatherLog(Model):
    dt = DateField()
    precipitation = FloatField()
    temp_curr = FloatField()
    temp_hi = FloatField()
    temp_low = FloatField()
    raw_info = TextField()

    class Meta:
        database = db # this model uses the "people.db" database


class Weather:
    def __init__(self, precipitation, curr_temp, hi_temp, low_temp):
        self.precipitation = precipitation
        self.curr_temp = curr_temp
        self.hi_temp = hi_temp
        self.low_temp = low_temp


db.connect()
db.create_tables([WeatherLog])


