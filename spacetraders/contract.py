from .enums import Goods
from .ship import Ship
from .utils import URL_BASE, GameObject, handle_error


class Contract(GameObject):
    @property
    def url(self) -> str:
        return f"/my/contracts/{self.id}"

    def __repr__(self):
        data = self.get_data()
        return (
            f"Contract(type={data['type']}, "
            f"accepted={data['accepted']}, "
            f"deadline={data['terms']['deadline']})"
        )

    @property
    def accepted(self):
        return self.get_data()['accepted']

    def accept(self):
        handle_error(self.pm.request(
            "POST",
            URL_BASE + self.url + "/accept",
        ))

    def deliver(self, good: Goods, units: int, ship: Ship):
        handle_error(self.pm.request(
            "POST",
            URL_BASE + self.url + "/deliver",
            json={
                "shipSymbol": ship.id,
                "tradeSymbol": str(good).upper(),
                "units": units
            }
        ))

    def fulfill(self):
        handle_error(self.pm.request(
            "POST",
            URL_BASE + self.url + "/fulfill",
        ))

    @property
    def items(self) -> dict[Goods, int]:
        data = self.get_data()
        deliveries = data['terms']['deliver']
        return dict(map(lambda d: (Goods(d['tradeSymbol'].lower()), d['unitsRequired']), deliveries))
