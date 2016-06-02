import orm
from models import User, Blog, Comment
import asyncio
loop = asyncio.get_event_loop()
@asyncio.coroutine
def test(loop):
    yield from orm.create_pool(user='root', password='root', db='awesome',loop=loop)

    u = User(name='Test', email='test@example.com', passwd='1234567890', image='about:blank')

    yield from u.save()

for x in test(loop):
    pass
loop.run_until_complete(test(loop))
loop.close()
if loop.is_closed():
    sys.exit(0)
#这个问题是原因是你的aiomysql 可能封装了PyMySql，然后pYMYSQL 升级了一下，现在最新版本是0.7.0，这个版本可能和yield from 有的问题。。。。
#如果你用的是pycharm的话，可以卸载pymysql和aiomysql，
#再安装aiomysql。。。。，会自动安装0.6.7的pymysql，也就是正确版本