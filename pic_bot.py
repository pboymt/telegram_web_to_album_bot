#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from telegram.ext import Updater, MessageHandler, Filters

import pic_cut
import yaml
from telegram_util import log_on_fail
from telegram import InputMediaPhoto
import os

with open('CREDENTIALS') as f:
    CREDENTIALS = yaml.load(f, Loader=yaml.FullLoader)
tele = Updater(CREDENTIALS['bot_token'], use_context=True)

debug_group = tele.bot.get_chat(-1001198682178)

@log_on_fail(debug_group)
def cut(update, context):
	msg = update.effective_message
	if msg.chat_id == debug_group.id:
		return
		
	cap = msg.caption_markdown or msg.text_markdown or ''
	if msg.document:
		file = msg.document
	if msg.photo:
		file = msg.photo[-1]
		cap = msg.caption_markdown
	
	file = file.get_file().download()
	cuts = list(pic_cut.cut(file))
	os.system('rm %s' % file)

	if not cuts:
		return

	group = [InputMediaPhoto(open(cuts[0], 'rb'), caption=cap, parse_mode='Markdown')] + \
		[InputMediaPhoto(open(c, 'rb')) for c in cuts[1:]]
	for c in cuts:
		os.system('rm %s' % c)		
	tele.bot.send_media_group(msg.chat_id, group, timeout = 20*60)

tele.dispatcher.add_handler(MessageHandler(Filters.document | Filters.photo, cut))

tele.start_polling()
tele.idle()