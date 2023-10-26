import re
import logging

import wget
from twitter.account import Account

import sel_deepl
import send_to_telegram


def tweets_data():
    """
    Connect to personal Twitter account and collect twits from timeline.
    Twits are selected according to conditions in code and translated to russian.

    :return: list of dictionary with following structure:
        {'author': 'link to twit author',
        'link': 'link to twit'
        'original_text': 'twit`s text',
        'translated_text': 'twit`s text translated to russian',
        'media_paths': path to twit`s images in local dir}
    """
    twitter_cookies = {} #your twitter cookies

    tweets_dict = {}

    try:
        account = Account(cookies=twitter_cookies)
        latest_timeline = account.home_latest_timeline(limit=1)
        tweets = latest_timeline[0]['data']['home']['home_timeline_urt']['instructions'][0]['entries']
    except Exception:
        return tweets_dict

    with open('seen_tweets.txt', 'r', encoding='utf-8') as fid:
        seen_tweets_ids = fid.read().split("\n")

    for i, tweet in enumerate(tweets):
        entry_id = find_all_key_values('entryId', tweet)[0]
        tweet_id = entry_id[entry_id.rfind('-') + 1:]

        if all((is_list_empty(find_all_key_values('user_mentions', tweet)),
                is_list_empty(find_all_key_values('quoted_status_result', tweet)),
                entry_id.find('promoted') == -1, entry_id.find('cursor') == -1,
                entry_id.find('conversation') == -1, tweet_id not in seen_tweets_ids,
                entry_id.find('follow') == -1)):

            seen_tweets_ids.append(tweet_id)
            full_text = '\n'.join(find_all_key_values('full_text', tweet))
            full_text = re.sub(r'\.(jpg|png)|https?://\S+', '', full_text)
            extended_entities = find_all_key_values('extended_entities', tweet)
            entities = find_all_key_values('entities', tweet)
            entities_list = []
            media_url = []

            if not is_list_empty(extended_entities):
                entities_list = extended_entities
            elif not is_list_empty(entities):
                entities_list = entities

            if not is_list_empty(entities_list):
                for entity in extended_entities:
                    media_url_https = find_all_key_values('media_url_https', entity)
                    media_url.extend([media for media in media_url_https if not is_list_empty(media_url_https)])

            media_paths = []

            for media in media_url:
                wget.download(media, out='photos\\')
                media_paths.append(f'photos\\{media[media.rfind("/") + 1:]}')

            try:
                author_name = find_all_key_values('screen_name', tweet)[0]
            except Exception:
                continue

            try:
                translated_text = sel_deepl.translate(full_text) if full_text else ''
            except Exception:
                continue

            tweets_dict[tweet_id] = {'author': f'<a href="https://twitter.com/{author_name}">{author_name}</a>\n',
                                     'link': f'<a href="https://twitter.com/{author_name}/status/{tweet_id}">Твит</a>\n\n',
                                     'original_text': f'{full_text}\n\n',
                                     'translated_text': f'{translated_text}',
                                     'media_paths': media_paths}

    with open('seen_tweets.txt', 'w', encoding='utf-8') as fid:
        for item in seen_tweets_ids:
            if item != '':
                fid.write(f'{item}\n')

    return tweets_dict


def find_all_key_values(key, data):
    """
    Search values in dictionary and nested dictionary with certain key

    :param key: search key
    :param data: dictionary in which the search is carried out
    :return: list of found values
    """
    results = []
    if isinstance(data, dict):
        for k, v in data.items():
            if k == key:
                results.append(v)
            elif isinstance(v, (dict, list)):
                results.extend(find_all_key_values(key, v))
    elif isinstance(data, list):
        for item in data:
            results.extend(find_all_key_values(key, item))
    return results


def is_list_empty(list_):
    """
    Checks list and nested lists is empty

    :param list_: checked list
    """
    if not list_:
        return True
    for item in list_:
        if isinstance(item, list):
            if not is_list_empty(item):
                return False
        elif item is not None:
            return False
    return True


async def twitter():
    """
    From each element of the list obtained as a result of the function tweets_data(),
    creates a text message and sends it to the telegram channel
    """
    print('twitter')
    tweet_dict = tweets_data()
    print(f'twits - {len(tweet_dict)}')
    if tweet_dict:
        for tweet in tweet_dict:
            post_text = ''.join((tweet_dict[tweet]['author'], tweet_dict[tweet]['link'],
                                 tweet_dict[tweet]['original_text'], tweet_dict[tweet]['translated_text']))
            if tweet_dict[tweet]['media_paths']:
                tweet_text = post_text if tweet_dict[tweet]['original_text'] and not tweet_dict[tweet][
                    'original_text'].isspace() else '🤔'
                await send_to_telegram.send_to_channel(method='send_file',
                                                       path=tweet_dict[tweet]['media_paths'],
                                                       text=tweet_text)
            elif all((tweet_dict[tweet]['original_text'], not tweet_dict[tweet]['original_text'].isspace())):
                await send_to_telegram.send_to_channel(method='send_message', text=post_text)

logging.basicConfig(level=logging.DEBUG)
logging.getLogger('telethon').setLevel(logging.CRITICAL)
