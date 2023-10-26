import asyncio
import glob
import os
import re
import logging

from bs4 import BeautifulSoup
import requests
import wget


import send_to_telegram


def img_list(text):
    """
    Grabbing urls of images from html code

    :param text: html code of web page with images
    :return: list of urls of images
    """
    if not text:
        raise ValueError("Empty HTML string")
    try:
        soup = BeautifulSoup(text, 'lxml')
    except Exception as e:
        raise ValueError(f"Failed to parse HTML string: {e}")

    image_divs = soup.find_all(name='script')
    for div in image_divs:
        txt = str(div)
        if 'AF_initDataCallback' not in txt:
            continue
        if 'ds:0' in txt or 'ds:1' not in txt:
            continue
        uris = re.findall(r'http[^\[]*?\.(?:jpg|png|bmp)', txt)
        return [{'file_url': uri} for uri in uris]


def find_new_trend(raw_text):
    """
    Extract name of trend from html code

    :param raw_text: html code
    :return: new_trend - name of trend, raw_text - html code after this trend
    """
    mark1 = raw_text.find('{"title":{"query":"')
    raw_text = raw_text[mark1 + 19:]
    mark2 = raw_text.find('","exploreLink"')
    new_trend = raw_text[:mark2]
    new_trend = new_trend.encode('utf-8').decode('unicode_escape')
    return new_trend, raw_text


async def trends():
    """
    Find current google trend in Russia, find relevant image for this trend,
    post trend with image in telegram channel
    """
    filename = 'gtrends.txt'
    url = 'https://trends.google.ru/trends/api/dailytrends?hl=en-US&tz=-180&geo=RU&ns=15'

    try:
        with open(filename, 'r', encoding='utf-8') as file:
            old_trend = file.read()
    except FileNotFoundError:
        old_trend = ''

    response = requests.get(url)
    raw_text = response.text

    new_trend, raw_text = find_new_trend(raw_text)
    if old_trend == new_trend:
        new_trend, raw_text = find_new_trend(raw_text)

    if old_trend != new_trend:
        with open('gtrends.txt', 'w', encoding='utf-8') as file:
            file.write(new_trend)
        files = glob.glob('postPhotos\\*')
        for f in files:
            os.remove(f)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/88.0.4324.104 Safari/537.36',
            'Accept-Encoding': 'gzip, deflate', 'Accept': '*/*', 'Connection': 'keep-alive',
            'Cookie': 'CONSENT=YES+RU.ru+201908; HSID=AsZXhAvAfbouN5-y4; SSID=AEgrdtG_jfqJD8dH2; APISID=Nn_suerp6Q1mJ5oo/AsK_c0rsbGt7qIGCW; SAPISID=R2oRL1i4teQ0rIqs/AQwMRIyyGbXl5bDhA; __Secure-1PAPISID=R2oRL1i4teQ0rIqs/AQwMRIyyGbXl5bDhA; __Secure-3PAPISID=R2oRL1i4teQ0rIqs/AQwMRIyyGbXl5bDhA; OTZ=7181849_44_48_123840_44_436320; SEARCH_SAMESITE=CgQIjZkB; SID=awgKSZ_CSj4O7HEybNaN9mzYMrFqLCyNbg_zTRJMgCDvr_qw3JPAaXkv---kCDY2PCfRqA.; __Secure-1PSID=awgKSZ_CSj4O7HEybNaN9mzYMrFqLCyNbg_zTRJMgCDvr_qwbBgGu0fybN9K76cfSZl2BA.; __Secure-3PSID=awgKSZ_CSj4O7HEybNaN9mzYMrFqLCyNbg_zTRJMgCDvr_qwTRfBk8--UCIERHO1Uuhb6A.; OGPC=19036484-1:; AEC=Ad49MVGsra4cSK5J-bSLAphFdqkp21domxoZnItypZdM6gv3dv1o8yEEjg==; NID=511=ORVb9Mx-xN9c7UyYbQ4ZfEpAM64U3TQsXpt6mEmugAaxoKGVGhwFC56po0m5J59yku6fyHGayu6pb-n5VnJjsD_QTmBy_56Vv7eIgqmRLhrW-4M_Tt2AFBHz_IC_zlWCkBVQydff11TZCWCz1o9NBmL2su4dsuVgHHT5SOQALyPO3zvlUTpVPLQUQVN_wAVWDelkNStH6_0_CwoY5mo6nW4vKbgA3Iu-XFZAjriU5YFOSMXTDNTftQRiwm92DVD2ja2TmTY1txhlXecG-_2U6rbToK4RW02GatRe6LokWTfRkHod67T4d-Z3IGocXmc5WNtflo4j2Bv8SqTVURkk7pRDBqlTdM1pH3sezVfNTIDeD6JrZ-FjoWxH0dtHcbkrVmIo5alJ_e974HAlguvQWejEmz8wmEsl-YB00whHn8HwDJYlh2gjDHvUGg; __Secure-1PSIDTS=sidts-CjIB3e41hYvc5K441RCo6l8KyQ--2Jy3bSBL4Fh8xKbqPGbMKpXOq46-OKuyyiF2XpAPChAA; __Secure-3PSIDTS=sidts-CjIB3e41hYvc5K441RCo6l8KyQ--2Jy3bSBL4Fh8xKbqPGbMKpXOq46-OKuyyiF2XpAPChAA; DV=I93DNX4UejJfUOdSY-cMjB_qTK2_q9i-g7kjb7seaQEAAEAIMU5ewDV2kAAAAGC9VCFbQNaLTwAAAI3rylNz9FMWFgAAAA; 1P_JAR=2023-09-22-08; SIDCC=APoG2W_dzdGv-RCo4HUdTk-ZK6rFwNvfvVTUKb4vbdYyxfVL9Os2ha1InmRxlxUOGm_EWm2aTw; __Secure-1PSIDCC=APoG2W9J3eIOwEpFR38x1awHVnPLjjMQWRF70nRwoUDWdS-ZYoj-p2-gAk3ieaEXZyYRYH-Qiw; __Secure-3PSIDCC=APoG2W-5ZvjOrs4anui_ZbOROuyOzQTUGjIJ00x_cezJ6EWjTLdUhmxFRHKHsd0WjCO2Fv1Crw'
                    }
        resp = requests.get(f'https://www.google.com/search?q={new_trend}&ijn=0&start=0&tbs=&tbm=isch',
                            headers=headers, allow_redirects=True, timeout=15)
        text = resp.text
        images = img_list(text)
        filename = ''
        for try_count in range(6):
            await asyncio.sleep(1)
            try:
                file1_url = images[try_count]['file_url']
                mark1 = file1_url.rfind('/')
                filename = file1_url[mark1 + 1:]
                wget.download(file1_url, out='postPhotos\\')
                break
            except Exception:
                pass
        message = f'Tоп-1 запрос в Google по России: {new_trend}'
        try:
            if not filename:
                path = 'gtrends.png'
            else:
                path = f'postPhotos\\{filename}'
            await send_to_telegram.send_to_channel(method='send_file', path=path, text=message)
        except Exception as e:
            print(f"Error posting trends: {e}")

logging.disable(logging.CRITICAL)
