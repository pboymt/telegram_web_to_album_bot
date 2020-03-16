#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from telegram.ext import Updater, MessageHandler, Filters

import yaml
from telegram_util import log_on_fail
from telegram import InputMediaPhoto
import os
import web_2_album

with open('CREDENTIALS') as f:
    CREDENTIALS = yaml.load(f, Loader=yaml.FullLoader)
tele = Updater(CREDENTIALS['bot_token'], use_context=True)

debug_group = tele.bot.get_chat(-1001198682178)

def getUrl(msg):
	for item in msg.entities:
		if (item["type"] == "url"):
			url = msg.text[item["offset"]:][:item["length"]]
			if not '://' in url:
				url = "https://" + url
			return url

@log_on_fail(debug_group)
def toAlbum(update, context):
	msg = update.message
	url = getUrl(msg)
	imgs, cap = web_2_album.get(url)
	group = [InputMediaPhoto(open(imgs[0], 'rb'), caption=cap, parse_mode='Markdown')] + \
		[InputMediaPhoto(open(x, 'rb')) for x in imgs[1:]]
	msg.reply_media_group(group, timeout = 20*60)

tele.dispatcher.add_handler(MessageHandler(Filters.text & Filters.entity(URL), toAlbum))

tele.start_polling()
tele.idle()