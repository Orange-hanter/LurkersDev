extends Node
## Central game state singleton. Holds all runtime data and emits signals
## for reactive UI updates.

# --- Signals ---
signal guest_queued(guest: Guest)
signal guest_served(guest: Guest, quality: float, income: float)
signal guest_left(guest: Guest)
signal day_started(day: int)
signal day_ended(stats: Dictionary)
signal bankruptcy()
signal budget_changed(new_value: int)
signal rep_changed(new_value: int)
signal event_occurred(message: String)
signal tick_advanced(tick: int)

# --- Game Data ---
var budget: int = GameConfig.STARTING_BUDGET
var reputation: int = 0
var day: int = 1
var tick: int = 0
var paused: bool = false
var game_speed: float = 1.0
var rush_hour_active: bool = false
var current_phase: int = 0  ## 1..6 for the six tick phases

# Collections
var kitchen_equip: Equipment
var hall_equip: Equipment
var staff_list: Array[Staff] = []
var guest_queue: Array[Guest] = []
var tables: Array[Table] = []
var table_size_chosen: String = "medium"
var table_count_chosen: int = 4
var tick_interval_chosen: float = GameConfig.DEFAULT_TICK_INTERVAL
var tick_duration_minutes: int = 5

# Pending economy (resolved at end of day)
var pending_income: float = 0.0
var pending_expense: float = 0.0
var pending_rep: float = 0.0
var day_total_income: float = 0.0
var day_total_guests_served: int = 0
var day_total_guests_lost: int = 0
var day_service_qualities: Array = []

# History
var day_history: Array = []


func reset_daily() -> void:
	tick = 0
	paused = false
	game_speed = 1.0
	rush_hour_active = false
	current_phase = 0
	guest_queue.clear()
	pending_income = 0.0
	pending_expense = 0.0
	pending_rep = 0.0
	day_total_income = 0.0
	day_total_guests_served = 0
	day_total_guests_lost = 0
	day_service_qualities.clear()

	for t in tables:
		t.state = Table.State.FREE
		t.busy_timer = 0
		t.assigned_guest = null
		t.assigned_staff = null

	for s in staff_list:
		s.status = Staff.Status.READY
		s.stamina = s.max_stamina
		s.busy_timer = 0