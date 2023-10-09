
import asyncio
from contextlib import contextmanager
import threading
from queue import Queue
import time
from typing import Generator

from main import RobustGeocoder, batch_geocode_sync_gen

def current_approach(addresses: list, rate_limit: int=2):
    for result in batch_geocode_sync_gen(addresses, in_order=True):
        print(result)

def approach_1(addresses: list, rate_limit: int=2):
    '''
    This approach uses an async generator to yield results as they are generated.
    It's slightly harder to understand than the thread+queue approach,
    but it's slightly faster, and less code.
    '''
    def batch_geocode_sync(addresses: list, in_order=True) -> Generator:
        async def run_async_gen():
            async for result in RobustGeocoder(rate_limit=rate_limit).batch_geocode_generator(addresses, in_order=in_order):
                yield result

        gen = run_async_gen()  # create an instance of the async generator

        def step_through_async_gen():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            while True:
                try:
                    next_result = loop.run_until_complete(gen.__anext__())
                    yield next_result
                except StopAsyncIteration:
                    break

        return step_through_async_gen()

    # Using the synchronous generator
    for result in batch_geocode_sync(addresses, in_order=True):
        print(result)


def approach_2(addresses, rate_limit=2):
    '''
    This approach uses a thread and a queue to yield results as they are generated.
    It's slightly easier to understand than the async generator approach,
    but it's slightly slower, and more code.
    '''
    def batch_geocode_sync(addresses: list, in_order=True) -> Generator:
        q = Queue()

        async def run_async_gen():
            async for result in RobustGeocoder(rate_limit=rate_limit).batch_geocode_generator(addresses, in_order=in_order):
                q.put(result)

        def start_event_loop():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(run_async_gen())

        t = threading.Thread(target=start_event_loop)
        
        
        t.start()

        while True:
            # If the queue is empty but the thread is still alive, continue waiting
            if q.empty() and t.is_alive():
                continue

            if not q.empty():
                next_result = q.get()
                # print("Yielding result")  # print something each iteration of the generator
                yield next_result

            # Break if the queue is empty and the thread is no longer alive (i.e., the loop has finished)
            if q.empty() and not t.is_alive():
                break

    for result in batch_geocode_sync(addresses, in_order=True):
        print(result)


@contextmanager
def timeit(name=''):
    start = time.time()
    yield
    end = time.time() - start
    print(f'{name} took {end:.2f} seconds')


if __name__ == '__main__':
    bad_address = [
        ';arshjg[rio vav;lkjer ijve]',
        ' guh409g78h3p;q3209jsdh fuh 2;4h 9',
    ]

    from example_addresses import addresses
    addresses = bad_address + addresses
    addresses = addresses[:10]

    rate_limit = 2

    with timeit('Current approach'):
        current_approach(addresses, rate_limit)
    with timeit('Approach 1'):
        approach_1(addresses, rate_limit)
    with timeit('Approach 2'):
        approach_2(addresses, rate_limit)
