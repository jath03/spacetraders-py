from urllib3 import PoolManager
from urllib3.response import BaseHTTPResponse
from threading import Thread, Lock
from abc import ABC, abstractmethod
from functools import cache
from json import JSONDecodeError
import time

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


class Bucket:
    def __init__(self, max: int, period: int):
        self.max = max
        self.current = max
        self.period = period
        self.refill_end = None
        self.lock = Lock()

    def take(self) -> bool:
        with self.lock:
            if self.current == self.max:
                self.refill_end = time.time() + self.period + 0.1
                self.refill()
            if self.current > 0:
                self.current -= 1
                return True
            else:
                return False
        return False

    def refill(self):
        self.refill_thread = Thread(target=self._refill)
        self.refill_thread.start()

    def _refill(self):
        time.sleep(self.period + 0.1)
        with self.lock:
            self.current = self.max

    @property
    def time_remaining(self) -> float:
        return max(self.refill_end - time.time(), 0)


def rate_limit(f):
    buckets = [
        Bucket(2, 1),
        Bucket(10, 10)
    ]

    def rate_limited_func(*args, **kwargs):
        while True:
            for bucket in buckets:
                if bucket.take():
                    return f(*args, **kwargs)
            time.sleep(min(bucket.time_remaining for bucket in buckets))
    return rate_limited_func


class RateLimitedPoolManager(PoolManager):
    urlopen = rate_limit(PoolManager.urlopen)


class GameObject(ABC):
    def __init__(self, pm: RateLimitedPoolManager, id: str):
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
