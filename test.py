import album_bot
import album_sender
import cached_url
import yaml


with open('CREDENTIALS') as f:
	CREDENTIALS = yaml.load(f, Loader=yaml.FullLoader)

def test(url):
	print({'cookie': CREDENTIALS.get('douban_cookie')})
	cached_url.get(url, 
					{'cookie': CREDENTIALS.get('douban_cookie')}, 
					force_cache=True)
	# result = album_bot.getResult(url, '', origin=[])
	# if not result:
	# 	return
	# print(result)
	# album_sender.send(album_bot.debug_group, url, result, rotate = 0)

if __name__ == "__main__":
	test('https://www.douban.com/group/topic/171906016')