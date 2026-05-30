class_name DaySummary
extends BaseScreen
## End-of-day summary with rich visual stats.

@onready var day_label: Label = $CenterContainer/VBoxContainer/DayLabel
@onready var profit_label: Label = $CenterContainer/VBoxContainer/StatsPanel/VBoxContainer/ProfitLabel
@onready var rep_label: Label = $CenterContainer/VBoxContainer/StatsPanel/VBoxContainer/RepLabel
@onready var served_label: Label = $CenterContainer/VBoxContainer/StatsPanel/VBoxContainer/ServedLabel
@onready var lost_label: Label = $CenterContainer/VBoxContainer/StatsPanel/VBoxContainer/LostLabel
@onready var quality_label: Label = $CenterContainer/VBoxContainer/StatsPanel/VBoxContainer/QualityLabel
@onready var equip_label: Label = $CenterContainer/VBoxContainer/StatsPanel/VBoxContainer/EquipLabel
@onready var stats_vbox: VBoxContainer = $CenterContainer/VBoxContainer/StatsPanel/VBoxContainer

var _strategy_label: Label
var _seats_label: Label

func _ready() -> void:
	_strategy_label = Label.new()
	_strategy_label.set("theme_override_font_sizes/font_size", 22)
	stats_vbox.add_child(_strategy_label)
	_seats_label = Label.new()
	_seats_label.set("theme_override_font_sizes/font_size", 22)
	stats_vbox.add_child(_seats_label)
	_populate_stats()

func _populate_stats() -> void:
	if GameState.day_history.is_empty():
		return
	var stats: Dictionary = GameState.day_history[-1]
	day_label.text = "Day " + str(stats.get("day", GameState.day))

	var profit: float = stats.get("profit", 0.0)
	profit_label.text = "Profit/Loss: " + ("+$" if profit >= 0 else "-$") + str(abs(int(profit)))
	profit_label.set("theme_override_colors/font_color", Color(0.3, 0.9, 0.4) if profit >= 0 else Color(0.9, 0.3, 0.3))

	var rep_change: int = stats.get("rep_change", 0)
	rep_label.text = "Rep Change: " + ("+" if rep_change >= 0 else "") + str(rep_change)
	rep_label.set("theme_override_colors/font_color", Color(0.3, 0.9, 0.4) if rep_change >= 0 else Color(0.9, 0.3, 0.3))

	served_label.text = "Guests Served: " + str(stats.get("guests_served", 0))
	lost_label.text = "Guests Lost: " + str(stats.get("guests_lost", 0))
	_seats_label.text = "Seats Sold: " + str(stats.get("seats_sold", 0))

	var avg_quality: float = stats.get("avg_quality", 0.0)
	quality_label.text = "Avg Quality: " + str(snapped(avg_quality, 0.1))

	var kitchen_status := "None"
	var hall_status := "None"
	if is_instance_valid(GameState.kitchen_equip):
		kitchen_status = str(int(GameState.kitchen_equip.durability)) + "/" + str(int(GameState.kitchen_equip.max_durability))
	if is_instance_valid(GameState.hall_equip):
		hall_status = str(int(GameState.hall_equip.durability)) + "/" + str(int(GameState.hall_equip.max_durability))
	equip_label.text = "Kitchen: " + kitchen_status + " | Hall: " + hall_status
	var marketing: Dictionary = GameConfig.MARKETING_LEVELS[int(stats.get("marketing_level", GameState.marketing_level))]
	_strategy_label.text = "Menu $" + str(stats.get("menu_price", GameState.menu_price)) + " | Decor " + str(stats.get("decor_level", GameState.decor_level)) + " | " + str(marketing["label"])

func _on_next_day_pressed() -> void:
	GameState.day += 1
	GameState.reputation = int(GameState.reputation * 0.8)
	show_screen("res://scenes/day_setup.tscn")
