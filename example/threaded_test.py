#!/usr/bin/env python3

import asyncio
import sys
import time

import aiohttp


async def request(url, params):
    buff_size = 1024
    start_time = time.perf_counter()
    size = 0
    session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=300))
    try:
        async with await session.request('GET', url, params=params) as rq:
            if rq.status != 200:
                raise RuntimeError('{}: {}'.format(rq.status, rq.reason))
            chunk = await rq.content.read(buff_size)
            while chunk:
                size += len(chunk)
                chunk = await rq.content.read(buff_size)
    except (aiohttp.client_exceptions.ClientConnectorError, RuntimeError, asyncio.TimeoutError) as e:
        print(e)
    finally:
        await session.close()
    return size, time.perf_counter() - start_time


def test(count):
    params = {
        'text': 'Внимание! Включён режим разработчика. Для возврата в обычный режим скажите \'выход\'',
        'voice': 'anna',
        'format': 'wav'
    }
    url = 'http://127.0.0.1:8080/say'
    time.sleep(0.1)
    w_time = time.perf_counter()

    loop = asyncio.get_event_loop()
    tasks = [request(url, params) for _ in range(count)]
    workers = loop.run_until_complete(asyncio.gather(*tasks))

    w_time = time.perf_counter() - w_time
    avg_time = w_time / count

    size = workers[0][0]
    for test_size in workers:
        assert size == test_size[0]
        assert test_size[0]

    real_w_time = sum([x[1] for x in workers])
    real_avg_time = real_w_time / count
    return count, w_time, avg_time, real_w_time, real_avg_time, size


def print_result(count, w_time, avg_time, real_w_time, real_avg_time, size, one):
    boost = one / avg_time
    print('Threads: {}'.format(count))
    print('In thread work time: {:.4f}, avg: {:.4f}'.format(real_w_time, real_avg_time))
    print('Work time: {:.4f}, avg: {:.4f}'.format(w_time, avg_time))
    print('Single thread time: {:.4f}'.format(one))
    print('Boost: x {:.4f}'.format(boost))
    print('Data size: {}'.format(size))


if __name__ == '__main__':
    threads = 6
    if len(sys.argv) > 1:
        threads = int(sys.argv[1])
    test(threads)  # Прогрев
    single = test(1)  # Время одного потока
    oll = test(threads)
    print_result(*oll, single[1])
