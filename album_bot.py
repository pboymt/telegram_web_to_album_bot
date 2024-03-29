#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from telegram.ext import Updater, MessageHandler, Filters

import yaml
from telegram_util import log_on_fail, matchKey, getBasicLog, getOrigins, tryDelete
import web_2_album
import weibo_2_album
import twitter_2_album
import reddit_2_album
import album_sender
from bs4 import BeautifulSoup
import plain_db
import threading
import cached_url

with open('CREDENTIALS') as f:
	CREDENTIALS = yaml.load(f, Loader=yaml.FullLoader)
tele = Updater(CREDENTIALS['bot_token'], use_context=True)

debug_group = tele.bot.get_chat(420074357)
info_log = tele.bot.get_chat(-1001439828294)
waitlist_log = tele.bot.get_chat(-1001345995889)
remove_origin = plain_db.loadKeyOnlyDB('remove_origin')

def getUrlFromInfoLog(msg):
	if not matchKey(str(msg), ['-1001316672281', "'title': '[info_log]"]):
		return 
	soup = BeautifulSoup(msg.text_html_urled, 'html.parser')
	for item in soup.find_all('a'):
		if 'www.douban.com/group/topic' in item.get('href'):
			return 'https://' + item.get('href')
	for item in list(soup.find_all('a'))[::-1]:
		if 'http' in item.get('href'):
			return item.get('href')

def getUrl(msg):
	if getUrlFromInfoLog(msg):
		return getUrlFromInfoLog(msg)
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
	if '.reddit.' in url:
		ranks = [reddit_2_album] + ranks
	for method in ranks:
		try:
			if method == twitter_2_album:
				candidate = method.get(url, origin = origin)
				candidate.url = candidate.url.split('?')[0]
			elif method == web_2_album and 'douban.' in url:
				candidate = method.get(url, content = cached_url.get(url, 
					{'cookie': CREDENTIALS.get('douban_cookie')}, 
					force_cache=True))
				candidate.url = candidate.url.split('/#')[0]
				candidate.url = candidate.url.split('/?')[0]
			elif method == reddit_2_album:
				candidate = method.get(url)
				candidate.url = candidate.url.split('/?')[0]
			else:
				candidate = method.get(url)
		except:
			continue
		if not candidate.empty():
			return candidate

def getParam(text, key, func, default):
	for item in text.split():
		if item.startswith(key):
			try:
				return func(item[1:])
			except:
				...
	return default


@log_on_fail(debug_group)
def toAlbumInternal(update, context):
	if update.edited_message or update.edited_channel_post:
		return
	msg = update.effective_message
	url = getUrl(msg)
	if not url:
		return
	result = getResult(url, msg.text, getOrigins(msg))
	if not result:
		return
	if msg.text.endswith(' t'): # text only
		result.imgs = []
		result.video = ''
	rotate = getParam(msg.text, 'r', int, 0)
	size_factor = getParam(msg.text, 's', float, None)
	page = getParam(msg.text, 'p', int, 0)
	tmp_msg = None
	error = ''
	final_result = ''
	send_all = (msg.chat_id == -1001367414473)
	try:
		if str(msg.chat_id) in remove_origin._db.items:
			tryDelete(msg)
			waitlist_msg = waitlist_log.send_message(msg.text, disable_web_page_preview=True)
		else:
			tmp_msg = tele.bot.send_message(msg.chat_id, 'sending')
		final_result = album_sender.send_v2(msg.chat, result, rotate = rotate, send_all=send_all, size_factor=size_factor, start_page=page)[0]
		if final_result and str(msg.chat_id) in remove_origin._db.items:
			tryDelete(waitlist_msg)
	except Exception as e:
		error = ' error: ' + str(e)
	if final_result:
		final_result = final_result.text_html_urled or final_result.caption_html_urled
		if final_result:
			final_result = ' result: ' + final_result
	info_log.send_message(getBasicLog(msg) + error + final_result, 
		parse_mode='html', disable_web_page_preview=True)
	if tmp_msg:
		tryDelete(tmp_msg)

@log_on_fail(debug_group)
def toAlbum(update, context):
	threading.Thread(target=toAlbumInternal, args=(update, context)).start()

def toggleRemoveOrigin(msg):
	result = remove_origin.toggle(msg.chat_id)
	if result:
		msg.reply_text('Remove Original message On')
	else:
		msg.reply_text('Remove Original message Off')

@log_on_fail(debug_group)
def command(update, context):
	msg = update.message or update.channel_post
	if not msg:
		return
	if matchKey(msg.text, ['origin', 'trmo', 'toggle_remove_origin']):
		return toggleRemoveOrigin(msg)

if __name__ == "__main__":
	tele.dispatcher.add_handler(MessageHandler(Filters.text & Filters.entity('url'), toAlbum))
	tele.dispatcher.add_handler(MessageHandler(Filters.command, command))
	tele.start_polling()
	tele.idle()