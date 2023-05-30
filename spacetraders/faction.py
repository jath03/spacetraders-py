from .utils import StaticGameObject
from .waypoint import Waypoint


class Faction(StaticGameObject):
    @property
    def url(self) -> str:
        return f"/factions/{self.id}"

    @property
    def headquarters(self) -> Waypoint:
        return Waypoint(self.pm, self.get_data()['headquarters'])