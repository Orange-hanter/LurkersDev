from ..config import EQUIP_LOW_DURABILITY


class Equipment:
    def __init__(self, name: str, quality: int, price: int, max_durability: int = 100):
        self.name = name
        self.quality = quality
        self.price = price
        self.max_durability = max_durability
        self.durability = max_durability

    @property
    def effective_quality(self) -> float:
        if self.durability <= 0:
            return 0.0
        if self.durability < EQUIP_LOW_DURABILITY:
            return self.quality * 0.5
        return float(self.quality)

    @property
    def durability_pct(self) -> float:
        return min(100.0, (self.durability / self.max_durability) * 100) if self.max_durability > 0 else 100.0

    @property
    def needs_repair(self) -> bool:
        return self.durability < EQUIP_LOW_DURABILITY

    def degrade(self, amount: int = 1) -> None:
        self.durability = max(0, self.durability - amount)

    def repair(self, amount: int = 50) -> None:
        self.durability = min(self.max_durability, self.durability + amount)

    def replace(self, new_quality: int, new_price: int, new_max_durability: int) -> None:
        self.quality = new_quality
        self.price = new_price
        self.max_durability = new_max_durability
        self.durability = new_max_durability