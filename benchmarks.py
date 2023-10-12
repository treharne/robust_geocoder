
from contextlib import contextmanager
import time
from common import GeocodedLocation

from stream import GeocodeStreamerQueue, GeocoderStreamerAsync
from mock_geocoders import make_mock_geocoder

REQUEST_DURATION = 0.1

def with_queue(addresses: list, rate_limit: int=2):
    Geocoder = make_mock_geocoder(request_duration=REQUEST_DURATION)
    geocoder_streamer = GeocodeStreamerQueue(rate_limit=rate_limit, Geocoder=Geocoder)
    for result in geocoder_streamer.geocode_gen(addresses, in_order=True):
        assert isinstance(result, GeocodedLocation)

def with_async_gen(addresses: list, rate_limit: int=2):
    Geocoder = make_mock_geocoder(request_duration=REQUEST_DURATION)
    geocoder_streamer = GeocoderStreamerAsync(rate_limit=rate_limit, Geocoder=Geocoder)
    for result in geocoder_streamer.geocode_gen(addresses, in_order=True):
        assert isinstance(result, GeocodedLocation)


@contextmanager
def timeit(name=''):
    start = time.time()
    yield
    end = time.time() - start
    print(f'{name} took {end:.2f} seconds')


if __name__ == '__main__':
    bad_address = [
        # ';arshjg[rio vav;lkjer ijve]',
        # ' guh409g78h3p;q3209jsdh fuh 2;4h 9',
    ]

    from example_addresses import addresses
    addresses = bad_address + addresses
    addresses = addresses[:100]

    rate_limit = 20

    with timeit('Queue approach'):
        with_queue(addresses, rate_limit)
    with timeit('Async generator approach'):
        with_async_gen(addresses, rate_limit)
