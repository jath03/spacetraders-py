from .utils import GameObject


class Market(GameObject):
    @property
    def url(self) -> str:
        return f"/systems/{wp_to_system(self.id)}/waypoints/{self.id}/market"