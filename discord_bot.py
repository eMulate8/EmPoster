import logging
import os
import random

import discord
import requests
from PIL import Image

import send_to_telegram


async def send_discord_attachment_to_telegram(discord_token: str):
    """
    A Discord bot that reacts to a message with an image appearing in a Discord channel,
    saves this image in local storage, splits this image into 4 parts and sends
    one of these parts to the Telegram channel.

    :param discord_token: required token for discord bot
    """
    intents = discord.Intents.all()
    client_discord = discord.Client(intents=intents)
    directory = os.getcwd()

    def split_image(image_file):
        """
        Splits image into 4 parts by cross -
        in half vertically and horizontally

        :param image_file: path to image in local storage
        """
        with Image.open(image_file) as im:
            width, height = im.size

            mid_x = width // 2
            mid_y = height // 2

            top_left = im.crop((0, 0, mid_x, mid_y))
            top_right = im.crop((mid_x, 0, width, mid_y))
            bottom_left = im.crop((0, mid_y, mid_x, height))
            bottom_right = im.crop((mid_x, mid_y, width, height))

            return top_left, top_right, bottom_left, bottom_right

    async def download_image(url, filename):
        """
        Download image, split image on 4 parts, save whole image in input_folder
        and save one of these parts in output_folder

        :param url: url image to donwload
        :param filename: name under which the image is saved
        """
        response = requests.get(url)
        if response.status_code == 200:

            input_folder = "input"
            output_folder = "output"

            with open(f"{directory}/{input_folder}/{filename}", "wb") as f:
                f.write(response.content)
            print(f"Image downloaded: {filename}")

            input_file = os.path.join(input_folder, filename)

            if "UPSCALED_" not in filename:
                file_prefix = os.path.splitext(filename)[0]

                top_left, top_right, bottom_left, bottom_right = split_image(input_file)

                top_left.save(os.path.join(output_folder, file_prefix + "1.jpg"))
                top_right.save(os.path.join(output_folder, file_prefix + "2.jpg"))
                bottom_left.save(os.path.join(output_folder, file_prefix + "3.jpg"))
                bottom_right.save(os.path.join(output_folder, file_prefix + "4.jpg"))

            else:
                os.rename(f"{directory}/{input_folder}/{filename}", f"{directory}/{output_folder}/{filename}")

    @client_discord.event
    async def on_ready():
        """
        Actions after the bot is ready to work
        """
        print("Bot connected")

    @client_discord.event
    async def on_message(message):
        """
        Actions after the bot is detected message in channel
        if message not from bot and have image
        bot download image, split it and send one part of it to telegram channel
        """
        if message.author == client_discord.user:
            return
        for attachment in message.attachments:
            if attachment.filename.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".webp")):
                await download_image(attachment.url, f"{attachment.filename}")
                filename = random.choice(os.listdir('output\\'))
                await send_to_telegram.send_to_channel('send_file', path=f'output\\{filename}')
                files = os.listdir('output\\')
                for file in files:
                    os.remove(f'output\\{file}')

    await client_discord.start(discord_token)
    print("Bot connected to Discord")
    await client_discord.wait_until_ready()

logging.disable(logging.CRITICAL)
