import os
import random
import asyncio
import time

import twitter_data
import news
import discord_bot
import midjorney
import trends
import price_model


def count_seconds_to_hour(target_hour):
    """
    The function counts the seconds from the current moment to the specified hour within 24 hours.

    :param target_hour: the hour to which you need to count the seconds
    :return: Number of seconds
    """
    current_time = time.time()
    current_hour = time.localtime(current_time).tm_hour
    current_minute = time.localtime(current_time).tm_min
    current_second = time.localtime(current_time).tm_sec
    min_sec = current_minute * 60 + current_second
    if current_hour < target_hour:
        seconds_to_target = (target_hour - current_hour) * 3600 - min_sec
    else:
        seconds_to_target = (24 - current_hour + target_hour) * 3600 - min_sec

    return seconds_to_target


discord_token = '' # YOUR DISCORD TOKEN HERE


async def run_task(task, first_hour, second_hour=None, timeout=1200):
    """
    Function for running tasks at certain times of the day or after a certain time interval
    If parameter first_hour less than 24 - it is hours, if more than 24 - it is seconds

    :param task: Function to be run
    :param first_hour: The hour at which run should occur, checked by the time on the device; or interval in seconds
    :param second_hour: An hour to second run in one day, if not required leave equal to None
    :param timeout: The number of seconds to complete a task; if the task is not completed within this time, it is  restarted

    """
    while True:
        if first_hour > 24:
            first_interval = first_hour
        else:
            first_interval = count_seconds_to_hour(first_hour)
        if second_hour:
            second_interval = count_seconds_to_hour(second_hour)
            interval = second_interval if first_interval > second_interval else first_interval
        else:
            interval = first_interval
        await asyncio.sleep(interval)
        try:
            await asyncio.wait_for(task(), timeout=timeout)
        except asyncio.TimeoutError:
            print(f"{task.__name__} timed out and will be restarted")


async def main():
    """
    The function collects tasks to be executed and passes them to the event loop.
    random_three_to_four: random count of seconds which equal time between 3 and 4 hours
    task from discord_bot.py passes separately from others because it`s never ends and no need to restart
    """
    every_ten_minutes = 600
    random_three_to_four = random.randint(10800, 14400)
    asyncio.create_task(discord_bot.send_discord_attachment_to_telegram(discord_token))
    await asyncio.gather(run_task(price_model.nn_bot, 8), run_task(news.news, every_ten_minutes),
                         run_task(trends.trends, 9, 18),
                         run_task(twitter_data.twitter, every_ten_minutes),
                         run_task(midjorney.midjorney, random_three_to_four))


if not os.path.exists("output"):
    os.makedirs("output")

if not os.path.exists("input"):
    os.makedirs("input")

asyncio.run(main())
