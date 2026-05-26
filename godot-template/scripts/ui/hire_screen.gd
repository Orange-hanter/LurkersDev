class_name HireScreen
extends BaseScreen
## Staff hiring screen. Shows 3 candidate cards with name, skill, salary.


@onready var warning_label: Label = $CenterContainer/VBoxContainer/WarningLabel


func _ready() -> void:
	pass  # generate and display 3 random candidates
	_update_warning()


func _update_warning() -> void:
	warning_label.visible = GameState.day == 1 and GameState.staff_list.is_empty()


func _on_hire_candidate(index: int) -> void:
	pass  # add candidate to GameState.staff_list, refresh candidates


func _on_back_pressed() -> void:
	if GameState.day == 1 and GameState.staff_list.is_empty():
		_update_warning()
		return
	show_screen("res://scenes/game_screen.tscn")


func _on_hire_candidate_1() -> void:
	pass  # hire candidate index 0


func _on_hire_candidate_2() -> void:
	pass  # hire candidate index 1


func _on_hire_candidate_3() -> void:
	pass  # hire candidate index 2