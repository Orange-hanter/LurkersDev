from ..config import REST_THRESHOLD, REST_RECOVERY_RATE


class Staff:
    def __init__(self, skill: int, daily_salary: int):
        self.skill = skill
        self.daily_salary = daily_salary
        self.max_stamina = 100
        self.stamina = self.max_stamina
        self.rest_threshold = int(self.max_stamina * REST_THRESHOLD)
        self.status = "ready"
        self.busy_timer = 0

    @property
    def is_ready(self) -> bool:
        return self.status == "ready"

    @property
    def is_free(self) -> bool:
        return self.status in ("ready", "resting") and self.busy_timer == 0

    def assign_service(self, duration: int) -> None:
        self.status = "busy"
        self.busy_timer = duration

    def release(self) -> None:
        self.busy_timer = 0
        self.status = "ready"

    def tick_update(self) -> None:
        if self.status == "busy":
            if self.busy_timer > 0:
                self.busy_timer -= 1
        elif self.status == "resting":
            self.stamina = min(self.max_stamina, self.stamina + REST_RECOVERY_RATE)