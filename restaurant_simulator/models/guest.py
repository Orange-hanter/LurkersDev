GUEST_TYPES = {
    "regular":  {"weight": 70, "budget_mult": 1.0, "exp_mult": 1.0, "rep_mult": 1.0, "icon": "r", "label": "Regular", "priority": 0},
    "business": {"weight": 20, "budget_mult": 1.5, "exp_mult": 1.2, "rep_mult": 1.5, "icon": "b", "label": "Business", "priority": 0},
    "VIP":      {"weight": 8,  "budget_mult": 2.5, "exp_mult": 1.5, "rep_mult": 2.0, "icon": "V", "label": "VIP", "priority": 1},
    "critic":   {"weight": 2,  "budget_mult": 3.0, "exp_mult": 2.0, "rep_mult": 5.0, "icon": "C", "label": "CRITIC", "priority": 1},
}


class Guest:
    def __init__(self, guest_type: str, budget: float, patience_ticks: int, expectation: float):
        self.guest_type = guest_type
        self.budget = budget
        self.patience_ticks = patience_ticks
        self.expectation = expectation
        self.wait_timer = 0
        self.mood = 1.0
        self.priority = GUEST_TYPES[guest_type]["priority"]

    @property
    def type_info(self) -> dict:
        return GUEST_TYPES[self.guest_type]

    @property
    def icon(self) -> str:
        return self.type_info["icon"]

    @property
    def label(self) -> str:
        return self.type_info["label"]

    @property
    def rep_multiplier(self) -> float:
        return self.type_info["rep_mult"]

    @property
    def expectation_multiplier(self) -> float:
        return self.type_info["exp_mult"]