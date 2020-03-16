#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from telegram.ext import Updater, MessageHandler, Filters

import yaml
from telegram_util import log_on_fail
from telegram import InputMediaPhoto
import os
import web_2_album
from PIL import Image
import weibo_2_album

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

def getImageAndCap(url, msg):
	if 'force_web' in msg.text:
		return web_2_album.get(url)
	if 'force_weibo' in msg.text:
		return weibo_2_album.get(url)

	for method in [web_2_album, weibo_2_album]:
		try:
			imgs, cap = method.get(url)	
			if images:
				return images, cap
		except Exception as e:
			print(e)
	return [], ''

@log_on_fail(debug_group)
def toAlbum(update, context):
	msg = update.effective_message
	url = getUrl(msg)
	imgs, cap = getImageAndCap(url, msg)
	print(imgs, cap)

	if not imgs:
		if msg.chat_id > 0:
			msg.reply_text('can not find images in your url')
		return

	if 'bot_rotate' in msg.text:
		for index, img_path in enumerate(imgs):
		    img = Image.open(img_path)
		    img = img.rotate(180)
		    img.save(img_path)
		    img.save('tmp_image/%s.jpg' % index)
		    
	group = [InputMediaPhoto(open(imgs[0], 'rb'), caption=cap, parse_mode='Markdown')] + \
		[InputMediaPhoto(open(x, 'rb')) for x in imgs[1:]]
	tele.bot.send_media_group(msg.chat_id, group, timeout = 20*60)

tele.dispatcher.add_handler(MessageHandler(Filters.text & Filters.entity('url'), toAlbum))

tele.start_polling()
tele.idle()