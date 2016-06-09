import gzip
import re
import http.cookiejar
import urllib.request
import urllib.parse
 
def ungzip(data):
    try:        # 尝试解压
        print('正在解压.....')
        data = gzip.decompress(data)
        print('解压完毕!')
    except:
        print('未经压缩, 无需解压')
    return data
 
def getXSRF(data):
    cer = re.compile('name=\"_xsrf\" value=\"(.*)\"', flags = 0)
    strlist = cer.findall(data)
    return strlist[0]
 
def getOpener(head):
    # deal with the Cookies
    cj = http.cookiejar.CookieJar()
    pro = urllib.request.HTTPCookieProcessor(cj)
    opener = urllib.request.build_opener(pro)
    header = []
    for key, value in head.items():
        elem = (key, value)
        header.append(elem)
    opener.addheaders = header
    return opener
 
header = {
    'Connection': 'Keep-Alive',    
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.8',
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.110 Safari/537.36',
    'Accept-Encoding': 'gzip, deflate',
    'Host': '222.194.15.1:7777',
    'DNT': '1',
    'Origin': 'http://222.194.15.1:7777'


''' Host: 222.194.15.1:7777
Connection: keep-alive
Content-Length: 24
Cache-Control: max-age=0
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8
Origin: http://222.194.15.1:7777
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.110 Safari/537.36
Content-Type: application/x-www-form-urlencoded
Referer: http://222.194.15.1:7777/zhxt_bks/xk_login.html
Accept-Encoding: gzip, deflate
Accept-Language: zh-CN,zh;q=0.8'''

}

 
url = 'http://222.194.15.1:7777/'
opener = getOpener(header)
op = opener.open(url)
data = op.read()
data = ungzip(data)     # 解压
_xsrf = getXSRF(data.decode())
 
url += 'login'
id = '130210307'
password = '4321'
postDict = {
        '_xsrf':_xsrf,
        'email': id,
        'password': password,
        'rememberme': 'y'
}
postData = urllib.parse.urlencode(postDict).encode()
op = opener.open(url, postData)
data = op.read()
data = ungzip(data)
 
print(data.decode())