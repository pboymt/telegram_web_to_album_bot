import album_bot
import album_sender

def test(url):
	result = album_bot.getResult(url, '', origin=[])
	if not result:
		return
	print(result)
	album_sender.send(album_bot.debug_group, url, result, rotate = 0)

if __name__ == "__main__":
	test('https://m.weibo.cn/status/KsH85ia8h')