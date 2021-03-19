#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from telegram.ext import Updater, MessageHandler, Filters

import yaml
from telegram_util import log_on_fail, matchKey
import web_2_album
import weibo_2_album
import twitter_2_album
import post_2_album
import album_sender
from datetime import datetime
from bs4 import beautifulSoup

with open('CREDENTIALS') as f:
	CREDENTIALS = yaml.load(f, Loader=yaml.FullLoader)
tele = Updater(CREDENTIALS['bot_token'], use_context=True)

debug_group = tele.bot.get_chat(420074357)

def getUrl(msg):
	if matchKey(msg.caption_html_urled, ['source</a>']):
		return
			and msg.chat.username == 'web_record'):
		return
	if (matchKey(msg.caption_html_urled, ['mp.weixin.qq.com', 
			'telegra.ph', 'source</a>']) 
			and msg.chat.username == 'web_record'):
		return

def getResult(url, text):
	# TODO: optimization based on url
	if 'force_web' in text:
		return web_2_album.get(url)
	if 'force_weibo' in text:
		return weibo_2_album.get(url)

	ranks = [web_2_album]
	if 'weibo' in url:
		ranks = [weibo_2_album] + ranks
	if matchKey(url, ['twitter', 't.co']):
		ranks = [twitter_2_album] + ranks
	if 't.me/' in url:
		ranks = [post_2_album] + ranks
	for method in ranks:
		try:
			candidate = method.get(url)
		except:
			continue
		if not candidate.empty():
			return candidate

@log_on_fail(debug_group)
def toAlbum(update, context):
	if update.edited_message or update.edited_channel_post:
		return
	msg = update.effective_message
	if (matchKey(msg.caption_html_urled, ['mp.weixin.qq.com', 
			'telegra.ph', 'source</a>']) 
			and msg.chat.username == 'web_record'):
		return
	url = getUrl(msg)
	result = getResult(url, msg.text)
	if not result:
		return
	rotate = 0
	for x in msg.text.split():
		if 'bot_rotate' in x:
			try:
				rotate = int(x.split('_')[-1])
			except:
				rotate = 180
	r = None
	try:
		r = tele.bot.send_message(msg.chat_id, 'sending')
		album_sender.send_v2(msg.chat, result, rotate = rotate)
	except Exception as e:
		debug_group.send_message('%s failed with exception: %s' % (url, str(e)))
	if r:
		r.delete()

if __name__ == "__main__":
	tele.dispatcher.add_handler(MessageHandler(Filters.text & Filters.entity('url'), toAlbum))
	tele.start_polling()
	tele.idle()