import calendar
import datetime
import json
import logging
import random

import keras
import numpy as np
import requests

import data_mod
import send_to_telegram


def forming_nn_bot_message() -> str:
    """
    Generates a text message based on neural network prediction data

    :return: text message
    """
    dictDays = {0: 'Понедельник', 1: 'Вторник', 2: 'Среда', 3: 'Четверг', 4: 'Пятница', 5: 'Суббота', 6: 'Воскресенье'}
    dictMonth = {1: 'Января', 2: 'Февраля', 3: 'Марта', 4: 'Апреля', 5: 'Мая', 6: 'Июня', 7: 'Июля', 8: 'Августа',
                 9: 'Сентября', 10: 'Октября', 11: 'Ноября', 12: 'Декабря'}

    current_date = datetime.date.today()
    hello_phrase_list = ['Доброго всем дня\n', 'Приветствую, уважаемые\n', 'Мое почтение, криптаны\n',
                         'Приветствую подписчиков\n',
                         'Всем привет\n']

    news_phrase_list = ['Вещает нейросеть:\n', 'Немного предсказаний и метрик:\n']

    api_url = "https://api.alternative.me/fng/?limit=1&format=json&date_format=world"
    response = requests.get(api_url)
    fng_today = response.json()

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/106.0.0.0 Safari/537.36'}

    domination = data_mod.dom
    today_dom = domination[-1:]
    domination = domination[-8:-1]

    response = requests.get(
        'https://min-api.cryptocompare.com/data/blockchain/histo/day?fsym=BTC&limit=2000&api_key'
        '=fe4dc332ae0ae1ffce6cd512d7fe1cb7484d59d2001c2592221b13ae25d955f0')
    onchain_metrics = json.loads(response.text)['Data']['Data']
    for i in range(len(onchain_metrics)):
        onchain_metrics[i].pop('id')
        onchain_metrics[i].pop('symbol')
        onchain_metrics[i].pop('zero_balance_addresses_all_time')
        onchain_metrics[i].pop('unique_addresses_all_time')
        onchain_metrics[i].pop('transaction_count_all_time')
        onchain_metrics[i].pop('large_transaction_count')
        onchain_metrics[i].pop('average_transaction_value')
        onchain_metrics[i].pop('block_height')
        onchain_metrics[i].pop('hashrate')
        onchain_metrics[i].pop('block_time')
        onchain_metrics[i].pop('block_size')
        try:
            onchain_metrics[i].pop('current_supply')
        except Exception:
            pass

    onchain_metrics = onchain_metrics[-7:]

    response = requests.get('https://min-api.cryptocompare.com/data/v2/histoday?fsym=BTC&tsym=USD&allData=true')
    price_metrics = json.loads(response.text)['Data']['Data']

    price_metrics = [dict((k, v) for k, v in d.items() if k not in ['conversionType', 'conversionSymbol']) for d in
                     price_metrics]

    today_open_price = price_metrics[-1]['open']
    yest_open_price = price_metrics[-2]['open']

    up_or_down = int(today_open_price > yest_open_price)

    price_metrics = price_metrics[-8:-1]

    response = requests.get('https://api.alternative.me/fng/?limit=0', headers=headers)
    fear_and_greed_index = json.loads(response.text)['data']

    for i in range(len(fear_and_greed_index)):
        fear_and_greed_index[i].pop('value_classification')
        if i == 0:
            fear_and_greed_index[i].pop('time_until_update')

    fear_and_greed_index = fear_and_greed_index[1:8]
    fear_and_greed_index.reverse()

    response = requests.get('https://bitinfocharts.com/comparison/tweets-btc.html#alltime', headers=headers)
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
        tweets = sub[m1 + 1:]
        date_object = datetime.datetime.strptime(data, "%Y/%m/%d").date()
        timestamp1 = calendar.timegm(date_object.timetuple())
        tweet_dict[str(timestamp1)] = tweets
    tweets = []
    for i in tweet_dict.keys():
        try:
            tweets.append([int(i), float(tweet_dict[i])])
        except ValueError:
            tweets.append([int(i), float(0)])

    tweets = tweets[-8:-1]

    predict_one = [[onchain_metrics[6]['new_addresses'], onchain_metrics[6]['active_addresses'],
                    onchain_metrics[6]['difficulty'],
                    price_metrics[6]['open'], price_metrics[6]['low'], price_metrics[6]['high'],
                    price_metrics[6]['volumeto'],
                    int(fear_and_greed_index[6]['value']), tweets[6][1], domination[6][1]]]

    data_one = np.array(predict_one, dtype=np.float32)

    model_0559 = keras.models.load_model('price_model_0559')
    model_9610 = keras.models.load_model('price_model_9610')

    data_one -= data_mod.mean
    data_one /= data_mod.std

    prediction_0559 = model_0559.predict(data_one)
    prediction_9610 = model_9610.predict(data_one)

    average_prediction = np.mean([prediction_0559[0][0], prediction_9610[0][0]])

    with open('last_predicted_price.txt', 'r+', encoding='utf-8') as file:
        last_predicted_price = file.read()
        file.seek(0)
        file.write(str(average_prediction))
        file.truncate()

    prediction_error = int(abs(float(today_open_price) - float(last_predicted_price)))

    with open('prediction_errors.txt', 'a', encoding='utf-8') as file:
        file.write(str(prediction_error))
        file.write('\n')

    with open('prediction_errors.txt', 'r', encoding='utf-8') as file:
        prediction_errors = file.read().split('\n')

    prediction_errors = [value for value in prediction_errors if value != '']
    predicted_up_or_down = int(float(last_predicted_price) > float(yest_open_price))
    is_up_down_equal = int(predicted_up_or_down == up_or_down)

    with open('is_up_down_equals.txt', 'a', encoding='utf-8') as file:
        file.write(str(is_up_down_equal))
        file.write('\n')

    with open('is_up_down_equals.txt', 'r', encoding='utf-8') as file:
        is_up_down_equals = file.read().split('\n')

    total = 0
    for i in range(len(is_up_down_equals)):
        if is_up_down_equals[i]:
            total += int(is_up_down_equals[i])
    predict_trend_accuracy = int((total / (len(is_up_down_equals) - 1)) * 100)

    price_error_message = f"Сегодня дневная свеча биткоина открылась по цене: {today_open_price}$\n\nНейросеть " \
                          f"ошиблась на: {prediction_error:.2f}$\n\n"
    predict_trend_accuracy_message = f"Процент правильно предсказанного тренда: {predict_trend_accuracy}%\n\n"

    trend = 'рост' if today_open_price < average_prediction else 'падение'

    trend_message = f"Тренд на сегодня - {trend}\n\n"
    predict_message = f"Прогноз нейросети на завтра: {average_prediction:.2f}$\n\n"

    mean_error = sum(float(i) for i in prediction_errors if i != '') / len(prediction_errors)

    relative_error_message = f"Средняя ошибка нейросети: {mean_error:.2f}$\n\n"

    today_dom_message = f"Индекс доминирования BTC: {today_dom[0][1]}\n"
    today_fng_message = f"Индекс страха и жадности: {fng_today['data'][0]['value']}\n\n"
    bottom_message = 'По всем вопросам пишите в комментарии или в личку @emulater\n'
    hello_phrase = random.choice(hello_phrase_list)
    news_phrase = random.choice(news_phrase_list)
    text_list = [f"{hello_phrase}\n",
                 f"{current_date.day} {dictMonth[current_date.month]} {dictDays[current_date.weekday()]}\n\n",
                 f"{news_phrase}\n", f"{price_error_message}", f"{trend_message}", f"{predict_trend_accuracy_message}",
                 f"{predict_message}", f"{relative_error_message}", f"{today_dom_message}", f"{today_fng_message}",
                 f"{bottom_message}"]

    final_text = ''.join(text_list)

    return final_text


async def nn_bot():
    """
    send text message to telegram channel
    """
    await send_to_telegram.send_to_channel(method='send_message', text=forming_nn_bot_message())


logging.disable(logging.CRITICAL)
