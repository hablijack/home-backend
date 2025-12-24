import requests
import json
from datetime import datetime


def fetch():
    FORECAST_URL = 'https://hop.maschinenring.de/api/weather/7days/49.9829487/12.0663612/0'
    ICON_URL = 'https://www.maschinenring.de/typo3conf/ext/mr_weatherbase/Resources/Public/Images/weathericons/day/large/semrw_'
    CONDITIONS = {
        1 : 'wolkenlos',
        2 : 'sonnig und heiß',
        3 : 'gering bewölkt, meist sonnig',
        4 : 'wechselnd bewölkt, teils sonnig',
        5 : 'wechselnd bewölkt mit Regenschauern',
        6 : 'wechselnd bewölkt mit Schneeregen',
        7 : 'wechselnd bewölkt mit Schneeschauern',
        8 : 'stark bewölkt',
        9 : 'dicht bewölkt mit Regen',
        10 : 'Regen',
        11 : 'dicht bewölkt mit Schneefall',
        12 : 'dicht bewölkt mit Schneeregen',
        13 : 'Gewitter',
        14 : 'Nebel',
        15 : 'Hochnebel',
        16 : 'meist sonnig',
    }

    try:
        forecast = []
        headers = {'User-Agent': 'Mozilla/5.0'}
        page = requests.get(FORECAST_URL, headers=headers)
        json_obj = json.loads(page.content.decode('utf-8'))
        for day in json_obj['result']['daily']:
            day_condition = {
                'day' : day['timestamp'],
                'condition' : CONDITIONS.get(day['weatherTypeID']),
                'min_temp' : day['tmin'],
                'max_temp' : day['tmax'],
                'prec_amount' : day['precSum'],
                'prec_text' : get_precipitation_text(day['weatherTypeID']),
                'prec_prob' : get_precipitation_probability(json_obj['result']['hourly'],day),
                'icon' : ICON_URL + str(day['weatherTypeID']) + '.png'
            }
            forecast.append(day_condition)
        print(forecast)
    except Exception as e:
        print(e)


def get_precipitation_probability(hourly_forecast, day):
    prec_prob = 0
    for hour in hourly_forecast:
        if datetime.fromtimestamp(hour['timestamp']).date() == datetime.fromtimestamp(day['timestamp']).date():
            if hour['precRisk'] > prec_prob:
                prec_prob = hour['precRisk']
    return prec_prob

def get_precipitation_text(type_id):
    prec_text = ''        
    if type_id in [6, 7, 11, 12]:
        prec_text = ' cm Neuschnee'
    else:
        prec_text = ' mm Regen'
    return prec_text



fetch()