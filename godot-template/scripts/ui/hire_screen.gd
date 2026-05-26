class_name HireScreen
extends BaseScreen
## Staff hiring screen. Shows 3 candidate cards with name, skill, salary.


func _ready() -> void:
	pass  # generate and display 3 random candidates


func _on_hire_candidate(index: int) -> void:
	pass  # add candidate to GameState.staff_list, refresh candidates


func _on_back_pressed() -> void:
	if GameState.day == 1 and GameState.staff_list.is_empty():
		return  # cannot leave without staff on first day
	show_screen("res://scenes/game_screen.tscn")