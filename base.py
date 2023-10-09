from abc import ABC, abstractmethod
import asyncio
from json import JSONDecodeError
from typing import AsyncGenerator, List
import httpx
import logging

from common import GeocodedLocation

from common import (
    GeocodedLocation,
    BadRequestError, GeocoderError, FailedGeocodeError, 
    BadAuthError, RateLimitError, ConnectionError, 
    ServerError,
)

logger = logging.getLogger(__name__)

class BaseGeocoder(ABC):
    def __init__(self, rate_limit=2):
        self.semaphore = asyncio.Semaphore(rate_limit)
    
    @abstractmethod
    async def _prepare_request(self, address: str) -> httpx.Request:
        ...

    @abstractmethod
    async def _response_to_location(self, address: str, response: dict) -> GeocodedLocation:
        ...
        
    async def _call_with_client(self, address, client) -> dict:
        req = await self._prepare_request(address)
        try: 
            resp = await client.send(req)
        except httpx.RequestError as e:
            logger.error(f'[{self.name}]: Error geocoding address: "{address}". HTTPX Error: {e}')
            raise ConnectionError()
        
        if not resp.status_code == 200:
            logger.error(f'[{self.name}]: Error geocoding address: "{address}". Status: {resp.status_code}. Response: {resp.text}')
            if resp.status_code == 400:
                raise BadRequestError()
            if resp.status_code in {401, 403}:
                raise BadAuthError()
            if resp.status_code == 429:
                raise RateLimitError()
            if resp.status_code == 499:
                raise BadAuthError
            if resp.status_code >= 500:
                raise ServerError()
            raise GeocoderError()

        try:
            body = resp.json()
        except JSONDecodeError as e:
            logger.error(f'[{self.name}]: Error geocoding address: "{address}". Status: {resp.status_code}. Could not JSON decode response: {resp.text}')
            raise GeocoderError()

        return body

    async def _call(self, address):
        async with httpx.AsyncClient() as client:
            return await self._call_with_client(address, client)

    async def geocode(self, address: str) -> GeocodedLocation:
        response = await self._call(address)
        return await self._response_to_location(address, response)
    
    async def geocode_with_client(self, address: str, client) -> GeocodedLocation:
        async with self.semaphore:
            response = await self._call_with_client(address, client)
        return await self._response_to_location(address, response)
    
    async def batch_geocode_generator(self, addresses: List[str], in_order=True) -> AsyncGenerator[GeocodedLocation, None]:
        async with httpx.AsyncClient() as client:
            coros = (self.geocode_with_client(address, client) for address in addresses)
            tasks = [asyncio.create_task(coro) for coro in coros]  # tasks actually start running here.

            tasks = tasks if in_order else asyncio.as_completed(tasks)

            for result in tasks:
                yield await result

    @property
    def name(self):
        return self.__class__.__name__
