from .enums import ShipType
from .utils import StaticGameObject, wp_to_system, URL_BASE, handle_error


class InventoryError(ValueError):
    pass


class Shipyard(StaticGameObject):
    @property
    def url(self) -> str:
        return f"/systems/{wp_to_system(self.id)}/waypoints/{self.id}/shipyard"

    @property
    def ships(self) -> list[dict]:
        try:
            return self.get_data()['ships']
        except KeyError as e:
            raise InventoryError("No ships available for purchase. Are you docked at the shipyard?") from e

    def buy_ship(self, ship_type: ShipType, confirm: bool = True):
        if confirm:
            ship = next(s for s in self.ships if s['type'] == "SHIP_" + str(ship_type).upper())
            i = input(f"Buy {ship['name']} for {ship['purchasePrice']}? (Y/n)")
            if len(i) > 0 and i.lower() != 'y':
                return
        handle_error(self.pm.request(
            "POST",
            URL_BASE + "/my/ships",
            json={
                "shipType": "SHIP_" + str(ship_type).upper(),
                "waypointSymbol": self.id
            }
        ))
