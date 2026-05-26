extends Node
## Manages random event definitions and triggers. Emits event_triggered
## when a tick event or daily event fires.

# --- Signals ---
signal event_triggered(event_type: String, data: Dictionary)

# --- Tick Events (8% per tick) ---
var tick_events: Array[Dictionary] = [
	{
		"name": "inspector",
		"weight": 10,
		"description": "Health inspector visits — equipment quality matters"
	},
	{
		"name": "rush_hour",
		"weight": 15,
		"description": "Rush hour! Guest spawn rate doubles for a few ticks"
	},
	{
		"name": "equipment_break",
		"weight": 10,
		"description": "Equipment malfunction — durability takes a hit"
	},
	{
		"name": "investor",
		"weight": 5,
		"description": "Investor visits — potential bonus income"
	},
	{
		"name": "party",
		"weight": 8,
		"description": "A party arrives — multiple guests at once"
	},
	{
		"name": "food_critic",
		"weight": 5,
		"description": "Food critic arrives — high expectations"
	},
]

# --- Daily Events (20% at day start) ---
var daily_events: Array[Dictionary] = [
	{
		"name": "health_inspection",
		"weight": 15,
		"description": "Scheduled health inspection — reputation at stake"
	},
	{
		"name": "vip_guest",
		"weight": 10,
		"description": "VIP reservation — big money if you satisfy them"
	},
	{
		"name": "equipment_breakdown",
		"weight": 10,
		"description": "Equipment breaks down at start of day"
	},
	{
		"name": "good_press",
		"weight": 8,
		"description": "Good press coverage — reputation boost"
	},
]


func pick_random_event(pool: Array[Dictionary]) -> Dictionary:
	var total_weight := 0
	for evt in pool:
		total_weight += evt["weight"]
	if total_weight == 0:
		return {}
	var roll := randi_range(1, total_weight)
	var cumulative := 0
	for evt in pool:
		cumulative += evt["weight"]
		if roll <= cumulative:
			return evt
	return {}


func trigger_tick_event() -> Dictionary:
	if randf() >= GameConfig.RANDOM_EVENT_CHANCE:
		return {}
	var evt := pick_random_event(tick_events)
	if evt.is_empty():
		return {}
	event_triggered.emit(evt["name"], evt)
	return evt


func trigger_daily_event() -> Dictionary:
	if randf() >= GameConfig.DAILY_EVENT_CHANCE:
		return {}
	var evt := pick_random_event(daily_events)
	if evt.is_empty():
		return {}
	event_triggered.emit(evt["name"], evt)
	return evt