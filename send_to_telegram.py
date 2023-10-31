import asyncio
import inspect
import logging

from telethon import TelegramClient


async def send_to_channel(method, path=None, text=None):
    """
    Sending message to telegram channel

    :param method: Method of sending. Choose one: send_message - sending only text but have huge letters limit (4096 symbols) or send_file - sending text with file (mostly image) but text limit is 200 symbols
    :param path: path to file location
    :param text: message to post
    """
    async with lock:
        print('send_to_channel')
        client_telegram = TelegramClient('session5', telegram_api_id, telegram_api_hash, system_version="4.16.30-vxCUSTOM")
        await client_telegram.start()
        client_telegram.parse_mode = 'html'
        if method == 'send_file':
            try:
                async with client_telegram:
                    call_from = inspect.currentframe().f_back.f_code.co_name
                    await client_telegram.send_file(channel_id, path, caption=text)
                    print(f'Message sent successfully and its function calling from {call_from}')
            except Exception as e:
                print(f'Error sending Message: {e}')
            finally:
                await client_telegram.disconnect()
        elif method == 'send_message':
            try:
                async with client_telegram:
                    await client_telegram.send_message(channel_id, text, link_preview=False)
                    call_from = inspect.currentframe().f_back.f_code.co_name
                    print(f'Message sent successfully and its function calling from {call_from}')
            except Exception as e:
                print(f'Error sending Message: {e}')
            finally:
                await client_telegram.disconnect()
        else:
            print('Error, method don`t recognised')

logging.basicConfig(level=logging.DEBUG)
logging.getLogger('telethon').setLevel(logging.CRITICAL)
telegram_api_id = settings.TELEGRAM_API_ID
telegram_api_hash = settings.TELEGRAM_API_HASH
channel_id = settings.TELEGRAM_CHANNEL_ID
lock = asyncio.Lock()
