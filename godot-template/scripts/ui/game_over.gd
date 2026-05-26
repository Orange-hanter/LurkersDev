class_name GameOver
extends BaseScreen
## Bankruptcy game-over screen. Shows final stats and return-to-menu button.


func _ready() -> void:
	pass  # populate final stats from GameState


func _on_return_pressed() -> void:
	# Reset GameState for a new game
	GameState.budget = GameConfig.STARTING_BUDGET
	GameState.reputation = 0
	GameState.day = 1
	GameState.staff_list.clear()
	GameState.guest_queue.clear()
	GameState.tables.clear()
	GameState.kitchen_equip = null
	GameState.hall_equip = null
	GameState.day_history.clear()
	show_screen("res://scenes/main_menu.tscn")