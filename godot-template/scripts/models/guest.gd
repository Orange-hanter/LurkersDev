class_name Guest
extends Resource
## A guest waiting to be served.

enum GuestType { REGULAR, BUSINESS, VIP, CRITIC }

@export var guest_type: GuestType = GuestType.REGULAR
@export var budget: float = 40.0
@export var patience_ticks: int = 5
@export var expectation: float = 3.0
@export var wait_timer: int = 0
@export var mood: float = 1.0
@export var party_size: int = 1
@export var max_check: float = 40.0

## String key into GameConfig.guest_types()
func type_key() -> String:
	match guest_type:
		GuestType.REGULAR:  return "regular"
		GuestType.BUSINESS: return "business"
		GuestType.VIP:      return "vip"
		GuestType.CRITIC:   return "critic"
	return "regular"

func type_label() -> String:
	return GameConfig.guest_types()[type_key()]["label"]

func priority() -> int:
	return int(GameConfig.guest_types()[type_key()]["priority"])

func check_value(menu_price: int) -> float:
	return float(menu_price * party_size)

func price_pressure(menu_price: int) -> float:
	return maxf(0.0, check_value(menu_price) - max_check) * GameConfig.PRICE_PRESSURE_PER_DOLLAR

static func generate_random(guest_types_override: Dictionary = {}) -> Guest:
	var pool := guest_types_override
	if pool.is_empty():
		pool = GameConfig.guest_types()
	var total_weight := 0
	for key in pool.keys():
		total_weight += pool[key]["weight"]
	var roll := randi_range(1, total_weight)
	var cumulative := 0
	var chosen_key := "regular"
	for key in pool.keys():
		cumulative += pool[key]["weight"]
		if roll <= cumulative:
			chosen_key = key
			break

	var info: Dictionary = pool[chosen_key]
	var guest := Guest.new()
	match chosen_key:
		"regular":  guest.guest_type = GuestType.REGULAR
		"business": guest.guest_type = GuestType.BUSINESS
		"vip":      guest.guest_type = GuestType.VIP
		"critic":   guest.guest_type = GuestType.CRITIC
	guest.party_size = randi_range(int(info["party_min"]), int(info["party_max"]))
	guest.budget = maxf(GameConfig.GUEST_BUDGET_MIN,
		clampf(randfn(GameConfig.GUEST_BUDGET_MEAN, GameConfig.GUEST_BUDGET_STDDEV),
			GameConfig.GUEST_BUDGET_MIN, GameConfig.GUEST_BUDGET_MEAN * 3.0))
	guest.budget *= info["budget_mult"]
	guest.max_check = guest.budget * guest.party_size
	guest.patience_ticks = randi_range(GameConfig.GUEST_PATIENCE_MIN, GameConfig.GUEST_PATIENCE_MAX)
	guest.patience_ticks += GameState.decor_level * GameConfig.DECOR_PATIENCE_BONUS
	guest.expectation = GameConfig.GUEST_BASE_EXPECTATION + (GameState.reputation * GameConfig.GUEST_EXPECTATION_REP_FACTOR)
	guest.expectation *= info["exp_mult"]
	return guest
