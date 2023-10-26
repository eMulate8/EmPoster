import logging
from builtins import ConnectionError as ConnErr

import requests
from bs4 import BeautifulSoup
from requests.exceptions import ConnectionError, ReadTimeout

import sel_deepl
import send_to_telegram


def grab_news():
    """
    Collects data on the latest news from three websites: coindesk.com,
    cointelegraph.com, bitcoinmagazine.com

    :return: dictionary with link to news as key and news title as value
    """
    print('coindesk')
    article_dict = {}
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/106.0.0.0 Safari/537.36'}
    try:
        response = requests.get(url='https://www.coindesk.com/', proxies={'http': '', 'https': ''},
                                headers=headers, timeout=600)
        ok = response.status_code
    except ConnectionError:
        ok = 0
        response = requests.Response()
    except ReadTimeout:
        response = requests.Response()
        ok = 0

    if ok == 200:
        with open('coindesk.txt', 'w', encoding='utf-8') as file:
            file.write(response.text)

        with open('links_cd.txt', 'r', encoding='utf-8') as file:
            links = file.read().split("\n")

        soup = BeautifulSoup(response.text, 'html.parser')
        for link in soup.find_all('a'):
            href = link.get('href')
            title = link.get('title')
            if title is not None and href not in links and not title.isspace():
                links.append(href)
                try:
                    title = sel_deepl.translate(title.strip())
                except Exception:
                    continue
                href = f'<a href="https://coindesk.com{href}">Источник</a>\n\n'
                article_dict[href] = f'{title}\n'

        with open('links_cd.txt', 'w', encoding='utf-8') as file:
            for item in links:
                if item:
                    file.write(str(item) + '\n')

    print('cointelegraph')

    try:
        response = requests.get('https://cointelegraph.com/', headers=headers, timeout=600)
        ok = response.status_code
    except ConnectionError:
        response = requests.Response()
        ok = 0
    except ReadTimeout:
        response = requests.Response()
        ok = 0

    if ok == 200:
        with open('cointelegraph.txt', 'w', encoding='utf-8') as file:
            file.write(response.text)

        with open('links_ct.txt', 'r', encoding='utf-8') as file:
            links = file.read().split("\n")

        soup = BeautifulSoup(response.text, 'html.parser')

        for link in soup.find_all('a'):
            href = link.get('href')
            title = link.get('title')
            if title is not None and href.startswith('/news') and href not in links and not title.isspace():
                links.append(href)
                href = f'<a href="https://cointelegraph.com{href}">Источник</a>\n\n'
                try:
                    title = sel_deepl.translate(title.strip())
                except Exception:
                    continue
                article_dict[href] = f'{title}\n'

        with open('links_ct.txt', 'w', encoding='utf-8') as file:
            for item in links:
                if item:
                    file.write(str(item) + '\n')

    print('bitmag')

    bitcoin_magazine_headers = {'sec-ch-ua': '"Chromium";v="110", "Not A(Brand";v="24", "Google Chrome";v="110"',
                                'sec-ch-ua-mobile': '?0',
                                'sec-ch-ua-platform': '"Windows"',
                                'Upgrade-Insecure-Requests': '1',
                                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, '
                                              'like Gecko) Chrome/110.0.0.0 Safari/537.36',
                                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,'
                                          'image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                                'Sec-Fetch-Site': 'none',
                                'Sec-Fetch-Mode': 'navigate',
                                'Sec-Fetch-User': '?1',
                                'Sec-Fetch-Dest': 'document',
                                'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7'
                                }
    try:
        response = requests.get('https://bitcoinmagazine.com/articles', headers=bitcoin_magazine_headers, timeout=600)
        ok = response.status_code
    except ConnectionError:
        response = requests.Response()
        ok = 0
    except ReadTimeout:
        response = requests.Response()
        ok = 0

    if ok == 200:
        with open('bitcoinmagazine.txt', 'w', encoding='utf-8') as file:
            file.write(response.text)

        with open('links_bm.txt', 'r', encoding='utf-8') as file:
            links = file.read().split("\n")

        valid_link_starts = ['/culture', '/business', '/technical', '/industry-events', '/markets', '/legal',
                             '/guides']
        soup = BeautifulSoup(response.text, 'html.parser')
        elements = soup.select('div[class="m-card--content"]')

        href = title = sub_title = None
        for element in elements:
            phoenix_ellipsis = element.find_all('phoenix-ellipsis')
            for phoenix_ellipse in phoenix_ellipsis:
                a = phoenix_ellipse.find('a')
                if a:
                    href = a.get('href')
                    title = phoenix_ellipse.get_text().strip()
                else:
                    sub_title = phoenix_ellipse.get_text().strip()

            if all((href, title, href not in links)):
                for prefix in valid_link_starts:
                    if href.startswith(prefix):
                        links.append(href)
                        href = f'<a href="https://bitcoinmagazine.com{href}">Источник</a>\n\n'
                        main_title = sel_deepl.translate(title)
                        secondary_title = sel_deepl.translate(sub_title)
                        if main_title:
                            try:
                                article_dict[href] = f'<b>{main_title}</b>\n<i>{secondary_title}</i>\n' \
                                    if sub_title else f'{main_title}\n'
                            except Exception:
                                continue
            href = title = sub_title = None

        with open('links_bm.txt', 'w', encoding='utf-8') as file:
            for item in links:
                if item:
                    file.write(str(item) + '\n')

    return article_dict


async def news():
    """
    Combine latest news in one text message and send it to telegram channel
    """
    article_dict = grab_news()
    text = ''.join(f'{value}{key}' for key, value in article_dict.items())
    if all((text, not text.isspace())):
        if len(text) >= 4096:
            t_text = text[:4096]
            m1 = t_text.rfind('Источник')
            text = text[:m1 + 14]
        try:
            await send_to_telegram.send_to_channel(method='send_message', text=text)
        except ConnErr:
            pass

logging.disable(logging.CRITICAL)