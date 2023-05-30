from urllib3 import request
from urllib3.util.retry import Retry, RequestHistory
from functools import cache, cached_property
import json
from xdg_base_dirs import xdg_data_home
from pathlib import Path
from .enums import FactionSymbol
from .utils import URL_BASE, GameObject, handle_error, RateLimitedPoolManager
from .contract import Contract
from .faction import Faction
from .waypoint import Waypoint
from .ship import Ship


class Agent(GameObject):
    def __init__(self, token: str):
        self.token = token
        h = tuple(RequestHistory(None, None, None, None, None) for _ in range(3))  # Makes backoff work
        r = Retry(allowed_methods=('DELETE', 'GET', 'POST', 'HEAD', 'OPTIONS', 'PUT', 'TRACE'), backoff_factor=0.4, history=h, respect_retry_after_header=True)
        self.pm = RateLimitedPoolManager(retries=r, num_pools=1, block=True, maxsize=1, headers={
            "Authorization": f"Bearer {token}"
        })

    @property
    def url(self) -> str:
        return "/my/agent"

    @classmethod
    def register(cls, name: str, faction: FactionSymbol):
        r = request(
            "POST",
            URL_BASE + "/register",
            json={
                "symbol": name,
                "faction": str(faction).upper()
            }
        )
        if r.status != 201:
            raise Exception(r.json())
        return cls(r.json()['data']['token'])

    @classmethod
    def load(cls, name: str, local: bool = False):
        with open(cls._token_path(local), "r") as f:
            tokens = json.load(f)
            return cls(tokens[name.upper()])

    def save_token(self, local: bool = False):
        tokens = {}
        try:
            with open(Agent._token_path(local), "r") as f:
                tokens = json.load(f)
        except (FileNotFoundError, json.decoder.JSONDecodeError):
            pass
        with open(Agent._token_path(local), "w") as f:
            tokens[self.get_data()['symbol']] = self.token
            json.dump(tokens, f, indent=4)

    @cache
    @staticmethod
    def _token_path(local: bool):
        p = Path(".") if local else xdg_data_home() / "spacetraders-py"
        p.mkdir(parents=True, exist_ok=True)
        p = p / "tokens.json"
        return p

    @property
    def contracts(self) -> list[Contract]:
        r = handle_error(self.pm.request("GET", URL_BASE + "/my/contracts"))
        return [Contract(self.pm, d['id']) for d in r.json()['data']]

    @property
    def fleet(self) -> list[Ship]:
        r = handle_error(self.pm.request("GET", URL_BASE + "/my/ships"))
        return [Ship(self.pm, d['symbol']) for d in r.json()['data']]

    @property
    def credits(self) -> int:
        return self.get_data()['credits']

    @cached_property
    def factions(self) -> list[Faction]:
        r = handle_error(self.pm.request("GET", URL_BASE + "/factions"))
        return [Faction(self.pm, d['symbol']) for d in r.json()['data']]

    @cached_property
    def headquarters(self) -> Waypoint:
        return Waypoint(self.pm, self.get_data()['headquarters'])
