from enum import StrEnum, auto
from functools import cached_property
from typing import Iterator, Self
from .enums import ShipStatus, FlightMode, WaypointType, WaypointTrait, Goods
from .utils import GameObject, URL_BASE, time_to_seconds, handle_error
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
        return ShipStatus(self.get_data()['status'])

    @property
    def mode(self) -> FlightMode:
        return FlightMode(self.get_data()['flightMode'])

    def find_traits(self, traits: tuple[WaypointTrait]) -> Iterator[Waypoint]:
        for wp in self.system.waypoints:
            if all(trait in wp.traits for trait in traits):
                yield wp

    def find_type(self, wp_type: WaypointType) -> Iterator[Waypoint]:
        for wp in self.system.waypoints:
            if wp.type == wp_type:
                yield wp


class Ship(GameObject):
    def __init__(self, pm, id: str):
        super().__init__(pm, id)
        self.nav = Nav(self.pm, self.id)

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

    def navigate(self, wp: Waypoint):
        r = handle_error(self.pm.request(
            "POST",
            URL_BASE + self.url + "/navigate",
            json={"waypointSymbol": wp.id}
        ))
        arrival = r.json()['data']['nav']['route']['arrival']
        departure = r.json()['data']['nav']['route']['departureTime']
        print("Flight duration: " + str(time_to_seconds(arrival) - time_to_seconds(departure)))

    def dock(self):
        handle_error(self.pm.request("POST", URL_BASE + self.url + "/dock"))

    def orbit(self):
        handle_error(self.pm.request("POST", URL_BASE + self.url + "/orbit"))

    def extract(self):
        handle_error(self.pm.request("POST", URL_BASE + self.url + "/extract"), 201)

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
                "symbol": str(Goods).upper(),
                "units": units
            }
        ))

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
