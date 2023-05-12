from .utils import GameObject, wp_to_system
from .enums import Goods


class Market(GameObject):
    @property
    def url(self) -> str:
        return f"/systems/{wp_to_system(self.id)}/waypoints/{self.id}/market"

    @property
    def exports(self) -> list[Goods]:
        return [Goods(item['symbol'].lower()) for item in self.get_data()['exports']]

    @property
    def imports(self) -> list[Goods]:
        return [Goods(item['symbol'].lower()) for item in self.get_data()['imports']]

    @property
    def exchange(self) -> list[Goods]:
        return [Goods(item['symbol'].lower()) for item in self.get_data()['exchange']]

    def details(self, item: Goods) -> dict:
        for i in self.get_data()['tradeGoods']:
            if i['symbol'] == str(item).upper():
                return i
        return {}

    def cargo_value(self, inventory: dict[Goods, int]) -> int:
        data = self.get_data()['tradeGoods']
        total = 0
        for item, quantity in inventory.items():
            for i in data:
                if i['symbol'] == str(item).upper():
                    total += i['sellPrice'] * quantity
        return total
