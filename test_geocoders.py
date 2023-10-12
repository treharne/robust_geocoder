
import asyncio
import json
import httpx
from common import GeocodedLocation

from strategies import esri, google, robust
from stream import GeocodeStreamerQueue, GeocoderStreamerAsync

from example_addresses import addresses
from mock_geocoders import make_mock_geocoder

# Set REQUEST_DURATION to zero for the purpose of testing, but you 
# can set it higher (realistic is 0.1 or 0.2) for 
# benchmarking performance.
REQUEST_DURATION = 0.01
RATE_LIMIT = 2
TEST_ADDRESSES = addresses[:4]


def test_geocoder_streamer_queue():
    Geocoder = make_mock_geocoder(robust.Geocoder, REQUEST_DURATION)
    streamer = GeocodeStreamerQueue(rate_limit=RATE_LIMIT, Geocoder=Geocoder)
    for result in streamer.geocode_gen(TEST_ADDRESSES, in_order=True):
        assert isinstance(result, GeocodedLocation)


def test_geocoder_streamer_async():
    Geocoder = make_mock_geocoder(robust.Geocoder, REQUEST_DURATION)
    streamer = GeocoderStreamerAsync(rate_limit=RATE_LIMIT, Geocoder=Geocoder)
    for result in streamer.geocode_gen(TEST_ADDRESSES, in_order=True):
        assert isinstance(result, GeocodedLocation)


def test_esri_geocoder():
    Geocoder = make_mock_geocoder(esri.Geocoder, REQUEST_DURATION)
    streamer = GeocodeStreamerQueue(rate_limit=RATE_LIMIT, Geocoder=Geocoder)
    for result in streamer.geocode_gen(TEST_ADDRESSES, in_order=True):
        assert isinstance(result, GeocodedLocation)


def test_google_geocoder():
    Geocoder = make_mock_geocoder(google.Geocoder, REQUEST_DURATION)
    streamer = GeocodeStreamerQueue(rate_limit=RATE_LIMIT, Geocoder=Geocoder)
    for result in streamer.geocode_gen(TEST_ADDRESSES, in_order=True):
        assert isinstance(result, GeocodedLocation)

