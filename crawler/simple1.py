import urllib.request,urllib

date={'word':'zhang'}
url = "http://www.baidu.com/?"
date_url=urllib.parse.urlencode(date)
full_url=url+date_url
a = urllib.request.urlopen(full_url).read()
a = a.decode('UTF-8')
print(a)