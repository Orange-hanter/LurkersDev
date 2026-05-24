from ..config import STAMINA_RECOVERY_BASE, STAMINA_RECOVERY_KITCHEN_BONUS, SERVICE_BASE_STAMINA_DRAIN


class Staff:
    def __init__(self, skill: int, daily_salary: int):
        self.skill = skill
        self.daily_salary = daily_salary
        self.max_stamina = 100
        self.stamina = self.max_stamina
        self.busy_timer = 0

    @property
    def is_free(self) -> bool:
        return self.busy_timer == 0 and self.stamina > 0

    def start_service(self, stamina_drain: int = SERVICE_BASE_STAMINA_DRAIN) -> None:
        if not self.is_free:
            raise RuntimeError("Staff is not available")
        self.busy_timer = 1
        self.stamina = max(0, self.stamina - stamina_drain)

    def tick_update(self, kitchen_effective_quality: float = 0.0) -> None:
        if self.busy_timer > 0:
            self.busy_timer -= 1
        elif self.stamina < self.max_stamina:
            recovery = STAMINA_RECOVERY_BASE + int(kitchen_effective_quality * STAMINA_RECOVERY_KITCHEN_BONUS)
            self.stamina = min(self.max_stamina, self.stamina + recovery)
