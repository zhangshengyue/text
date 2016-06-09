import logging
import  asyncio, aiomysql
from models import User, Blog, Comment
@asyncio.coroutine
def create_pool(loop, **kw):
    #打印创建数据库连接日志信息：
    logging.info('create database connection pool...')
    #aiomysql.create_pool()创建连接到Mysql数据库池中的协程链接：
    yield from aiomysql.create_pool(
        host=kw.get('host', 'localhost'),           #数据库链接地址，默认localhost
        port=kw.get('port', 3306),                  #链接端口号，默认3306
        user=kw['user'],                            #登陆名
        password=kw['password'],                    #登陆密码
        
        db=kw['db'],
        #数据库名
        
        charset=kw.get('charset', 'utf8'),          #字符集设置，默认utf-8
        
        autocommit=kw.get('autocommit', True),      #自动提交模式，默认True
        maxsize=kw.get('maxsize', 10),              #最大连接数，默认10
        minsize=kw.get('minsize', 1),               #最小连接数，默认1
        loop=loop                                   #可选循环实例，[aiomysql默认为asyncio.get_event_loop()]
    )

def test():
    yield from create_pool(user='root', password='password',loop='loop',db='awesome')


for x in test():
    pass
loop = asyncio.get_event_loop()
loop.run_until_complete(test())
loop.close()