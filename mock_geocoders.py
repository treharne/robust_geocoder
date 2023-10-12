# Set REQUEST_DURATION to zero for the purpose of testing, but you 
# can set it higher (realistic is 0.1 or 0.2) for 
# benchmarking performance.
import asyncio
import json
from typing import Type
import httpx

from strategies import esri, google, robust
import protocols


REQUEST_DURATION = 0.05

ESRI_TOKEN_RESP_MSG =  {'access_token': '[[fake_token]]', 'expires_in': 300}
ESRI_GEOCODE_RESP_MSG = {
    'candidates': [{
        'address': 'Mocked Geocoded Address in ESRI Response', 
        'location': {'x': 115.72874704177, 'y': -31.733750976498}, 
}]}
GOOGLE_GEOCODE_RESP_MSG = {'results': [{
        'formatted_address': 'Mocked Geocoded Address in Google Response', 
        'geometry': {'location': {'lat': -31.7337549, 'lng': 115.728749}}, 
    }],
    'status': 'OK'
}

def make_mock_transport(request_duration=REQUEST_DURATION):
    class MockTransport(httpx.AsyncBaseTransport):
        @staticmethod
        def _make_response(message: dict, status_code: int):
            content = json.dumps(message).encode("utf-8")
            stream = httpx.ByteStream(content)
            headers = [(b"content-type", b"application/json")]
            return httpx.Response(status_code, headers=headers, stream=stream)

        async def handle_async_request(self, request):
            req_url = request.url.scheme + '://' + request.url.host + request.url.path

            await asyncio.sleep(request_duration)

            if req_url == esri.Geocoder.token_url:
                return self._make_response(ESRI_TOKEN_RESP_MSG, 200)
            elif req_url == esri.Geocoder.geocode_url:
                return self._make_response(ESRI_GEOCODE_RESP_MSG, 200)
            elif req_url == google.Geocoder.url:
                return self._make_response(GOOGLE_GEOCODE_RESP_MSG, 200)
            else:
                raise NotImplementedError(f'No mock response for request: {request}')

    return MockTransport()


def make_mock_geocoder(Geocoder: Type[protocols.BulkAsyncGeocoder] = robust.Geocoder, request_duration=REQUEST_DURATION):
    def MockClient(self):
        return httpx.AsyncClient(transport=make_mock_transport(request_duration))

    class MockGeocoder(Geocoder):
        RequestClient = MockClient

    return MockGeocoder