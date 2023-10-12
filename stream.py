from typing import Generator, Any, Type
from queue import Queue
import threading
import asyncio

import protocols
from strategies import robust

class GeocodeStreamerQueue:
    '''
    Enables Geocoding to happen async but the results to be
    returned in a sync iterator as soon as they are available.
    '''
    DONE = object()  # sentinel to indicate geocoding finished.

    def __init__(self, rate_limit=2, Geocoder: Type[protocols.BulkAsyncGeocoder] = robust.Geocoder):
        self.Geocoder = Geocoder
        self.rate_limit = rate_limit
    
    async def _geocode_to_queue(self, addresses, in_order, result_queue):
        geocoder = self.Geocoder(rate_limit=self.rate_limit)
        async for result in geocoder.geocode_async_gen(addresses, in_order):
            result_queue.put(result)

    def _geocode_to_queue_in_async_loop(self, addresses, in_order, result_queue):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self._geocode_to_queue(addresses, in_order, result_queue))
        finally:
            result_queue.put(self.DONE)

    def geocode_gen(self, addresses: list, in_order=True) -> Generator[Any, None, None]:
        result_queue = Queue()
        thread = threading.Thread(target=self._geocode_to_queue_in_async_loop, args=(addresses, in_order, result_queue))
        thread.start()

        while True:
            next_result = result_queue.get(block=True)
            if next_result is self.DONE:
                break
            yield next_result


class GeocoderStreamerAsync:
    '''
    This approach uses an async generator to yield results as they are generated.
    I think it's harder to understand than the thread+queue approach,
    but it's interesting and less code.

    The drawback is that anything using the geocode_gen() method will block
    the async loop, so it won't progress if something else is happening.

    Hence, we're not using this approach.

    Originally, this was faster than the queue approach, but perf issues
    are resolved in queue approach and now they are more-or-less identical.
    '''

    def __init__(self, rate_limit=2, Geocoder: Type[protocols.BulkAsyncGeocoder] = robust.Geocoder):
        self.Geocoder = Geocoder
        self.rate_limit = rate_limit

    async def run_async_gen(self, addresses, in_order):
        async for result in self.Geocoder(rate_limit=self.rate_limit).geocode_async_gen(addresses, in_order):
            yield result

    def geocode_gen(self, addresses: list, in_order=True) -> Generator[Any, None, None]:
        gen = self.run_async_gen(addresses, in_order) 

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        while True:
            try:
                next_result = loop.run_until_complete(gen.__anext__())
                yield next_result
            except StopAsyncIteration:
                break
