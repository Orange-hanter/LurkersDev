GUEST_TYPES = {
    "regular":  {"weight": 70, "budget_mult": 1.0, "exp_mult": 1.0, "rep_mult": 1.0, "icon": "🔵", "label": "Regular"},
    "business": {"weight": 20, "budget_mult": 1.5, "exp_mult": 1.2, "rep_mult": 1.5, "icon": "🟡", "label": "Business"},
    "VIP":      {"weight": 8,  "budget_mult": 2.5, "exp_mult": 1.5, "rep_mult": 2.0, "icon": "🟣", "label": "VIP"},
    "critic":   {"weight": 2,  "budget_mult": 3.0, "exp_mult": 2.0, "rep_mult": 5.0, "icon": "🔴", "label": "CRITIC"},
}


class Guest:
    def __init__(self, guest_type: str, budget: float, patience_ticks: int, expectation: float):
        self.guest_type = guest_type
        self.budget = budget
        self.patience_ticks = patience_ticks
        self.expectation = expectation
        self.wait_timer = 0

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
