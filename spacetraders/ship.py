from typing import Iterator, Self
from datetime import datetime, timezone, timedelta
import time
from .enums import ShipStatus, FlightMode, WaypointType, WaypointTrait, Goods
from .utils import GameObject, URL_BASE, handle_error, CooldownError
from .system import System
from .waypoint import Waypoint


class Nav(GameObject):
    CACHED_SYSTEMS: dict[str, System] = {}

    @property
    def url(self) -> str:
        return f"/my/ships/{self.id}/nav"

    @property
    def system(self) -> System:
        symbol = self.get_data()['systemSymbol']
        try:
            return self.CACHED_SYSTEMS[symbol]
        except KeyError:
            system = System(self.pm, symbol)
            self.CACHED_SYSTEMS[symbol] = system
            return system

    @property
    def waypoint(self) -> Waypoint:
        return Waypoint(self.pm, self.get_data()['waypointSymbol'])

    @property
    def status(self) -> ShipStatus:
        return ShipStatus(self.get_data()['status'].lower())

    @property
    def mode(self) -> FlightMode:
        return FlightMode(self.get_data()['flightMode'].lower())

    def find_traits(self, traits: tuple[WaypointTrait]) -> Iterator[Waypoint]:
        for wp in self.system.waypoints:
            if all(trait in wp.traits for trait in traits):
                yield wp

    def find_type(self, wp_type: WaypointType) -> Iterator[Waypoint]:
        for wp in self.system.waypoints:
            if wp.type == wp_type:
                yield wp

    @property
    def eta(self) -> int:
        data = self.get_data()
        if data['status'] == "IN_TRANSIT":
            return datetime.fromisoformat(data['route']['arrival']) - datetime.now(timezone.utc)
        else:
            return timedelta()


class Ship(GameObject):
    def __init__(self, pm, id: str):
        super().__init__(pm, id)
        self.nav = Nav(pm, id)

    @property
    def url(self) -> str:
        return f"/my/ships/{self.id}"

    def __repr__(self):
        data = self.get_data()
        return (
            f"Ship(symbol={data['symbol']}, "
            f"role={data['registration']['role']}, "
            f"waypoint={data['nav']['waypointSymbol']}, "
            f"status={data['nav']['status']})"
        )

    def navigate(self, wp: Waypoint) -> float:
        handle_error(self.pm.request(
            "POST",
            URL_BASE + self.url + "/navigate",
            json={"waypointSymbol": wp.id}
        ))
        return self.nav.eta

    def dock(self):
        handle_error(self.pm.request("POST", URL_BASE + self.url + "/dock"))

    def orbit(self):
        handle_error(self.pm.request("POST", URL_BASE + self.url + "/orbit"))

    def extract(self) -> int:
        return handle_error(self.pm.request("POST", URL_BASE + self.url + "/extract"), 201).json()['data']['cooldown']['remainingSeconds']

    def extract_until_full(self):
        while len(set(self.cargo_status)) != 1:
            try:
                time.sleep(self.extract())
            except CooldownError:
                time.sleep(1)

    def refuel(self):
        handle_error(self.pm.request("POST", URL_BASE + self.url + "/refuel"))

    def warp(self, destination: str):
        handle_error(self.pm.request(
            "POST",
            URL_BASE + self.url + "/warp",
            json={
                "waypointSymbol": destination
            }
        ))

    @property
    def inventory(self) -> dict[Goods, int]:
        return {Goods(item['symbol'].lower()): item['units'] for item in self.get_data()['cargo']['inventory']}

    @property
    def cargo_status(self) -> tuple[int, int]:
        data = self.get_data()['cargo']
        return (data['units'], data['capacity'])

    def sell(self, item: Goods, units: int):
        handle_error(self.pm.request(
            "POST",
            URL_BASE + self.url + "/sell",
            json={
                "symbol": str(item).upper(),
                "units": units
            }
        ), 201)

    def sell_all(self, do_not_sell: tuple[Goods] | None = None):
        for (good, quantity) in self.inventory.items():
            if do_not_sell is None or good not in do_not_sell:
                self.sell(good, quantity)

    def buy(self, item: Goods, units: int):
        handle_error(self.pm.request(
            "POST",
            URL_BASE + self.url + "/buy",
            json={
                "symbol": str(Goods).upper(),
                "units": units
            }
        ))

    def transfer(self, item: Goods, units: int, ship: Self):
        handle_error(self.pm.request(
            "POST",
            URL_BASE + self.url + "/transfer",
            json={
                "tradeSymbol": str(Goods).upper(),
                "units": units,
                "shipSymbol": ship.id
            }
        ))

    def wait_for_arrival(self):
        time.sleep(self.nav.eta.seconds)
