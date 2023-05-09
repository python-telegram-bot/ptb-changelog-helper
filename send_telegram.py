#!/usr/bin/env python

from configparser import ConfigParser

from telegram import Bot, ParseMode

config = ConfigParser()
config.read("config.ini")
token = config["Telegram"]["token"]
chat_id = config["Telegram"]["chat_id"]

bot = Bot(token)
with open("channel.html", encoding="utf-8") as file:
    text = file.read().rstrip()
    bot.send_message(
        chat_id=chat_id, text=text, parse_mode=ParseMode.HTML, disable_web_page_preview=True
    )
