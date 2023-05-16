from urllib3 import PoolManager
from urllib3.exceptions import InvalidHeader
from urllib3.response import BaseHTTPResponse
from abc import ABC, abstractmethod
from functools import cache
from json import JSONDecodeError
import time
import re
import email

URL_BASE = "https://api.spacetraders.io/v2"


class APIError(Exception):
    pass


class ClientError(APIError):
    pass


class RateLimitException(ClientError):
    pass


class CooldownError(ClientError):
    pass


class InsufficientFuelError(ClientError):
    pass


def wp_to_system(waypoint_symbol: str) -> str:
    return '-'.join(waypoint_symbol.split('-')[:2])


def handle_error(response: BaseHTTPResponse, expected: int = 200):
    if response.status == expected:
        return response
    elif response.status == 429:
        try:
            raise RateLimitException(response.retries, response.json()['error'])
        except JSONDecodeError:
            raise RateLimitException(response.retries, response.data)
    elif 400 <= response.status <= 499:
        code = response.json()['error']['code']
        if code == 4000:
            raise CooldownError(response.json()['error']['data'])
        elif code == 4203:
            raise InsufficientFuelError(response.json()['error']['data'])
        elif code == 4204:
            return response
        else:
            raise ClientError(response.json()['error'])
    else:
        print(response.status)
        try:
            raise APIError(response.json()['error'])
        except JSONDecodeError:
            raise APIError(response.data)


def custom_parse_retry_after(self, retry_after):
    # Whitespace: https://tools.ietf.org/html/rfc7230#section-3.2.4
    if re.match(r"^\s*[0-9.]+\s*$", retry_after):
        seconds = float(retry_after)
    else:
        retry_date_tuple = email.utils.parsedate_tz(retry_after)
        if retry_date_tuple is None:
            raise InvalidHeader("Invalid Retry-After header: %s" % retry_after)
        if retry_date_tuple[9] is None:  # Python 2
            # Assume UTC if no timezone was specified
            # On Python2.7, parsedate_tz returns None for a timezone offset
            # instead of 0 if no timezone is given, where mktime_tz treats
            # a None timezone offset as local time.
            retry_date_tuple = retry_date_tuple[:9] + (0,) + retry_date_tuple[10:]

        retry_date = email.utils.mktime_tz(retry_date_tuple)
        seconds = retry_date - time.time()

    if seconds < 0:
        seconds = 0

    return seconds


class GameObject(ABC):
    def __init__(self, pm: PoolManager, id: str):
        self.pm = pm
        self.id = id

    @property
    @abstractmethod
    def url(self) -> str:
        pass

    def get_data(self) -> dict:
        r = handle_error(self.pm.request("GET", URL_BASE + self.url))
        return r.json()['data']

    def __repr__(self):
        try:
            data = self.get_data()
            return (
                f"{type(self).__name__}(symbol={data['symbol']})"
            )
        except KeyError:
            return super().__repr__()


class StaticGameObject(GameObject):
    @cache
    def get_data(self) -> dict:
        r = handle_error(self.pm.request("GET", URL_BASE + self.url))
        return r.json()['data']
