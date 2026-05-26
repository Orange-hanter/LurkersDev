from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .guest import Guest
    from .staff import Staff


class Table:
    def __init__(self, table_id: int, capacity: int):
        self.table_id = table_id
        self.capacity = capacity
        self.state = "free"
        self.busy_timer = 0
        self.guest: "Guest | None" = None
        self.staff: "Staff | None" = None

    @property
    def is_free(self) -> bool:
        return self.state == "free"