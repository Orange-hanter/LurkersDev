class_name GameScreen
extends BaseScreen
## Main gameplay screen with rich visual design.

@onready var day_title: Label = $HBoxContainer/LeftPanel/TopBar/DayTitle
@onready var phase_label: Label = $HBoxContainer/LeftPanel/TopBar/PhaseLabel
@onready var root_hbox: HBoxContainer = $HBoxContainer
@onready var background: ColorRect = $Background
@onready var left_panel: VBoxContainer = $HBoxContainer/LeftPanel
@onready var floor_host: VBoxContainer = $HBoxContainer/LeftPanel/TablesPanel/VBoxContainer
@onready var table_grid: GridContainer = $HBoxContainer/LeftPanel/TablesPanel/VBoxContainer/TableGrid
@onready var center_panel: VBoxContainer = $HBoxContainer/CenterPanel
@onready var right_panel: VBoxContainer = $HBoxContainer/RightPanel
@onready var guests_panel: PanelContainer = $HBoxContainer/RightPanel/GuestsPanel
@onready var staff_panel: PanelContainer = $HBoxContainer/RightPanel/StaffPanel
@onready var equip_panel: PanelContainer = $HBoxContainer/RightPanel/EquipPanel
@onready var guest_list: VBoxContainer = $HBoxContainer/RightPanel/GuestsPanel/VBoxContainer/GuestList
@onready var guest_header: Label = $HBoxContainer/RightPanel/GuestsPanel/VBoxContainer/GuestHeader
@onready var staff_grid: HFlowContainer = $HBoxContainer/RightPanel/StaffPanel/VBoxContainer/StaffGrid
@onready var staff_header: Label = $HBoxContainer/RightPanel/StaffPanel/VBoxContainer/StaffHeader
@onready var kitchen_bar: ProgressBar = $HBoxContainer/RightPanel/EquipPanel/EquipVBox/KitchenBar
@onready var hall_bar: ProgressBar = $HBoxContainer/RightPanel/EquipPanel/EquipVBox/HallBar
@onready var equip_vbox: VBoxContainer = $HBoxContainer/RightPanel/EquipPanel/EquipVBox
@onready var budget_label: Label = $HBoxContainer/RightPanel/EquipPanel/EquipVBox/BudgetLabel
@onready var rep_label: Label = $HBoxContainer/RightPanel/EquipPanel/EquipVBox/RepLabel
@onready var speed_label: Label = $HBoxContainer/LeftPanel/ControlsBar/SpeedLabel
@onready var event_log: RichTextLabel = $HBoxContainer/CenterPanel/LogPanel/VBoxContainer/EventLog

var _table_buttons: Array[Button] = []
var _floor_view: Control
var _cashflow_label: Label
var _strategy_label: Label
var _throughput_label: Label

func _ready() -> void:
	GameState.paused = false
	_configure_window_and_layout()
	_create_floor_view()
	_create_tycoon_metrics()
	GameState.budget_changed.connect(_on_budget_changed)
	GameState.rep_changed.connect(_on_rep_changed)
	GameState.guest_queued.connect(_on_guest_queued)
	GameState.guest_served.connect(_on_guest_served)
	GameState.guest_left.connect(_on_guest_left)
	GameState.tick_advanced.connect(_on_tick_advanced)
	GameState.event_occurred.connect(_on_event_occurred)
	GameState.tables_refreshed.connect(_refresh_tables)
	GameState.staff_refreshed.connect(_refresh_staff)
	GameState.day_started.connect(_on_day_started)
	GameState.day_ended.connect(_on_day_ended)
	GameState.bankruptcy.connect(_on_bankruptcy)

	day_title.text = "Day " + str(GameState.day)
	_on_budget_changed(GameState.budget)
	_on_rep_changed(GameState.reputation)
	_build_table_buttons()
	_refresh_tables()
	_refresh_staff()
	_refresh_guests()
	_refresh_equipment()
	_on_tick_advanced(GameState.tick)
	_update_speed_label()
	log_event("=== Day " + str(GameState.day) + " started ===")

func _configure_window_and_layout() -> void:
	if DisplayServer.get_name() != "headless":
		DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_FULLSCREEN)
	background.color = Color(0.12, 0.09, 0.06, 1.0)
	center_panel.visible = false
	root_hbox.add_theme_constant_override("separation", 10)
	left_panel.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	left_panel.size_flags_stretch_ratio = 1.0
	right_panel.custom_minimum_size = Vector2(270, 0)
	right_panel.size_flags_horizontal = Control.SIZE_SHRINK_END
	right_panel.add_theme_constant_override("separation", 10)
	_configure_sidebar()
	_compact_controls()

func _configure_sidebar() -> void:
	guests_panel.custom_minimum_size = Vector2(0, 126)
	staff_panel.custom_minimum_size = Vector2(0, 150)
	equip_panel.custom_minimum_size = Vector2(0, 238)
	guests_panel.size_flags_vertical = Control.SIZE_EXPAND_FILL
	staff_panel.size_flags_vertical = Control.SIZE_EXPAND_FILL
	equip_panel.size_flags_vertical = Control.SIZE_EXPAND_FILL
	guests_panel.size_flags_stretch_ratio = 0.65
	staff_panel.size_flags_stretch_ratio = 0.75
	equip_panel.size_flags_stretch_ratio = 1.15
	_make_label_compact(guest_header, 21)
	_make_label_compact(staff_header, 21)
	_make_label_compact(budget_label, 24)
	_make_label_compact(rep_label, 22)

func _make_label_compact(label: Label, font_size: int) -> void:
	label.custom_minimum_size = Vector2(0, 0)
	label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	label.set("theme_override_font_sizes/font_size", font_size)

func _compact_controls() -> void:
	var controls := $HBoxContainer/LeftPanel/ControlsBar
	controls.add_theme_constant_override("separation", 6)
	var pause_btn: Button = $HBoxContainer/LeftPanel/ControlsBar/PauseButton
	var shop_btn: Button = $HBoxContainer/LeftPanel/ControlsBar/ShopButton
	var hire_btn: Button = $HBoxContainer/LeftPanel/ControlsBar/HireButton
	var end_btn: Button = $HBoxContainer/LeftPanel/ControlsBar/EndDayButton
	pause_btn.text = "Pause"
	pause_btn.custom_minimum_size = Vector2(84, 42)
	shop_btn.text = "Shop"
	shop_btn.custom_minimum_size = Vector2(82, 42)
	hire_btn.text = "Hire"
	hire_btn.custom_minimum_size = Vector2(82, 42)
	end_btn.text = "End Day"
	end_btn.custom_minimum_size = Vector2(104, 42)

func _create_floor_view() -> void:
	table_grid.visible = false
	_floor_view = load("res://scripts/ui/restaurant_floor.gd").new()
	_floor_view.name = "RestaurantFloor"
	_floor_view.custom_minimum_size = Vector2(720, 560)
	_floor_view.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_floor_view.size_flags_vertical = Control.SIZE_EXPAND_FILL
	floor_host.add_child(_floor_view)
	floor_host.move_child(_floor_view, 1)

func _create_tycoon_metrics() -> void:
	_cashflow_label = Label.new()
	_make_label_compact(_cashflow_label, 15)
	equip_vbox.add_child(_cashflow_label)
	_strategy_label = Label.new()
	_make_label_compact(_strategy_label, 15)
	equip_vbox.add_child(_strategy_label)
	_throughput_label = Label.new()
	_make_label_compact(_throughput_label, 15)
	equip_vbox.add_child(_throughput_label)

func _on_day_started(day: int) -> void:
	day_title.text = "Day " + str(day)
	log_event("=== Day " + str(day) + " started ===")
	_build_table_buttons()
	_refresh_tables()
	_refresh_staff()
	_refresh_guests()
	_refresh_equipment()
	_on_tick_advanced(GameState.tick)

func log_event(message: String) -> void:
	if not is_instance_valid(event_log):
		return
	event_log.add_text(message + "\n")

func _on_budget_changed(new_value: int) -> void:
	budget_label.text = "Budget: $" + str(new_value)
	_refresh_tycoon_metrics()
	_budget_pulse()

func _on_rep_changed(new_value: int) -> void:
	rep_label.text = "Rep: " + str(new_value)
	_refresh_tycoon_metrics()
	_rep_pulse()

func _budget_pulse() -> void:
	var tween := create_tween()
	budget_label.modulate = Color(1.5, 1.5, 1.5, 1)
	tween.tween_property(budget_label, "modulate", Color.WHITE, 0.3)

func _rep_pulse() -> void:
	var tween := create_tween()
	rep_label.modulate = Color(1.5, 1.3, 1, 1)
	tween.tween_property(rep_label, "modulate", Color.WHITE, 0.3)

func _on_guest_queued(_guest: Guest) -> void:
	_refresh_guests()

func _on_guest_served(guest: Guest, quality: float, income: float) -> void:
	var success := quality >= guest.expectation
	var color_str := "[color=#55ff55]" if success else "[color=#ff5555]"
	var end_color := "[/color]"
	log_event(color_str + "Served " + guest.type_label() + " x" + str(guest.party_size) + " | Q: " + str(snapped(quality, 0.1)) + " | $" + str(int(income)) + end_color)
	_refresh_tables()
	_refresh_guests()

func _on_guest_left(guest: Guest) -> void:
	log_event("[color=#ff4444]LEFT: " + guest.type_label() + " (impatient)[/color]")
	_refresh_guests()

func _on_tick_advanced(tick: int) -> void:
	phase_label.text = "Tick: " + str(tick) + " / " + str(GameConfig.TOTAL_TICKS_PER_DAY)
	if tick > GameConfig.TOTAL_TICKS_PER_DAY * 0.8:
		phase_label.set("theme_override_colors/font_color", Color(0.9, 0.3, 0.3, 1))
	_refresh_tables()
	_refresh_staff()
	_refresh_equipment()
	_refresh_tycoon_metrics()

func _on_event_occurred(message: String) -> void:
	log_event("[color=#ffcc44]" + message + "[/color]")

func _on_pause_pressed() -> void:
	GameState.paused = not GameState.paused
	log_event("Paused: " + str(GameState.paused))

func _on_speed_up_pressed() -> void:
	GameState.game_speed = min(GameState.game_speed * 2.0, 8.0)
	_update_speed_label()

func _on_speed_down_pressed() -> void:
	GameState.game_speed = max(GameState.game_speed / 2.0, 0.25)
	_update_speed_label()

func _update_speed_label() -> void:
	speed_label.text = str(GameState.game_speed) + "x"

func _on_shop_pressed() -> void:
	GameState.paused = true
	show_screen("res://scenes/shop_screen.tscn")

func _on_hire_pressed() -> void:
	GameState.paused = true
	show_screen("res://scenes/hire_screen.tscn")

func _on_end_day_pressed() -> void:
	GameState.end_day()

func _on_day_ended(_stats: Dictionary) -> void:
	show_screen("res://scenes/day_summary.tscn")

func _on_bankruptcy() -> void:
	show_screen("res://scenes/game_over.tscn")

func _build_table_buttons() -> void:
	for btn in _table_buttons:
		if is_instance_valid(btn) and btn.get_parent():
			btn.get_parent().remove_child(btn)
			btn.queue_free()
	_table_buttons.clear()
	for i in range(GameState.tables.size()):
		var btn := Button.new()
		btn.custom_minimum_size = Vector2(90, 90)
		btn.pressed.connect(func() -> void: _on_table_clicked(i))
		btn.set("theme_override_font_sizes/font_size", 16)
		table_grid.add_child(btn)
		_table_buttons.append(btn)

func _refresh_tables() -> void:
	for i in range(min(_table_buttons.size(), GameState.tables.size())):
		var table := GameState.tables[i]
		var btn := _table_buttons[i]
		match table.state:
			Table.State.FREE:
				btn.text = "Table\n" + str(table.table_id) + "\n" + str(table.capacity) + " seats"
				btn.modulate = Color(0.5, 0.9, 0.5)
				btn.set("theme_override_colors/font_color", Color.WHITE)
			Table.State.OCCUPIED:
				var guest := table.assigned_guest
				var staff := table.assigned_staff
				var guest_name := guest.type_label() if guest else "?"
				var staff_name := staff.staff_name if staff else "?"
				btn.text = guest_name + "\n" + staff_name + "\n" + str(table.busy_timer) + "t"
				btn.modulate = Color(0.9, 0.5, 0.5)
				btn.set("theme_override_colors/font_color", Color.WHITE)

func _on_table_clicked(idx: int) -> void:
	if idx >= GameState.tables.size():
		return
	var table := GameState.tables[idx]
	log_event("Table " + str(table.table_id) + " | " + ("Free" if table.state == Table.State.FREE else "Occupied"))

func _refresh_guests() -> void:
	while guest_list.get_child_count() > 0:
		var child := guest_list.get_child(0)
		guest_list.remove_child(child)
		child.queue_free()

	guest_header.text = "Queue " + str(GameState.guest_queue.size())

	if GameState.guest_queue.is_empty():
		var empty := Label.new()
		empty.text = "No waiting parties"
		empty.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		empty.set("theme_override_font_sizes/font_size", 14)
		empty.set("theme_override_colors/font_color", Color(0.68, 0.64, 0.58, 1))
		guest_list.add_child(empty)
		return

	for guest in GameState.guest_queue:
		var hbox := HBoxContainer.new()
		hbox.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		hbox.add_theme_constant_override("separation", 6)
		var type_icon := ColorRect.new()
		type_icon.custom_minimum_size = Vector2(10, 18)
		type_icon.color = _guest_color(guest)
		type_icon.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		hbox.add_child(type_icon)

		var lbl := Label.new()
		lbl.text = _guest_short_label(guest)
		lbl.custom_minimum_size = Vector2(0, 0)
		lbl.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		lbl.set("theme_override_font_sizes/font_size", 14)
		lbl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		hbox.add_child(lbl)
		guest_list.add_child(hbox)

func _guest_short_label(guest: Guest) -> String:
	var label := guest.type_label()
	match guest.guest_type:
		Guest.GuestType.REGULAR:
			label = "Reg"
		Guest.GuestType.BUSINESS:
			label = "Biz"
		Guest.GuestType.VIP:
			label = "VIP"
		Guest.GuestType.CRITIC:
			label = "Critic"
	return label + " x" + str(guest.party_size) + "  " + str(guest.wait_timer) + "/" + str(guest.patience_ticks) + "  $" + str(int(guest.max_check))

func _guest_color(guest: Guest) -> Color:
	match guest.guest_type:
		Guest.GuestType.REGULAR:  return Color(0.7, 0.7, 0.7)
		Guest.GuestType.BUSINESS: return Color(0.3, 0.5, 0.9)
		Guest.GuestType.VIP:      return Color(1, 0.85, 0.3)
		Guest.GuestType.CRITIC:   return Color(0.9, 0.2, 0.2)
	return Color.WHITE

func _refresh_staff() -> void:
	while staff_grid.get_child_count() > 0:
		var child := staff_grid.get_child(0)
		staff_grid.remove_child(child)
		child.queue_free()

	staff_header.text = "Staff (" + str(GameState.staff_list.size()) + ")"

	for staff in GameState.staff_list:
		var card := VBoxContainer.new()
		card.size_flags_horizontal = Control.SIZE_EXPAND_FILL

		var name_lbl := Label.new()
		name_lbl.text = staff.staff_name
		name_lbl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		name_lbl.set("theme_override_font_sizes/font_size", 15)
		card.add_child(name_lbl)

		var status_lbl := Label.new()
		match staff.status:
			Staff.Status.READY:
				status_lbl.text = "Ready"
				status_lbl.modulate = Color(0.3, 0.9, 0.4)
			Staff.Status.BUSY:
				status_lbl.text = "Busy " + str(staff.busy_timer) + "t"
				status_lbl.modulate = Color(0.9, 0.4, 0.3)
			Staff.Status.RESTING:
				status_lbl.text = "Resting"
				status_lbl.modulate = Color(0.3, 0.5, 0.9)
		status_lbl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		status_lbl.set("theme_override_font_sizes/font_size", 13)
		card.add_child(status_lbl)

		var stamina_bar := ProgressBar.new()
		stamina_bar.max_value = 1.0
		stamina_bar.value = staff.stamina_fraction()
		stamina_bar.custom_minimum_size = Vector2(74, 12)
		stamina_bar.show_percentage = false
		var fill_style := _stamina_style(staff.stamina_fraction())
		stamina_bar.set("theme_override_styles/fill", fill_style)
		card.add_child(stamina_bar)

		staff_grid.add_child(card)

func _stamina_style(frac: float) -> StyleBoxFlat:
	var style := StyleBoxFlat.new()
	style.corner_radius_top_left = 6
	style.corner_radius_top_right = 6
	style.corner_radius_bottom_right = 6
	style.corner_radius_bottom_left = 6
	if frac > 0.6:
		style.bg_color = Color(0.25, 0.65, 0.35, 1)
	elif frac > 0.3:
		style.bg_color = Color(0.85, 0.75, 0.2, 1)
	else:
		style.bg_color = Color(0.8, 0.25, 0.25, 1)
	return style

func _refresh_equipment() -> void:
	if is_instance_valid(GameState.kitchen_equip):
		kitchen_bar.value = GameState.kitchen_equip.durability_fraction() * 100.0
		var k_frac := GameState.kitchen_equip.durability_fraction()
		kitchen_bar.set("theme_override_styles/fill", _durability_style(k_frac))
	else:
		kitchen_bar.value = 0.0

	if is_instance_valid(GameState.hall_equip):
		hall_bar.value = GameState.hall_equip.durability_fraction() * 100.0
		var h_frac := GameState.hall_equip.durability_fraction()
		hall_bar.set("theme_override_styles/fill", _durability_style(h_frac))
	else:
		hall_bar.value = 0.0
	_refresh_tycoon_metrics()

func _refresh_tycoon_metrics() -> void:
	if not is_instance_valid(_cashflow_label):
		return
	var projected_profit := int(GameState.pending_income - GameState.pending_expense)
	_cashflow_label.text = "Net " + ("+$" if projected_profit >= 0 else "-$") + str(abs(projected_profit)) + "  +" + str(int(GameState.pending_income)) + "/-" + str(int(GameState.pending_expense))
	_cashflow_label.set("theme_override_colors/font_color", Color(0.35, 0.9, 0.48) if projected_profit >= 0 else Color(0.95, 0.38, 0.32))
	var marketing: Dictionary = GameConfig.MARKETING_LEVELS[GameState.marketing_level]
	_strategy_label.text = "Menu $" + str(GameState.menu_price) + " | D" + str(GameState.decor_level) + " | " + _marketing_short(str(marketing["label"]))
	_throughput_label.text = str(GameState.day_total_guests_served) + " groups / " + str(GameState.day_total_seats_sold) + " seats"

func _marketing_short(label: String) -> String:
	match label:
		"Word of mouth":
			return "WoM"
		"Radio ads":
			return "Radio"
		"City campaign":
			return "City"
	return label

func _durability_style(frac: float) -> StyleBoxFlat:
	var style := StyleBoxFlat.new()
	style.corner_radius_top_left = 6
	style.corner_radius_top_right = 6
	style.corner_radius_bottom_right = 6
	style.corner_radius_bottom_left = 6
	if frac > 0.6:
		style.bg_color = Color(0.25, 0.65, 0.35, 1)
	elif frac > 0.3:
		style.bg_color = Color(0.85, 0.75, 0.2, 1)
	else:
		style.bg_color = Color(0.8, 0.25, 0.25, 1)
	return style

func _exit_tree() -> void:
	if GameState.budget_changed.is_connected(_on_budget_changed):
		GameState.budget_changed.disconnect(_on_budget_changed)
	if GameState.rep_changed.is_connected(_on_rep_changed):
		GameState.rep_changed.disconnect(_on_rep_changed)
	if GameState.guest_queued.is_connected(_on_guest_queued):
		GameState.guest_queued.disconnect(_on_guest_queued)
	if GameState.guest_served.is_connected(_on_guest_served):
		GameState.guest_served.disconnect(_on_guest_served)
	if GameState.guest_left.is_connected(_on_guest_left):
		GameState.guest_left.disconnect(_on_guest_left)
	if GameState.tick_advanced.is_connected(_on_tick_advanced):
		GameState.tick_advanced.disconnect(_on_tick_advanced)
	if GameState.event_occurred.is_connected(_on_event_occurred):
		GameState.event_occurred.disconnect(_on_event_occurred)
	if GameState.tables_refreshed.is_connected(_refresh_tables):
		GameState.tables_refreshed.disconnect(_refresh_tables)
	if GameState.staff_refreshed.is_connected(_refresh_staff):
		GameState.staff_refreshed.disconnect(_refresh_staff)
	if GameState.day_started.is_connected(_on_day_started):
		GameState.day_started.disconnect(_on_day_started)
	if GameState.day_ended.is_connected(_on_day_ended):
		GameState.day_ended.disconnect(_on_day_ended)
	if GameState.bankruptcy.is_connected(_on_bankruptcy):
		GameState.bankruptcy.disconnect(_on_bankruptcy)

func _input(event: InputEvent) -> void:
	if event.is_action_pressed("pause"):
		_on_pause_pressed()
	elif event.is_action_pressed("speed_up"):
		_on_speed_up_pressed()
	elif event.is_action_pressed("speed_down"):
		_on_speed_down_pressed()
	elif event.is_action_pressed("shop"):
		_on_shop_pressed()
	elif event.is_action_pressed("hire"):
		_on_hire_pressed()
	elif event.is_action_pressed("end_day"):
		_on_end_day_pressed()
