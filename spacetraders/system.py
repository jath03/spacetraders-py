from functools import cached_property
from .utils import StaticGameObject, URL_BASE, handle_error
from .waypoint import Waypoint


class System(StaticGameObject):
    @property
    def url(self) -> str:
        return f"/systems/{self.id}"

    def __repr__(self):
        data = self.get_data()
        return (
            f"System(symbol={data['symbol']}, "
            f"type={data['type']})"
        )

    @cached_property
    def waypoints(self):
        r = handle_error(self.pm.request("GET", URL_BASE + f"/systems/{self.id}/waypoints"))
        return [Waypoint(self.pm, d['symbol']) for d in r.json()['data']]
