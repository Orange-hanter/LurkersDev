from ..models import Table, Guest, Staff


def create_tables(count: int, capacity: int) -> list[Table]:
    return [Table(table_id=i, capacity=capacity) for i in range(count)]


def find_free_table(tables: list[Table]) -> Table | None:
    for t in tables:
        if t.is_free:
            return t
    return None


def allocate_table(table: Table, guest: Guest, staff: Staff, duration: int) -> None:
    table.state = "occupied"
    table.guest = guest
    table.staff = staff
    table.busy_timer = duration


def release_table(table: Table) -> None:
    table.state = "free"
    table.guest = None
    table.staff = None
    table.busy_timer = 0


def find_ready_staff(staff_list: list[Staff]) -> Staff | None:
    for s in staff_list:
        if s.is_ready and s.stamina > s.rest_threshold:
            return s
    return None
