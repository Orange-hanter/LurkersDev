class_name Equipment
extends Resource
## Represents a piece of kitchen or front-of-house equipment.

enum Tier { BASIC = 0, STANDARD = 1, PREMIUM = 2 }

@export var tier: Tier = Tier.BASIC
@export var quality: int = 1
@export var durability: float = 80.0
@export var max_durability: float = 80.0
@export var label: String = "Equipment"

## Effective quality: halved when durability drops below threshold.
func effective_quality() -> float:
	if durability < GameConfig.EQUIP_LOW_DURABILITY:
		return quality * 0.5
	return quality

## Durability as fraction 0..1
func durability_fraction() -> float:
	if max_durability <= 0:
		return 0.0
	return clamp(durability / max_durability, 0.0, 1.0)

static func create(tier_index: int, p_label: String) -> Equipment:
	var info: Dictionary = GameConfig.EQUIPMENT_TIERS[tier_index]
	var e := Equipment.new()
	e.tier = tier_index as Tier
	e.quality = info["quality"]
	e.max_durability = info["max_durability"]
	e.durability = e.max_durability
	e.label = p_label + " " + info["label"]
	return e
