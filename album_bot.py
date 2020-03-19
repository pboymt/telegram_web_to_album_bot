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
import twitter_2_album

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
	# TODO: optimization based on url
	if 'force_web' in msg.text:
		return web_2_album.get(url, ok_no_image=True)
	if 'force_weibo' in msg.text:
		return weibo_2_album.get(url)

	candidate = [], ''
	for method in [web_2_album, weibo_2_album, twitter_2_album]:
		try:
			new_candidate = method.get(url)
		except:
			continue
		candidate = web_2_album.compare(candidate, new_candidate)
		if candidate[0]:
			return candidate
	return candidate

@log_on_fail(debug_group)
def toAlbum(update, context):
	msg = update.effective_message
	url = getUrl(msg)
	imgs, cap = getImageAndCap(url, msg)

	if 'bot_rotate' in msg.text:
		for index, img_path in enumerate(imgs):
			img = Image.open(img_path)
			img = img.rotate(180)
			img.save(img_path)
			img.save('tmp_image/%s.jpg' % index)
	
	if imgs:			
		group = [InputMediaPhoto(open(imgs[0], 'rb'), caption=cap, parse_mode='Markdown')] + \
			[InputMediaPhoto(open(x, 'rb')) for x in imgs[1:]]
		tele.bot.send_media_group(msg.chat_id, group, timeout = 20*60)
	elif cap:
		tele.bot.send_message(msg.chat_id, cap, parse_mode='Markdown')

def test(update, context):
	print(update.message.text_markdown)

tele.dispatcher.add_handler(MessageHandler(Filters.text & Filters.entity('url'), toAlbum))
tele.dispatcher.add_handler(MessageHandler(Filters.private, test))

tele.start_polling()
tele.idle()