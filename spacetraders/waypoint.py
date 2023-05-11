from functools import cached_property
from enum import StrEnum, auto
from .enums import WaypointTrait, WaypointType
from .utils import StaticGameObject, wp_to_system
from .shipyard import Shipyard
from .market import Market


class TraitError(ValueError):
    pass


class Waypoint(StaticGameObject):
    @property
    def url(self) -> str:
        return f"/systems/{wp_to_system(self.id)}/waypoints/{self.id}"

    def __repr__(self):
        data = self.get_data()
        return (
            f"Waypoint(symbol={data['symbol']}, "
            f"type={data['type']})"
        )

    @cached_property
    def traits(self):
        return tuple(WaypointTrait(trait['symbol'].lower()) for trait in self.get_data()['traits'])

    @cached_property
    def shipyard(self):
        if WaypointTrait.SHIPYARD in self.traits:
            return Shipyard(self.pm, self.id)
        else:
            raise TraitError("Trait SHIPYARD not found at this waypoint")

    @cached_property
    def market(self):
        if WaypointTrait.MARKETPLACE in self.traits:
            return Market(self.pm, self.id)
        else:
            return TraitError("Trait MARKETPLACE not found at this waypoint")

    @cached_property
    def type(self):
        return WaypointType(self.get_data()['type'].lower())
