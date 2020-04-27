import album_bot
import album_sender

def test(url):
	result = album_bot.getResult(url, '')
	if not result:
		return
	album_sender.send(album_bot.debug_group, url, result, rotate = 0)

if __name__ == "__main__":
	test('https://www.douban.com/people/ynyykx/status/2933752763')