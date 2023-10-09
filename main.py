import asyncio
import logging
from typing import Generator
from dotenv import load_dotenv
from base import BaseGeocoder
from google import GoogleGeocoder
from esri import EsriGeocoder

from common import GeocodedLocation, GeocoderError

load_dotenv()

logger = logging.getLogger(__name__)

class SETTINGS:
    simultaneous_requests = 2

class RobustGeocoder(BaseGeocoder):
    '''
    A geocoder that uses multiple geocoders to geocode addresses.
    If the first geocoder fails, it tries the next one.
    '''
    def __init__(self, rate_limit=50):
        self.google = GoogleGeocoder(rate_limit=rate_limit)
        self.esri = EsriGeocoder(rate_limit=rate_limit)

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


def batch_geocode_sync_gen(addresses: list, in_order=True, rate_limit=SETTINGS.simultaneous_requests) -> Generator[GeocodedLocation, None, None]:
    async def run_async_gen():
        geocoder = RobustGeocoder(rate_limit=rate_limit)
        async for result in geocoder.batch_geocode_generator(addresses, in_order=in_order):
            yield result

    gen = run_async_gen()

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
