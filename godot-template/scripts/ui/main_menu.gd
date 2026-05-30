class_name MainMenu
extends BaseScreen
## Main menu screen with animated prompt and rich visuals.

@onready var prompt_label: Label = $CenterContainer/VBoxContainer/PromptLabel

func _ready() -> void:
	pass

func _input(event: InputEvent) -> void:
	if event.is_action_pressed("ui_accept"):
		_start_game()

func _start_game() -> void:
	show_screen("res://scenes/day_setup.tscn")

func _on_blink_timer() -> void:
	prompt_label.visible = not prompt_label.visible
