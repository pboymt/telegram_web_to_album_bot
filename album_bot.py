#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from telegram.ext import Updater, MessageHandler, Filters

import yaml
from telegram_util import log_on_fail, matchKey, getBasicLog, getOrigins, tryDelete
import web_2_album
import weibo_2_album
import twitter_2_album
import album_sender
from bs4 import BeautifulSoup
import plain_db

with open('CREDENTIALS') as f:
	CREDENTIALS = yaml.load(f, Loader=yaml.FullLoader)
tele = Updater(CREDENTIALS['bot_token'], use_context=True)

debug_group = tele.bot.get_chat(420074357)
info_log = tele.bot.get_chat(-1001198682178)
remove_origin = plain_db.loadKeyOnlyDB('remove_origin')

def getUrl(msg):
	if matchKey(msg.text_html_urled, ['source</a>']):
		return
	if (matchKey(msg.text_html_urled, 
			['mp.weixin.qq.com', 'telegra.ph']) 
			and msg.chat.username == 'web_record'):
		return
	soup = BeautifulSoup(msg.text_html_urled, 'html.parser')
	for item in soup.find_all('a'):
		if 'http' in item.get('href'):
			return item.get('href')

def getResult(url, text, origin):
	ranks = [web_2_album]
	if 'weibo.' in url:
		ranks = [weibo_2_album] + ranks
	if matchKey(url, ['twitter.', 't.co']):
		ranks = [twitter_2_album] + ranks
	for method in ranks:
		try:
			if method == twitter_2_album:
				candidate = method.get(url, origin = origin)
			else:
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
	url = getUrl(msg)
	if not url:
		return
	result = getResult(url, msg.text, getOrigins(msg))
	if not result:
		return
	rotate = 0
	if msg.text.split()[-1].startswith('r'):
		try:
			rotate = int(msg.text.split()[-1][1:])
		except:
			...
	tmp_msg = None
	error = ''
	final_result = ''
	try:
		tmp_msg = tele.bot.send_message(msg.chat_id, 'sending')
		final_result = album_sender.send_v2(msg.chat, result, rotate = rotate)[0]
		if final_result and str(msg.chat_id) in remove_origin._db.items:
			tryDelete(msg)
	except Exception as e:
		error = ' error: ' + str(e)
	if final_result:
		final_result = final_result.text_html_urled or final_result.caption_html_urled
		if final_result:
			final_result = ' result: ' + final_result
	info_log.send_message(getBasicLog(msg) + error + final_result, 
		parse_mode='html', disable_web_page_preview=True)
	if tmp_msg:
		try:
			tmp_msg.delete()
		except:
			...

def toggleRemoveOrigin(msg):
	result = remove_origin.toggle(msg.chat_id)
	if result:
		msg.reply_text('Remove Original message On')
	else:
		msg.reply_text('Remove Original message Off')

@log_on_fail(debug_group)
def command(update, context):
	msg = update.message or update.channel_post
	if matchKey(msg.text, ['origin', 'trmo', 'toggle_remove_origin']):
		return toggleRemoveOrigin(msg)

if __name__ == "__main__":
	tele.dispatcher.add_handler(MessageHandler(Filters.text & Filters.entity('url'), toAlbum))
	tele.dispatcher.add_handler(MessageHandler(Filters.command, command))
	tele.start_polling()
	tele.idle()