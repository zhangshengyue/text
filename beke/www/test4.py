import asyncio, logging

from orm import create_pool
from models import User

db_config = {
    'port':3307,
    'user': 'root',
    'password': 'root',
    'db': 'awesome'
}

async def test():
    await create_pool(loop, **db_config)

    # 测试count rows语句
    # rows = await User.countRows(), 这句是我改写了老师的findNumber方法，用‘*’比‘id'更高效
    rows = await User.findNumber('*')
    logging.info('rows is: %s' % rows)

    # 测试insert into语句
    if rows < 2:
        for idx in range(5):
            u = User(name='test%s'%(idx), email='test%s@orm.org'%(idx),
                        password='pw', image='/static/img/user.png')
            # rows = await User.countRows('email = ?', u.email)
            rows = await User.findNumber('*', 'email = ?', u.email)
            if rows == 0:
                # await u.register(),这句是我改写了，先加密再调用save方法
                await u.save()
            else:
                print('the email was already registered...')

    # 测试select语句
    users = await User.findAll(orderBy='created_at')
    for user in users:
        logging.info('name: %s, email: %s' % (user.name, user.email))

    # 测试update语句
    user = users[1]
    user.email = 'guest@orm.com'
    user.name = 'guest'
    await user.update()

    # 测试查找指定用户
    test_user = await User.find(user.id)
    logging.info('name: %s, email: %s' % (user.name, user.email))

    # 测试delete语句
    users = await User.findAll(orderBy='created_at', limit=(1, 2))
    for user in users:
        logging.info('delete user: %s' % (user.name))
        await user.remove()

loop = asyncio.get_event_loop()
loop.run_until_complete(test())
loop.close()