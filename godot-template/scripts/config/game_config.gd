class_name GameConfig
## Game balance constants — mirrors restaurant_simulator/config.py

# Economy
const DAILY_SALARY_PER_SKILL: int = 30
const STARTING_BUDGET: int = 500
const REPAIR_COST: int = 20
const REPAIR_AMOUNT: int = 50

# Reputation
const REP_MIN: int = -50
const REP_MAX: int = 100
const DAILY_EVENT_CHANCE: float = 0.20
const EQUIP_LOW_DURABILITY: int = 20

# Time
const WORK_START_HOUR: int = 9
const WORK_END_HOUR: int = 21
const TOTAL_TICKS_PER_DAY: int = 100

# Events
const RANDOM_EVENT_CHANCE: float = 0.08

# Spawning
const SPAWN_BASE_RATE: float = 0.3
const SPAWN_REP_FACTOR: float = 0.01
const SPAWN_VARIANCE_LOW: float = 0.8
const SPAWN_VARIANCE_HIGH: float = 1.2

# Time of day multipliers
const TIME_OF_DAY_MULTIPLIERS: Dictionary = {
	Vector2i(0, 20): 0.5,
	Vector2i(20, 40): 1.5,
	Vector2i(40, 60): 2.0,
	Vector2i(60, 80): 1.5,
	Vector2i(80, 100): 0.5,
}

# Guests
const GUEST_BUDGET_MEAN: float = 40.0
const GUEST_BUDGET_STDDEV: float = 15.0
const GUEST_BUDGET_MIN: float = 5.0
const GUEST_PATIENCE_MIN: int = 3
const GUEST_PATIENCE_MAX: int = 8
const GUEST_BASE_EXPECTATION: float = 3.0
const GUEST_EXPECTATION_REP_FACTOR: float = 0.05

# Service
const QUALITY_STAFF_WEIGHT: float = 0.7
const QUALITY_EQUIP_WEIGHT: float = 0.3
const SERVICE_DURATION: int = 5
const SUCCESS_INCOME_MULT: float = 1.2
const SUCCESS_REP_GAIN: int = 3
const FAILURE_COST_MULT: float = 0.3
const FAILURE_REP_LOSS: int = 10
const GUEST_LEFT_REP_LOSS: int = 2

# Stamina
const REST_THRESHOLD: float = 0.3
const REST_RECOVERY_RATE: int = 2

# Equipment
const EQUIP_DEGRADE_PER_SERVICE: int = 1

# Tables
const MAX_TABLES: int = 20

static func table_seat_count(size: String) -> int:
	match size:
		"small": return 2
		"medium": return 4
		"large": return 6
	return 0

# UI
const WINDOW_WIDTH: int = 960
const WINDOW_HEIGHT: int = 640
const BG_COLOR: Color = Color(0.102, 0.102, 0.18, 1.0)
const DEFAULT_TICK_INTERVAL: float = 0.5
const FPS: int = 60

# Equipment tiers: (label, price, quality, max_durability)
const EQUIPMENT_TIERS: Dictionary = {
	0: {"label": "Basic",    "price": 50,  "quality": 1, "max_durability": 80},
	1: {"label": "Standard", "price": 100, "quality": 3, "max_durability": 120},
	2: {"label": "Premium",  "price": 180, "quality": 5, "max_durability": 150},
}

# Guest types: {type_name: {weight, budget_mult, exp_mult, rep_mult, label, priority}}
static func guest_types() -> Dictionary:
	return {
		"regular":  {"weight": 70, "budget_mult": 1.0, "exp_mult": 1.0, "rep_mult": 1.0, "label": "Regular",  "priority": 0},
		"business": {"weight": 20, "budget_mult": 1.5, "exp_mult": 1.2, "rep_mult": 1.5, "label": "Business", "priority": 0},
		"vip":      {"weight": 8,  "budget_mult": 2.5, "exp_mult": 1.5, "rep_mult": 2.0, "label": "VIP",      "priority": 1},
		"critic":   {"weight": 2,  "budget_mult": 3.0, "exp_mult": 2.0, "rep_mult": 5.0, "label": "CRITIC",   "priority": 1},
	}