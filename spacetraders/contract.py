import time
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

    def accept(self):
        handle_error(self.pm.request(
            "POST",
            URL_BASE + f"/my/contracts/{self.id}/accept",
        ))
