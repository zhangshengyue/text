import asyncio
import aiomysql
import orm

loop = asyncio.get_event_loop()

@asyncio.coroutine
def go():
    global _pool
    _pool =yield from orm.create_pool()

    with (yield from _pool) as conn:
        cur = yield from conn.cursor()
        yield from cur.execute("SELECT 10")
        # print(cur.description)
        (r,) = yield from cur.fetchone()
        print((r,))
    pool.close()
    yield from pool.wait_closed()

loop.run_until_complete(go())