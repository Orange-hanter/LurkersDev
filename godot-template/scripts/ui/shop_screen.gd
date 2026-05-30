class_name ShopScreen
extends BaseScreen
## Responsive tycoon shop screen. Built in code so the layout can adapt
## to fullscreen, windowed, and smaller laptop viewports.

var _budget_label: Label
var _warning_label: Label
var _fixed_cost_label: Label
var _menu_price_label: Label
var _price_effect_label: Label
var _marketing_option: OptionButton
var _decor_label: Label
var _decor_button: Button
var _strategy_grid: GridContainer
var _status_grid: GridContainer
var _equipment_grid: GridContainer
var _kitchen_status_label: Label
var _hall_status_label: Label
var _repair_kitchen_button: Button
var _repair_hall_button: Button
var _equipment_buttons: Array = []


func _ready() -> void:
	_clear_legacy_scene()
	_build_layout()
	_connect_signals()
	_refresh_all()
	queue_redraw()


func _exit_tree() -> void:
	if GameState.budget_changed.is_connected(_on_budget_changed):
		GameState.budget_changed.disconnect(_on_budget_changed)
	if get_viewport().size_changed.is_connected(_on_viewport_resized):
		get_viewport().size_changed.disconnect(_on_viewport_resized)


func _draw() -> void:
	var rect := Rect2(Vector2.ZERO, size)
	draw_rect(rect, Color(0.18, 0.10, 0.055, 1), true)
	draw_rect(Rect2(Vector2.ZERO, Vector2(rect.size.x, 96.0)), Color(0.33, 0.19, 0.11, 1), true)
	for x in range(0, int(rect.size.x), 96):
		draw_rect(Rect2(Vector2(float(x), 96.0), Vector2(46.0, rect.size.y - 96.0)), Color(0.24, 0.13, 0.07, 0.12), true)
	for i in range(9):
		var shelf := Rect2(Vector2(rect.size.x - 210.0 + i * 14.0, 22.0 + sin(float(i)) * 5.0), Vector2(8.0, 40.0))
		draw_rect(shelf, Color(0.84, 0.56, 0.28, 0.28), true)


func _clear_legacy_scene() -> void:
	for child in get_children():
		remove_child(child)
		child.queue_free()


func _connect_signals() -> void:
	if not GameState.budget_changed.is_connected(_on_budget_changed):
		GameState.budget_changed.connect(_on_budget_changed)
	if not get_viewport().size_changed.is_connected(_on_viewport_resized):
		get_viewport().size_changed.connect(_on_viewport_resized)


func _build_layout() -> void:
	var margin := MarginContainer.new()
	margin.name = "ShopLayout"
	margin.set_anchors_preset(Control.PRESET_FULL_RECT)
	margin.add_theme_constant_override("margin_left", 24)
	margin.add_theme_constant_override("margin_top", 18)
	margin.add_theme_constant_override("margin_right", 24)
	margin.add_theme_constant_override("margin_bottom", 18)
	add_child(margin)

	var root := VBoxContainer.new()
	root.add_theme_constant_override("separation", 14)
	margin.add_child(root)

	root.add_child(_build_header())

	_warning_label = Label.new()
	_warning_label.text = "Buy kitchen equipment before opening day one."
	_warning_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_warning_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_warning_label.set("theme_override_font_sizes/font_size", 16)
	_warning_label.set("theme_override_colors/font_color", Color(1.0, 0.55, 0.34, 1))
	root.add_child(_warning_label)

	var scroll := ScrollContainer.new()
	scroll.name = "ShopScroll"
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	scroll.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	root.add_child(scroll)

	var content := VBoxContainer.new()
	content.name = "ShopContent"
	content.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	content.add_theme_constant_override("separation", 14)
	scroll.add_child(content)

	content.add_child(_build_strategy_row())
	content.add_child(_build_status_row())
	content.add_child(_build_equipment_section())
	content.add_child(_build_footer())


func _build_header() -> Control:
	var panel := PanelContainer.new()
	panel.set("theme_override_styles/panel", _panel_style(Color(0.24, 0.13, 0.075, 0.92), Color(0.86, 0.55, 0.28, 0.82), 8))
	var hbox := HBoxContainer.new()
	hbox.add_theme_constant_override("separation", 14)
	panel.add_child(hbox)

	var title_box := VBoxContainer.new()
	title_box.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	title_box.add_theme_constant_override("separation", 0)
	hbox.add_child(title_box)

	var title := Label.new()
	title.text = "Restaurant Workshop"
	title.set("theme_override_font_sizes/font_size", 30)
	title.set("theme_override_colors/font_color", Color(1.0, 0.86, 0.56, 1))
	title_box.add_child(title)

	var subtitle := Label.new()
	subtitle.text = "Tune demand, comfort, and production before the next shift."
	subtitle.set("theme_override_font_sizes/font_size", 15)
	subtitle.set("theme_override_colors/font_color", Color(0.86, 0.73, 0.58, 1))
	subtitle.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	title_box.add_child(subtitle)

	_budget_label = Label.new()
	_budget_label.custom_minimum_size = Vector2(170, 0)
	_budget_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	_budget_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	_budget_label.set("theme_override_font_sizes/font_size", 25)
	_budget_label.set("theme_override_colors/font_color", Color(0.48, 0.95, 0.55, 1))
	hbox.add_child(_budget_label)
	return panel


func _build_strategy_row() -> Control:
	var grid := GridContainer.new()
	grid.name = "StrategyGrid"
	grid.columns = 3
	grid.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	grid.add_theme_constant_override("h_separation", 12)
	grid.add_theme_constant_override("v_separation", 12)
	_strategy_grid = grid

	grid.add_child(_build_menu_panel())
	grid.add_child(_build_marketing_panel())
	grid.add_child(_build_decor_panel())
	return grid


func _build_menu_panel() -> Control:
	var panel := _section_panel("Menu Price", "Higher checks make money faster, but overpriced meals reduce service quality.")
	var box := panel.get_child(0) as VBoxContainer

	var stepper := HBoxContainer.new()
	stepper.alignment = BoxContainer.ALIGNMENT_CENTER
	stepper.add_theme_constant_override("separation", 8)
	var down := _small_button("-")
	down.pressed.connect(_on_menu_price_down)
	stepper.add_child(down)
	_menu_price_label = Label.new()
	_menu_price_label.custom_minimum_size = Vector2(170, 0)
	_menu_price_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_menu_price_label.set("theme_override_font_sizes/font_size", 24)
	_menu_price_label.set("theme_override_colors/font_color", Color(1.0, 0.82, 0.35, 1))
	stepper.add_child(_menu_price_label)
	var up := _small_button("+")
	up.pressed.connect(_on_menu_price_up)
	stepper.add_child(up)
	box.add_child(stepper)

	_price_effect_label = Label.new()
	_price_effect_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_price_effect_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_price_effect_label.set("theme_override_font_sizes/font_size", 14)
	_price_effect_label.set("theme_override_colors/font_color", Color(0.88, 0.76, 0.62, 1))
	box.add_child(_price_effect_label)
	return panel


func _build_marketing_panel() -> Control:
	var panel := _section_panel("Demand", "Marketing brings more parties, increases queue pressure, and raises daily fixed costs.")
	var box := panel.get_child(0) as VBoxContainer
	_marketing_option = OptionButton.new()
	_marketing_option.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	for level in GameConfig.MARKETING_LEVELS.keys():
		var info: Dictionary = GameConfig.MARKETING_LEVELS[level]
		_marketing_option.add_item(str(info["label"]) + "  $" + str(info["cost"]) + "/day", int(level))
	_marketing_option.item_selected.connect(_on_marketing_selected)
	box.add_child(_marketing_option)

	_fixed_cost_label = Label.new()
	_fixed_cost_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_fixed_cost_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_fixed_cost_label.set("theme_override_font_sizes/font_size", 14)
	_fixed_cost_label.set("theme_override_colors/font_color", Color(0.88, 0.76, 0.62, 1))
	box.add_child(_fixed_cost_label)
	return panel


func _build_decor_panel() -> Control:
	var panel := _section_panel("Atmosphere", "Decor improves patience and softens the pain of waiting during rushes.")
	var box := panel.get_child(0) as VBoxContainer
	_decor_label = Label.new()
	_decor_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_decor_label.set("theme_override_font_sizes/font_size", 22)
	_decor_label.set("theme_override_colors/font_color", Color(1.0, 0.82, 0.35, 1))
	box.add_child(_decor_label)

	_decor_button = Button.new()
	_decor_button.custom_minimum_size = Vector2(0, 40)
	_decor_button.pressed.connect(_on_upgrade_decor)
	box.add_child(_decor_button)
	return panel


func _build_status_row() -> Control:
	var grid := GridContainer.new()
	grid.columns = 2
	grid.add_theme_constant_override("h_separation", 12)
	grid.add_theme_constant_override("v_separation", 12)
	grid.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_status_grid = grid
	grid.add_child(_build_status_panel("Kitchen Line", true))
	grid.add_child(_build_status_panel("Dining Room", false))
	return grid


func _build_status_panel(title: String, kitchen: bool) -> Control:
	var panel := _section_panel(title, "Current station condition and repair action.")
	var box := panel.get_child(0) as VBoxContainer
	var status := Label.new()
	status.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	status.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	status.set("theme_override_font_sizes/font_size", 16)
	box.add_child(status)

	var repair := Button.new()
	repair.custom_minimum_size = Vector2(0, 40)
	box.add_child(repair)

	if kitchen:
		_kitchen_status_label = status
		_repair_kitchen_button = repair
		repair.pressed.connect(_on_repair_kitchen)
	else:
		_hall_status_label = status
		_repair_hall_button = repair
		repair.pressed.connect(_on_repair_hall)
	return panel


func _build_equipment_section() -> Control:
	var panel := PanelContainer.new()
	panel.set("theme_override_styles/panel", _panel_style(Color(0.21, 0.12, 0.075, 0.9), Color(0.63, 0.38, 0.20, 0.82), 8))
	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", 10)
	panel.add_child(box)

	var header := HBoxContainer.new()
	header.add_theme_constant_override("separation", 12)
	box.add_child(header)
	var title := Label.new()
	title.text = "Equipment Market"
	title.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	title.set("theme_override_font_sizes/font_size", 25)
	title.set("theme_override_colors/font_color", Color(1.0, 0.86, 0.56, 1))
	header.add_child(title)
	var note := Label.new()
	note.text = "Kitchen affects cooking quality. Hall affects guest experience."
	note.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	note.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	note.set("theme_override_font_sizes/font_size", 14)
	note.set("theme_override_colors/font_color", Color(0.83, 0.70, 0.55, 1))
	header.add_child(note)

	_equipment_grid = GridContainer.new()
	_equipment_grid.columns = 3
	_equipment_grid.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_equipment_grid.add_theme_constant_override("h_separation", 10)
	_equipment_grid.add_theme_constant_override("v_separation", 10)
	box.add_child(_equipment_grid)
	_build_equipment_cards()
	return panel


func _build_equipment_cards() -> void:
	_equipment_buttons.clear()
	for kind in ["Kitchen", "Hall"]:
		for i in range(3):
			var tier := i
			var panel := _equipment_card(kind, tier)
			_equipment_grid.add_child(panel)


func _equipment_card(kind: String, tier: int) -> Control:
	var info: Dictionary = GameConfig.EQUIPMENT_TIERS[tier]
	var panel := PanelContainer.new()
	panel.custom_minimum_size = Vector2(250, 178)
	panel.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	panel.set("theme_override_styles/panel", _panel_style(_tier_color(tier), Color(0.88, 0.56, 0.30, 0.65), 7))
	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", 7)
	panel.add_child(box)

	var top := HBoxContainer.new()
	box.add_child(top)
	var label := Label.new()
	label.text = kind
	label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	label.set("theme_override_font_sizes/font_size", 15)
	label.set("theme_override_colors/font_color", Color(0.95, 0.80, 0.58, 1))
	top.add_child(label)
	var tier_label := Label.new()
	tier_label.text = str(info["label"])
	tier_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	tier_label.set("theme_override_font_sizes/font_size", 17)
	tier_label.set("theme_override_colors/font_color", Color(1.0, 0.92, 0.76, 1))
	top.add_child(tier_label)

	var icon := Label.new()
	icon.text = _equipment_icon(kind, tier)
	icon.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	icon.set("theme_override_font_sizes/font_size", 30)
	icon.set("theme_override_colors/font_color", Color(1.0, 0.78, 0.34, 1))
	box.add_child(icon)

	var stats := Label.new()
	stats.text = "$" + str(info["price"]) + "   Quality +" + str(info["quality"]) + "   Durability " + str(info["max_durability"])
	stats.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	stats.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	stats.set("theme_override_font_sizes/font_size", 14)
	stats.set("theme_override_colors/font_color", Color(0.88, 0.78, 0.66, 1))
	box.add_child(stats)

	var impact := Label.new()
	impact.text = _equipment_impact(kind, tier)
	impact.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	impact.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	impact.set("theme_override_font_sizes/font_size", 13)
	impact.set("theme_override_colors/font_color", Color(0.73, 0.86, 0.70, 1))
	box.add_child(impact)

	var button := Button.new()
	button.text = "Buy"
	button.custom_minimum_size = Vector2(0, 38)
	button.pressed.connect(func() -> void:
		_on_buy_equipment(kind, tier)
	)
	box.add_child(button)
	_equipment_buttons.append({"button": button, "kind": kind, "tier": tier})
	return panel


func _build_footer() -> Control:
	var row := HBoxContainer.new()
	row.alignment = BoxContainer.ALIGNMENT_END
	var back := Button.new()
	back.text = "Back to floor"
	back.custom_minimum_size = Vector2(170, 44)
	back.pressed.connect(_on_back_pressed)
	row.add_child(back)
	return row


func _section_panel(title: String, description: String) -> PanelContainer:
	var panel := PanelContainer.new()
	panel.custom_minimum_size = Vector2(250, 132)
	panel.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	panel.set("theme_override_styles/panel", _panel_style(Color(0.25, 0.15, 0.09, 0.92), Color(0.70, 0.42, 0.22, 0.75), 8))
	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", 8)
	panel.add_child(box)

	var title_label := Label.new()
	title_label.text = title
	title_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	title_label.set("theme_override_font_sizes/font_size", 20)
	title_label.set("theme_override_colors/font_color", Color(1.0, 0.85, 0.56, 1))
	box.add_child(title_label)

	var desc := Label.new()
	desc.text = description
	desc.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	desc.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	desc.set("theme_override_font_sizes/font_size", 13)
	desc.set("theme_override_colors/font_color", Color(0.82, 0.70, 0.57, 1))
	box.add_child(desc)
	return panel


func _small_button(text: String) -> Button:
	var button := Button.new()
	button.text = text
	button.custom_minimum_size = Vector2(42, 38)
	button.set("theme_override_font_sizes/font_size", 20)
	return button


func _panel_style(bg: Color, border: Color, radius: int) -> StyleBoxFlat:
	var style := StyleBoxFlat.new()
	style.bg_color = bg
	style.border_color = border
	style.border_width_left = 2
	style.border_width_top = 2
	style.border_width_right = 2
	style.border_width_bottom = 2
	style.corner_radius_top_left = radius
	style.corner_radius_top_right = radius
	style.corner_radius_bottom_right = radius
	style.corner_radius_bottom_left = radius
	style.content_margin_left = 14
	style.content_margin_top = 12
	style.content_margin_right = 14
	style.content_margin_bottom = 12
	style.shadow_color = Color(0, 0, 0, 0.28)
	style.shadow_size = 4
	return style


func _tier_color(tier: int) -> Color:
	match tier:
		0:
			return Color(0.20, 0.13, 0.09, 0.94)
		1:
			return Color(0.18, 0.20, 0.13, 0.94)
		2:
			return Color(0.25, 0.15, 0.08, 0.96)
	return Color(0.20, 0.13, 0.09, 0.94)


func _equipment_icon(kind: String, tier: int) -> String:
	if kind == "Kitchen":
		return ["Stove I", "Chef Line", "Pro Range"][tier]
	return ["Seats I", "Warm Hall", "Fine Room"][tier]


func _equipment_impact(kind: String, tier: int) -> String:
	var quality: int = GameConfig.EQUIPMENT_TIERS[tier]["quality"]
	if kind == "Kitchen":
		return "Boosts food quality and speeds service decisions by +" + str(quality)
	return "Boosts hall comfort and keeps guests happier by +" + str(quality)


func _refresh_all() -> void:
	_refresh_budget()
	_refresh_warning()
	_refresh_strategy()
	_refresh_status()
	_refresh_equipment_buttons()
	_update_responsive_columns()


func _refresh_budget() -> void:
	if is_instance_valid(_budget_label):
		_budget_label.text = "$" + str(GameState.budget)


func _refresh_warning() -> void:
	if not is_instance_valid(_warning_label):
		return
	_warning_label.visible = GameState.day == 1 and not GameState.kitchen_equip


func _refresh_strategy() -> void:
	if not is_instance_valid(_menu_price_label):
		return
	_menu_price_label.text = "$" + str(GameState.menu_price)
	var average_check := GameState.menu_price * 3
	_price_effect_label.text = "Typical 3-seat check: $" + str(average_check) + " | Min $" + str(GameConfig.MIN_MENU_PRICE) + " / Max $" + str(GameConfig.MAX_MENU_PRICE)
	var marketing: Dictionary = GameConfig.MARKETING_LEVELS[GameState.marketing_level]
	_fixed_cost_label.text = "Fixed costs: $" + str(GameState.daily_cost_forecast()) + " | Demand x" + str(marketing["demand_mult"])
	_marketing_option.select(GameState.marketing_level)
	_decor_label.text = str(GameState.decor_level) + " / " + str(GameConfig.DECOR_MAX_LEVEL)
	if GameState.decor_level >= GameConfig.DECOR_MAX_LEVEL:
		_decor_button.text = "Atmosphere maxed"
		_decor_button.disabled = true
	else:
		_decor_button.text = "Upgrade for $" + str(GameState.upgrade_decor_cost())
		_decor_button.disabled = not GameState.can_upgrade_decor()


func _refresh_status() -> void:
	_set_equipment_status(_kitchen_status_label, _repair_kitchen_button, GameState.kitchen_equip, "No kitchen line yet")
	_set_equipment_status(_hall_status_label, _repair_hall_button, GameState.hall_equip, "No dining room kit yet")


func _set_equipment_status(label: Label, button: Button, equip: Equipment, empty_text: String) -> void:
	if not is_instance_valid(label) or not is_instance_valid(button):
		return
	if is_instance_valid(equip):
		label.text = equip.label + " | " + str(int(equip.durability)) + "/" + str(int(equip.max_durability)) + " durability"
		button.text = "Repair $" + str(GameConfig.REPAIR_COST)
		button.disabled = equip.durability >= equip.max_durability or GameState.budget < GameConfig.REPAIR_COST
	else:
		label.text = empty_text
		button.text = "Nothing to repair"
		button.disabled = true


func _refresh_equipment_buttons() -> void:
	for entry in _equipment_buttons:
		var button: Button = entry["button"]
		var tier: int = entry["tier"]
		var info: Dictionary = GameConfig.EQUIPMENT_TIERS[tier]
		button.disabled = GameState.budget < int(info["price"])
		button.text = "Buy $" + str(info["price"])


func _update_responsive_columns() -> void:
	var width := get_viewport_rect().size.x
	if is_instance_valid(_strategy_grid):
		if width < 920.0:
			_strategy_grid.columns = 1
		elif width < 1240.0:
			_strategy_grid.columns = 2
		else:
			_strategy_grid.columns = 3
	if is_instance_valid(_status_grid):
		_status_grid.columns = 1 if width < 920.0 else 2
	if not is_instance_valid(_equipment_grid):
		return
	if width < 860.0:
		_equipment_grid.columns = 1
	elif width < 1220.0:
		_equipment_grid.columns = 2
	else:
		_equipment_grid.columns = 3


func _on_budget_changed(_new: int) -> void:
	_refresh_all()


func _on_viewport_resized() -> void:
	_update_responsive_columns()
	queue_redraw()


func _on_menu_price_down() -> void:
	GameState.set_menu_price(GameState.menu_price - 4)
	_refresh_strategy()


func _on_menu_price_up() -> void:
	GameState.set_menu_price(GameState.menu_price + 4)
	_refresh_strategy()


func _on_marketing_selected(index: int) -> void:
	GameState.set_marketing_level(index)
	_refresh_strategy()


func _on_upgrade_decor() -> void:
	if GameState.upgrade_decor():
		log_event("Decor upgraded to level " + str(GameState.decor_level))
	_refresh_all()


func _on_buy_equipment(kind: String, tier: int) -> void:
	var info: Dictionary = GameConfig.EQUIPMENT_TIERS[tier]
	if not GameState.spend_budget(int(info["price"])):
		log_event("Not enough budget for " + kind + " " + str(info["label"]))
		return
	if kind == "Kitchen":
		GameState.kitchen_equip = Equipment.create(tier, "Kitchen")
	else:
		GameState.hall_equip = Equipment.create(tier, "Hall")
	log_event("Purchased " + kind + " " + str(info["label"]))
	_refresh_all()


func _on_buy_kitchen(tier: int) -> void:
	_on_buy_equipment("Kitchen", tier)


func _on_buy_hall(tier: int) -> void:
	_on_buy_equipment("Hall", tier)


func _on_repair_kitchen() -> void:
	_repair_equipment(GameState.kitchen_equip, "Kitchen")


func _on_repair_hall() -> void:
	_repair_equipment(GameState.hall_equip, "Hall")


func _repair_equipment(equip: Equipment, label: String) -> void:
	if not is_instance_valid(equip):
		log_event("No " + label + " equipment to repair")
		return
	if not GameState.spend_budget(GameConfig.REPAIR_COST):
		log_event("Not enough budget for repair")
		return
	equip.durability = minf(equip.max_durability, equip.durability + GameConfig.REPAIR_AMOUNT)
	log_event("Repaired " + label)
	_refresh_all()


func _on_back_pressed() -> void:
	if GameState.day == 1 and not GameState.kitchen_equip:
		_refresh_warning()
		return
	if GameState.day == 1 and GameState.staff_list.is_empty():
		show_screen("res://scenes/hire_screen.tscn")
		return
	show_screen("res://scenes/game_screen.tscn")


func log_event(message: String) -> void:
	print("[Shop] ", message)
