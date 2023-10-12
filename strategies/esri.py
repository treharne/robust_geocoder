import asyncio
from dotenv import load_dotenv
import httpx
import logging
import os

from strategies import abstract
from common import BadAuthError, GeocodedLocation, GeocoderError, FailedGeocodeError

load_dotenv()
logger = logging.getLogger(__name__)


class Geocoder(abstract.Geocoder):
    client_id = os.environ['ESRI_CLIENT_ID']
    client_secret = os.environ['ESRI_CLIENT_SECRET']
    token_url = 'https://www.arcgis.com/sharing/rest/oauth2/token'
    geocode_url = 'https://geocode.arcgis.com/arcgis/rest/services/World/GeocodeServer/findAddressCandidates'

    def __init__(self, rate_limit: int = 2):
        self.token = None
        self.token_request_lock = asyncio.Lock()
        super().__init__(rate_limit=rate_limit)

    async def _login_params(self) -> dict:
        return {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': 'client_credentials',
            'expiration': 5,
            'f': 'json',
        }

    async def _get_token(self) -> str:
        if self.token:
            return self.token

        logger.info(f'[{self.name}]: Getting token')
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                url=self.token_url,
                params=await self._login_params(),
            )

        body = resp.json()
        return body['access_token']

    async def _safe_get_token(self) -> None:
        async with self.token_request_lock:
            if not self.token:
                self.token = await self._get_token()

    async def geocode_with_client(self, address: str, client) -> GeocodedLocation:
        if not self.token:
            await self._safe_get_token()

        try:
            geocoded_loc = await super().geocode_with_client(address, client)
        except BadAuthError as e:
            self.token = None
            await self._safe_get_token()
            geocoded_loc = await super().geocode_with_client(address, client)

        return geocoded_loc

    async def _prepare_request(self, address: str) -> httpx.Request:
        return httpx.Request(
            method='GET',
            url=self.geocode_url,
            params={
                'SingleLine': address, 
                'f': 'json', 
                'token': self.token,
                "outFields": "address,location,Score,LongLabel,ShortLabel,Match_addr,postal",
                "forStorage": 0,
            }
        )
    
    async def _response_to_location(self, address: str, response_body: dict) -> GeocodedLocation:
        if ('error' in response_body) or ('candidates' not in response_body):
            logger.error(f'[{self.name}]: Error geocoding "{address}". Response: {response_body}')
            raise GeocoderError()

        candidates = response_body['candidates']

        try:
            first = candidates[0]
        except IndexError:
            logger.error(f'[{self.name}]: Error geocoding address: "{address}". No Results. Response: {response_body}')
            raise FailedGeocodeError()

        try:
            loc = first['location']
            lat = loc['y']
            lon = loc['x']
        except KeyError as e:
            logger.error(f'[{self.name}]: Error geocoding address: "{address}". Invalid response format: {response_body}. Error: {e}')
            raise GeocoderError()

        return GeocodedLocation(
            address=address,
            lat=round(lat, 6),
            lon=round(lon, 6),
            geocode_address=first['address'],
        )
