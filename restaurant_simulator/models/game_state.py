from typing import List, Dict
from .equipment import Equipment
from .staff import Staff
from .guest import Guest
from ..config import STARTING_BUDGET, WORK_START_HOUR


class GameState:
    def __init__(self):
        self.budget = STARTING_BUDGET
        self.reputation = 0.0
        self.kitchen = Equipment("Kitchen", 0, 0)
        self.hall = Equipment("Hall", 0, 0)
        self.staff_list: List[Staff] = []
        self.guest_queue: List[Guest] = []
        self.tick = 0
        self.tick_minutes = 5
        self.total_ticks = 144
        self.start_minute = WORK_START_HOUR * 60
        self.served_total = 0
        self.served_success = 0
        self.served_fail = 0
        self.left_guests = 0
        self.day = 1
        self.day_history: List[Dict] = []
        self.debt_days = 0
        self.rush_hour_active = False
        self.rush_hour_remaining = 0

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
        minutes = self.start_minute + self.tick * self.tick_minutes
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
