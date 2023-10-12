import asyncio
import logging
from typing import Generator
from dotenv import load_dotenv

from strategies import abstract, google, esri


from common import GeocodedLocation, GeocoderError

load_dotenv()

logger = logging.getLogger(__name__)

class SETTINGS:
    simultaneous_requests = 2

class Geocoder(abstract.Geocoder):
    '''
    A geocoder that uses multiple geocoders to geocode addresses.
    If the first geocoder fails, it tries the next one.
    '''
    def __init__(self, rate_limit: int = 2):
        self.google = google.Geocoder(rate_limit=rate_limit)
        self.esri = esri.Geocoder(rate_limit=rate_limit)
        super().__init__(rate_limit=rate_limit)

    async def _prepare_request(self, address: str): pass
    async def _response_to_location(self, address: str, response):  pass

    async def geocode_with_client(self, address: str, client) -> GeocodedLocation:
        try:
            loc = await self.google.geocode_with_client(address, client)
            return loc
        except GeocoderError:
            pass
        
        try:
            return await self.esri.geocode_with_client(address, client)
        except GeocoderError:
            pass

        return GeocodedLocation.null_island(address)


# from queue import Queue
# import threading
# def batch_geocode_sync_gen(addresses: list, in_order=True, rate_limit=SETTINGS.simultaneous_requests) -> Generator[GeocodedLocation, None, None]:
#     geocoded_locs = Queue()
#     DONE = object()

#     async def run_async_gen():
#         async for result in RobustGeocoder(rate_limit=rate_limit).batch_geocode_agen(addresses, in_order=in_order):
#             geocoded_locs.put(result)

#     def start_event_loop():
#         loop = asyncio.new_event_loop()
#         asyncio.set_event_loop(loop)
#         try:
#             loop.run_until_complete(run_async_gen())
#         finally:
#             geocoded_locs.put(DONE)            

#     t = threading.Thread(target=start_event_loop)
#     t.start()

#     while True:
#         next_result = geocoded_locs.get(block=True)
#         if next_result is DONE:
#             break
#         yield next_result
