class_name MainMenu
extends BaseScreen
## Main menu screen. Press ENTER/SPACE to start the game.


func _ready() -> void:
	# Connect to ui_accept action (Enter / Space)
	pass


func _input(event: InputEvent) -> void:
	if event.is_action_pressed("ui_accept"):
		_start_game()


func _start_game() -> void:
	show_screen("res://scenes/day_setup.tscn")