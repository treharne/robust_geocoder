from enum import Enum
import os
from typing import Tuple
from dotenv import load_dotenv

import httpx
import logging

from strategies import abstract

from common import GeocodedLocation

from common import (
    GeocodedLocation,
    BadRequestError, GeocoderError, FailedGeocodeError, 
    BadAuthError, RateLimitError, ConnectionError, 
    ServerError,
)

load_dotenv()

logger = logging.getLogger(__name__)

class STATUS(str, Enum):
    '''
    From Google Geocoder docs https://developers.google.com/maps/documentation/geocoding/requests-geocoding#StatusCodes

    "OK" indicates that no errors occurred; the address was successfully parsed and at least one geocode was returned.
    "ZERO_RESULTS" indicates that the geocode was successful but returned no results. This may occur if the geocoder was passed a non-existent address.
    OVER_DAILY_LIMIT indicates any of the following:
        The API key is missing or invalid.
        Billing has not been enabled on your account.
        A self-imposed usage cap has been exceeded.
        The provided method of payment is no longer valid (for example, a credit card has expired).
        See the Maps FAQ to learn how to fix this.

    "OVER_QUERY_LIMIT" indicates that you are over your quota.
    "REQUEST_DENIED" indicates that your request was denied.
    "INVALID_REQUEST" generally indicates that the query (address, components or latlng) is missing.
    "UNKNOWN_ERROR" indicates that the request could not be processed due to a server error. The request may succeed if you try again.
    '''
    OK = 'OK'
    ZERO_RESULTS = 'ZERO_RESULTS'
    OVER_DAILY_LIMIT = 'OVER_DAILY_LIMIT'
    OVER_QUERY_LIMIT = 'OVER_QUERY_LIMIT'
    REQUEST_DENIED = 'REQUEST_DENIED'
    INVALID_REQUEST = 'INVALID_REQUEST'
    UNKNOWN_ERROR = 'UNKNOWN_ERROR'


class Geocoder(abstract.Geocoder):
    url = 'https://maps.googleapis.com/maps/api/geocode/json'
    key = os.environ['GOOGLE_API_KEY']
    
    async def _prepare_request(self, address: str) -> httpx.Request:
        return httpx.Request(
            method='GET',
            url=self.url,
            params={'address': address, 'key': self.key}
        )
    
    async def _raise_for_status(self, address: str, response_body: dict) -> STATUS:
        status = response_body.get('status')

        if status == STATUS.OK:
            return STATUS.OK
        
        logger.error(f'[{self.name}]: Error geocoding address: "{address}". Status: {status}. Response: {response_body}')

        if status == STATUS.ZERO_RESULTS:
            raise FailedGeocodeError()
        elif status == STATUS.OVER_DAILY_LIMIT:
            raise RateLimitError()
        elif status == STATUS.OVER_QUERY_LIMIT:
            raise RateLimitError()
        elif status == STATUS.REQUEST_DENIED:
            raise BadAuthError()
        elif status == STATUS.INVALID_REQUEST:
            raise GeocoderError()
        elif status == STATUS.UNKNOWN_ERROR:
            raise GeocoderError()
        else:
            raise GeocoderError()

    async def _parse_response_body(self, address: str, response_body: dict) -> Tuple[float, float, str]:
        try:
            results = response_body['results']
        except KeyError as e:
            logger.error(f'[{self.name}]: Error geocoding address: "{address}". Invalid response format: {response_body}. Error: {e}')
            raise GeocoderError()

        try:
            first = results[0]
        except IndexError:
            logger.error(f'[{self.name}]: Error geocoding address: "{address}". No Results. Response: {response_body}')
            raise FailedGeocodeError()

        try:
            loc = first['geometry']['location']
            lat = loc['lat']
            lon = loc['lng']
            geocode_address = first['formatted_address']
        except KeyError as e:
            logger.error(f'[{self.name}]: Error geocoding address: "{address}". Invalid response format: {response_body}. Error: {e}')
            raise GeocoderError()
        
        return lat, lon, geocode_address

    async def _response_to_location(self, address: str, response_body: dict) -> GeocodedLocation:
        await self._raise_for_status(address, response_body)
        lat, lon, geocode_address = await self._parse_response_body(address, response_body)
        
        return GeocodedLocation(
            address=address,
            lat=round(lat, 6),
            lon=round(lon, 6),
            geocode_address=geocode_address,
        )
