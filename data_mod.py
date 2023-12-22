"""
Collect data from charts and calculate standard deviation and mean
witch needs to neuro network generated prediction
"""

import logging
import time
from datetime import datetime, date, timedelta
import calendar
import json
import os.path
from collections import defaultdict

import requests
import numpy as np
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from webdriver_manager.firefox import GeckoDriverManager


def remove_unwanted_keys(data, current_supply=False):
    """
    Remove keys from dictionary witch don`t need for further work

    :param data: dictionary from which keys are removed
    :param current_supply: Add current_supply key to list of unwanted keys or not
    """
    unwanted_keys = ['id', 'symbol', 'zero_balance_addresses_all_time', 'unique_addresses_all_time',
                     'transaction_count_all_time', 'large_transaction_count', 'average_transaction_value',
                     'block_height', 'hashrate', 'block_time', 'block_size']
    if current_supply:
        unwanted_keys.append('current_supply')
    for d in data:
        for key in unwanted_keys:
            d.pop(key, None)


def chain():
    """
    Collecting data from cryptocompare.com - state of the chain.
    Data from the beginning of 2017.

    :return: dictionary with following keys: new_addresses, active_addresses,
        transaction_count and difficulty
    """
    response = requests.get(
        'https://min-api.cryptocompare.com/data/blockchain/histo/day?fsym=BTC&limit=2000&api_key'
        '=fe4dc332ae0ae1ffce6cd512d7fe1cb7484d59d2001c2592221b13ae25d955f0')

    data = json.loads(response.text)['Data']['Data']
    remove_unwanted_keys(data)
    for k in range(len(data)):
        try:
            data[k].pop('current_supply')
        except Exception:
            pass

    time_ = data[0]['time']
    response = requests.get(
        f'https://min-api.cryptocompare.com/data/blockchain/histo/day?fsym=BTC&limit=2000&toTs={time_}&api_key'
        f'=fe4dc332ae0ae1ffce6cd512d7fe1cb7484d59d2001c2592221b13ae25d955f0')

    data1 = json.loads(response.text)['Data']['Data']
    remove_unwanted_keys(data, current_supply=True)
    data = data1[:2000] + data
    data = [d for d in data if datetime.utcfromtimestamp(int(d['time'])).year > 2016]

    return data


def price():
    """
    Collecting data from cryptocompare.com - price of bitcoin.
    Data from the beginning of 2017.

    :return: dictionary with following keys: open, close, low, high,
        volumefrom and volumeto
    """
    response = requests.get('https://min-api.cryptocompare.com/data/v2/histoday?fsym=BTC&tsym=USD&allData=true',
                            headers=headers)

    data = json.loads(response.text)['Data']['Data']
    for d in data:
        del d['conversionType']
        del d['conversionSymbol']
    data = [d for d in data if datetime.utcfromtimestamp(int(d['time'])).year > 2016]

    return data


def tweets():
    """
    Collecting data from bitinfocharts.com - twits about bitcoin.
    Data from the beginning of 2017.

    :return: dictionary with timestamp as key and number of twits as value
    """
    response = requests.get('https://bitinfocharts.com/comparison/tweets-btc.html#alltime', headers=headers, )
    tweet_dict = {}
    text = response.text

    mark1 = text.find('getElementById("container"),')
    mark2 = text.find(', {labels:')

    text = text[mark1 + 29:mark2 - 1]

    while text.find('[') != -1:
        m1 = text.find('[')
        m2 = text.find(']')
        sub = text[m1 + 1:m2]
        text = text[m2 + 1:]
        m1 = sub.find('("')
        m2 = sub.find('")')
        data = sub[m1 + 2:m2]
        m1 = sub.find(',')
        tweet_stat = sub[m1 + 1:]
        try:
            date_ = datetime.strptime(data, "%Y/%m/%d").date()
            timestamp1 = calendar.timegm(date_.timetuple())
            tweet_dict[str(timestamp1)] = tweet_stat
        except ValueError:
            pass

    clean_dict = {k: v for k, v in tweet_dict.items() if datetime.utcfromtimestamp(float(k)).year > 2016}

    return clean_dict


def fng():
    """
    Collecting data from alternative.me - fear and greed index.
    Data from the beginning of 2017.

    :return: list of dictionaries with timestamp as key and fear and greed index as value
    """
    response = requests.get('https://api.alternative.me/fng/?limit=0', headers=headers)
    data = json.loads(response.text)['data']
    data[0].pop('time_until_update')
    for d in data:
        d.pop('value_classification')
    data = [d for d in data if datetime.utcfromtimestamp(int(d['timestamp'])).year > 2016]

    return data


def dominate_data(url):
    """
    Collecting data from url - bitcoin dominance index.

    :return: list of dictionaries with timestamp as key and bitcoin dominance index as value
    """
    try:
        options = Options()
        options.headless = False
        with webdriver.Firefox(options=options, service=Service(log_path=os.devnull,
                                                                executable_path=GeckoDriverManager().install())) as browser:
            browser.get(url)
            text = browser.page_source
    except Exception:
        return None

    m1 = text.find('<div id="json">[')
    text = text[m1 + 15:]
    m1 = text.find(',{"name":"ETH"')
    text = text[1:m1]
    data = json.loads(text)
    data = data['data']

    return data


def dominate():
    """
    Combining data from two samples on Bitcoin dominance
    Data from the beginning of 2017 and data for the last 90 days

    :return: list of dictionaries with timestamp as key and bitcoin dominance index as value
    """

    def timestamp_to_seconds(timestamp):
        return int(timestamp / 1000)

    data1 = data2 = None
    while data1 is None or data2 is None:
        time.sleep(3)
        data1 = dominate_data('https://www.coingecko.com/global_charts/market_dominance_data?locale=en')
        data2 = dominate_data('https://www.coingecko.com/global_charts/market_dominance_data?duration=90&amp;locale=en')

    data1 = [d for d in data1 if timestamp_to_seconds(d[0]) > 2016]
    data_all = data1 + data2

    data_all = [[timestamp_to_seconds(d[0]), d[1]] for d in data_all]

    return data_all


logging.disable(logging.CRITICAL)

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 '
                  'Safari/537.36'}

yesterday = date.today() - timedelta(days=1)

chain = chain()
price = price()
tweets = tweets()
fng = fng()
dom = dominate()

all_data = []

start_date = '01/01/2017'
end_date = yesterday.strftime("%d/%m/%Y")
date_object = datetime.strptime(end_date, "%d/%m/%Y").date()
timestamp_end = calendar.timegm(date_object.timetuple())
date_object = datetime.strptime(start_date, "%d/%m/%Y").date()
timestamp_start = calendar.timegm(date_object.timetuple())
num_days = (timestamp_end - timestamp_start) // 86400
tss = [timestamp_start + 86400 * k for k in range(num_days + 1)]

fng_dict = {d['timestamp']: d['value'] for d in fng}
dom_dict = {d[0]: d[1] for d in dom}

all_day_data = defaultdict(int)
j = 0
for i in tss:
    all_day_data['time'] = i
    try:
        if chain[j]['time'] == i:
            all_day_data['newaddr'] = chain[j]['new_addresses']
            all_day_data['actaddr'] = chain[j]['active_addresses']
            all_day_data['trans'] = chain[j]['transaction_count']
            all_day_data['diff'] = chain[j]['difficulty']
        if price[j]['time'] == i:
            all_day_data['open'] = price[j]['open']
            all_day_data['close'] = price[j]['close']
            all_day_data['low'] = price[j]['low']
            all_day_data['high'] = price[j]['high']
            all_day_data['vsell'] = price[j]['volumefrom']
            all_day_data['vbuy'] = price[j]['volumeto']
        all_day_data['fng'] = int(fng_dict.get(str(i), 0))
        all_day_data['dom'] = dom_dict.get(i, 0)
    except Exception as e:
        print(f"An exception occurred while processing timestamp {i}: {e}")
    try:
        all_day_data['tweet'] = int(tweets.get(str(i), 0))
    except Exception:
        all_day_data['tweet'] = 0

    all_data.append(dict(all_day_data))
    j += 1

data_one = [[d['newaddr'], d['actaddr'], d['diff'], d['open'], d['low'],
             d['high'], d['vbuy'], d['fng'], d['tweet'], d['dom']] for d in all_data[:-1]]

data_one = np.array(data_one, dtype=np.float32)
mean = data_one.mean(axis=0)
std = data_one.std(axis=0)
