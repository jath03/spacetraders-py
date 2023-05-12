from .enums import ShipType
from .utils import StaticGameObject, wp_to_system, URL_BASE, handle_error


class InventoryError(ValueError):
    pass


class Shipyard(StaticGameObject):
    @property
    def url(self) -> str:
        return f"/systems/{wp_to_system(self.id)}/waypoints/{self.id}/shipyard"

    @property
    def ships(self) -> list[tuple[ShipType, int]]:
        try:
            ships = self.get_data()['ships']
            return [(ShipType(ship['type'].lower()), ship['purchasePrice']) for ship in ships]
        except KeyError as e:
            raise InventoryError("No ships available for purchase. Are you docked at the shipyard?") from e

    def buy_ship(self, ship_type: ShipType):
        handle_error(self.pm.request(
            "POST",
            URL_BASE + "/my/ships",
            json={
                "shipType": str(ship_type).upper(),
                "waypointSymbol": self.id
            }
        ), 201)

    def ship_details(self, ship_type: ShipType) -> dict:
        for ship in self.get_data()['ships']:
            if ship['type'] == str(ship_type).upper():
                return ship
