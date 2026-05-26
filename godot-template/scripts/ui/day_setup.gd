class_name DaySetup
extends BaseScreen
## Day setup screen. Player chooses tick duration, table count, and capacity.


@onready var table_slider: HSlider = $CenterContainer/VBoxContainer/TableHBox/TableSlider
@onready var table_count_label: Label = $CenterContainer/VBoxContainer/TableHBox/TableCountLabel
@onready var tick_option: OptionButton = $CenterContainer/VBoxContainer/TickHBox/TickOptionButton
@onready var size_option: OptionButton = $CenterContainer/VBoxContainer/SizeHBox/SizeOptionButton


func _ready() -> void:
	table_slider.value_changed.connect(_on_table_slider_changed)
	_update_table_label(table_slider.value)


func _on_table_slider_changed(value: float) -> void:
	_update_table_label(value)


func _update_table_label(value: float) -> void:
	table_count_label.text = str(int(value))


func _on_confirm_pressed() -> void:
	GameState.table_count_chosen = int(table_slider.value)
	GameState.table_size_chosen = size_option.get_item_text(size_option.selected).to_lower()
	var tick_text := tick_option.get_item_text(tick_option.selected)
	GameState.tick_duration_minutes = int(tick_text.trim_suffix(" min"))
	GameState.tick_interval_chosen = GameState.tick_duration_minutes / 60.0 * GameConfig.TOTAL_TICKS_PER_DAY / 100.0 * 0.5

	if GameState.day == 1 and not GameState.kitchen_equip:
		show_screen("res://scenes/shop_screen.tscn")
	elif GameState.day == 1 and GameState.staff_list.is_empty():
		show_screen("res://scenes/hire_screen.tscn")
	else:
		show_screen("res://scenes/game_screen.tscn")