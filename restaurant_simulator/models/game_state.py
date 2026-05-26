from typing import List, Dict
from .equipment import Equipment
from .staff import Staff
from .guest import Guest
from .table import Table
from ..config import STARTING_BUDGET, WORK_START_HOUR


class GameState:
    def __init__(self):
        self.budget = STARTING_BUDGET
        self.reputation = 0.0
        self.kitchen = Equipment("Kitchen", 0, 0)
        self.hall = Equipment("Hall", 0, 0)
        self.staff_list: List[Staff] = []
        self.guest_queue: List[Guest] = []
        self.tables: List[Table] = []
        self.tick = 0
        self.total_ticks = 100
        self.start_minute = WORK_START_HOUR * 60
        self.day = 1
        self.day_history: List[Dict] = []
        self.rush_hour_active = False
        self.rush_hour_remaining = 0
        self.day_ended = False

        self.pending_income: float = 0.0
        self.pending_expense: float = 0.0
        self.pending_rep: float = 0.0
        self.guests_served: int = 0
        self.avg_quality: float = 0.0
        self.lost_guests: int = 0
        self.daily_event = None

    @property
    def avg_equipment_quality(self) -> float:
        return (self.kitchen.effective_quality + self.hall.effective_quality) / 2.0

    @property
    def avg_durability_pct(self) -> float:
        total_max = self.kitchen.max_durability + self.hall.max_durability
        if total_max == 0:
            return 100.0
        return ((self.kitchen.durability + self.hall.durability) / total_max) * 100

    def current_time_str(self) -> str:
        minutes = self.start_minute + self.tick * 5
        h = (minutes // 60) % 24
        m = minutes % 60
        return f"{h:02d}:{m:02d}"

    def time_remaining(self) -> int:
        return max(0, self.total_ticks - self.tick)

    def hire_staff(self, skill: int, daily_salary: int) -> None:
        self.staff_list.append(Staff(skill, daily_salary))

    def fire_staff(self, index: int) -> None:
        if 0 <= index < len(self.staff_list):
            self.staff_list.pop(index)

    def reset_daily(self) -> None:
        for table in self.tables:
            table.state = "free"
            table.busy_timer = 0
            table.guest = None
            table.staff = None
        self.guest_queue.clear()
        for staff in self.staff_list:
            staff.status = "ready"
            staff.busy_timer = 0
            staff.stamina = staff.max_stamina
        self.pending_income = 0.0
        self.pending_expense = 0.0
        self.pending_rep = 0.0
        self.guests_served = 0
        self.avg_quality = 0.0
        self.lost_guests = 0
        self.tick = 0
        self.day_ended = False
        self.daily_event = None