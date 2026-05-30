class_name GameOver
extends BaseScreen
## Bankruptcy game-over screen with rich visuals.

@onready var survived_label: Label = $CenterContainer/VBoxContainer/StatsPanel/VBoxContainer/SurvivedLabel
@onready var budget_label: Label = $CenterContainer/VBoxContainer/StatsPanel/VBoxContainer/BudgetLabel
@onready var rep_label: Label = $CenterContainer/VBoxContainer/StatsPanel/VBoxContainer/RepLabel

func _ready() -> void:
	_populate_final_stats()

func _populate_final_stats() -> void:
	survived_label.text = "Survived: " + str(GameState.day) + " days"
	budget_label.text = "Final Budget: $" + str(GameState.budget)
	rep_label.text = "Final Rep: " + str(GameState.reputation)

func _on_return_pressed() -> void:
	GameState.budget = GameConfig.STARTING_BUDGET
	GameState.reputation = 0
	GameState.day = 1
	GameState.staff_list.clear()
	GameState.guest_queue.clear()
	GameState.tables.clear()
	GameState.kitchen_equip = null
	GameState.hall_equip = null
	GameState.menu_price = GameConfig.BASE_MENU_PRICE
	GameState.marketing_level = 0
	GameState.decor_level = 0
	GameState.day_history.clear()
	GameState.reset_daily()
	show_screen("res://scenes/main_menu.tscn")
