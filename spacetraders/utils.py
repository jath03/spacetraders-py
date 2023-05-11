from urllib3 import PoolManager
from urllib3.response import BaseHTTPResponse
from dataclasses import dataclass
from enum import StrEnum, auto
from abc import ABC, abstractmethod
from functools import cache
import time

URL_BASE = "https://api.spacetraders.io/v2"


class APIError(Exception):
    pass


class RateLimitException(Exception):
    pass


def wp_to_system(waypoint_symbol: str) -> str:
    return '-'.join(waypoint_symbol.split('-')[:2])


def time_to_seconds(t: str) -> float:
    t = t.split('.')[0]
    return time.mktime(time.strptime(t, "%Y-%m-%dT%H:%M:%S"))


def handle_error(response: BaseHTTPResponse, expected: int = 200):
    if response.status == expected:
        return response
    elif response.status == 429:
        raise RateLimitException()
    else:
        raise APIError(response.json()['error']['message'])


class GameObject(ABC):
    def __init__(self, pm: PoolManager, id: str | None = None):
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
