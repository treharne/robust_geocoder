# Robust Geocoder 🌍📍

## Why Robust Geocoding?

Ever tried to geocode an address and ended up with inaccurate or incomplete results? Frustrating, right? That's where `robust_geocoder` comes in. This Python library aims to provide a more reliable and robust geocoding experience by combining multiple geocoding strategies and services.

## How It Works

`robust_geocoder` uses a strategy pattern to combine multiple geocoding services like Google Maps, ESRI, and others. It also includes fallback mechanisms and retries to ensure you get the most accurate geocoding results.

Additionally, it's super fast because it geocodes async, yet returns the geocodes in a sync generator as they complete, so you can access them simply in your sync code.

## Features

- `async` in a thread for massive parallelism
- Sync `generator` for easy access to results
- Request rate limiting to prevent exceeding provider rate limits
- Multiple geocoding strategies
- Extensible for custom strategies

## Quick Start
Here's a simple example using Google Maps as the geocoding service:

```python
from robust_geocoder.stream import GeocodeStreamerQueue
from robust_geocoder.strategies import robust

addresses = [
    '1731 ACHILLES LOOP, ILUKA, WA, Australia',
    '2 ANGUILLA GARDENS, ILUKA, WA, Australia',
    '37 ANTALYA VISTA, ILUKA, WA, Australia',
    '3 ARAL COURT, ILUKA, WA, Australia',
    '2 ATLANTIC AVENUE, ILUKA, WA, Australia',
]

streamer = GeocodeStreamerQueue(Geocoder=robust.Geocoder)
for geocoded_loc in streamer.geocode_gen(TEST_ADDRESSES, in_order=True):
    assert isinstance(geocoded_loc, GeocodedLocation)
    print(geocoded_loc.address, geocoded_loc.lat, geocoded_loc.log)
```

## Contributing
Feel free to open issues or PRs. We're always looking for ways to make robust_geocoder even more robust!