class_name DaySummary
extends BaseScreen
## End-of-day summary. Shows profit, rep change, service stats, equipment status.

func _ready() -> void:
	pass  # populate stats from GameState


func _on_next_day_pressed() -> void:
	GameState.day += 1
	GameState.reputation = int(GameState.reputation * 0.8)
	show_screen("res://scenes/day_setup.tscn")