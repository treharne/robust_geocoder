from dataclasses import dataclass

class GeocoderError(Exception): ...

class FailedGeocodeError(GeocoderError): ...

class BadAuthError(GeocoderError): ...

class RateLimitError(GeocoderError): ...

class ConnectionError(GeocoderError): ...

class BadRequestError(GeocoderError): ...

class ServerError(GeocoderError): ...

@dataclass
class GeocodedLocation:
    address: str
    lat: float
    lon: float
    geocode_address: str

    @classmethod
    def null_island(cls, address: str) -> 'GeocodedLocation':
        return cls(
            address=address, 
            lat=0, 
            lon=0, 
            geocode_address='Could not geocode'
        )
