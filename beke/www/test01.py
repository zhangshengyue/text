import logging
import  asyncio, aiomysql
import text
loop = asyncio.get_event_loop()
@asyncio.coroutine
def test():
    global __pool
    yield from text.create_pool()
    with (yield from __pool) as conn:
        cur = yield from conn.cursor()
        yield from cur.execute("SELECT 10")
        # print(cur.description)
        (r,) = yield from cur.fetchone()
        print((r,))
    pool.close()
    yield from pool.wait_closed()
loop.run_until_complete(test())
loop.close()    