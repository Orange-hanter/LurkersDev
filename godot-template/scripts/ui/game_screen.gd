class_name GameScreen
extends BaseScreen
## Main gameplay screen. Shows table grid, guest queue, staff cards,
## equipment status bars, event log, and control buttons.

signal pending_action(action: String)

@onready var event_log: RichTextLabel = $HBoxContainer/CenterPanel/EventLog
@onready var phase_label: Label = $HBoxContainer/CenterPanel/BottomBar/PhaseLabel
@onready var table_grid: GridContainer = $HBoxContainer/TablePanel/TableGrid
@onready var guest_list: VBoxContainer = $HBoxContainer/RightPanel/GuestsSection/GuestList
@onready var staff_grid: HFlowContainer = $HBoxContainer/RightPanel/StaffSection/StaffGrid
@onready var kitchen_bar: ProgressBar = $HBoxContainer/RightPanel/EquipmentSection/EquipVBox/KitchenBar
@onready var hall_bar: ProgressBar = $HBoxContainer/RightPanel/EquipmentSection/EquipVBox/HallBar
@onready var budget_label: Label = $HBoxContainer/RightPanel/EquipmentSection/EquipVBox/BudgetLabel
@onready var rep_label: Label = $HBoxContainer/RightPanel/EquipmentSection/EquipVBox/RepLabel


func _ready() -> void:
	GameState.budget_changed.connect(_on_budget_changed)
	GameState.rep_changed.connect(_on_rep_changed)
	GameState.guest_queued.connect(_on_guest_queued)
	GameState.tick_advanced.connect(_on_tick_advanced)
	EventManager.event_triggered.connect(_on_event)


func log_event(message: String) -> void:
	event_log.add_text(message + "\n")


func _on_budget_changed(_new: int) -> void:
	budget_label.text = "Budget: $" + str(_new)


func _on_rep_changed(_new: int) -> void:
	rep_label.text = "Rep: " + str(_new)


func _on_guest_queued(_guest: Guest) -> void:
	pass  # will refresh guest list display


func _on_tick_advanced(tick: int) -> void:
	phase_label.text = "Tick: " + str(tick) + " / " + str(GameConfig.TOTAL_TICKS_PER_DAY)


func _on_event(event_type: String, _data: Dictionary) -> void:
	log_event("EVENT: " + event_type)


func _on_pause_pressed() -> void:
	GameState.paused = not GameState.paused


func _on_speed_up_pressed() -> void:
	GameState.game_speed = min(GameState.game_speed * 2.0, 8.0)


func _on_speed_down_pressed() -> void:
	GameState.game_speed = max(GameState.game_speed / 2.0, 0.25)


func _on_shop_pressed() -> void:
	pending_action.emit("shop")


func _on_hire_pressed() -> void:
	pending_action.emit("hire")


func _on_end_day_pressed() -> void:
	pending_action.emit("end_day")