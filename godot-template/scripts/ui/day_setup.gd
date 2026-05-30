class_name DaySetup
extends BaseScreen
## Day setup screen. Player chooses tick duration, table count, and capacity.


@onready var table_slider: HSlider = $CenterContainer/VBoxContainer/SettingsPanel/VBoxContainer/TableHBox/TableSlider
@onready var table_count_label: Label = $CenterContainer/VBoxContainer/SettingsPanel/VBoxContainer/TableHBox/TableCountLabel
@onready var tick_option: OptionButton = $CenterContainer/VBoxContainer/SettingsPanel/VBoxContainer/TickHBox/TickOptionButton
@onready var size_option: OptionButton = $CenterContainer/VBoxContainer/SettingsPanel/VBoxContainer/SizeHBox/SizeOptionButton
@onready var day_label: Label = $CenterContainer/VBoxContainer/DayLabel
@onready var settings_vbox: VBoxContainer = $CenterContainer/VBoxContainer/SettingsPanel/VBoxContainer

var _forecast_label: Label

func _ready() -> void:
	table_slider.value_changed.connect(_on_table_slider_changed)
	size_option.item_selected.connect(_on_size_changed)
	_build_forecast_label()
	_update_table_label(table_slider.value)
	day_label.text = "Day: " + str(GameState.day)
	_update_forecast()


func _on_table_slider_changed(value: float) -> void:
	_update_table_label(value)
	_update_forecast()


func _on_size_changed(_idx: int) -> void:
	_update_forecast()


func _update_table_label(value: float) -> void:
	table_count_label.text = str(int(value))


func _build_forecast_label() -> void:
	_forecast_label = Label.new()
	_forecast_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_forecast_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_forecast_label.set("theme_override_font_sizes/font_size", 18)
	_forecast_label.set("theme_override_colors/font_color", Color(0.66, 0.76, 0.88, 1))
	settings_vbox.add_child(_forecast_label)


func _update_forecast() -> void:
	if not is_instance_valid(_forecast_label):
		return
	var table_count := int(table_slider.value)
	var size_key := size_option.get_item_text(size_option.selected).to_lower()
	var seats := table_count * GameConfig.table_seat_count(size_key)
	var marketing: Dictionary = GameConfig.MARKETING_LEVELS[GameState.marketing_level]
	var fixed_cost := GameConfig.UTILITY_COST_PER_DAY + table_count * GameConfig.TABLE_RENT_PER_DAY + int(marketing["cost"])
	for staff in GameState.staff_list:
		fixed_cost += staff.daily_salary()
	_forecast_label.text = "Seats: " + str(seats) + " | Menu $" + str(GameState.menu_price) + " | Fixed costs $" + str(fixed_cost) + " | Demand " + str(marketing["label"])


func _on_confirm_pressed() -> void:
	GameState.table_count_chosen = int(table_slider.value)
	GameState.table_size_chosen = size_option.get_item_text(size_option.selected).to_lower()
	var tick_text := tick_option.get_item_text(tick_option.selected)
	GameState.tick_duration_minutes = int(tick_text.trim_suffix(" min"))
	GameState.tick_interval_chosen = GameConfig.DEFAULT_TICK_INTERVAL

	if GameState.day == 1 and not GameState.kitchen_equip:
		show_screen("res://scenes/shop_screen.tscn")
	elif GameState.day == 1 and GameState.staff_list.is_empty():
		show_screen("res://scenes/hire_screen.tscn")
	else:
		GameState.start_day()
		show_screen("res://scenes/game_screen.tscn")
