class_name BaseScreen
extends Control
## Base class for all screen nodes. Provides a show_screen() helper
## that disables the current screen and loads a new scene additively.

func _enter_tree() -> void:
	if DisplayServer.get_name() != "headless":
		DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_FULLSCREEN)
	call_deferred("_apply_screen_backdrop")


func _apply_screen_backdrop() -> void:
	var background := get_node_or_null("Background") as ColorRect
	if background:
		background.color = Color(0.16, 0.10, 0.065, 1.0)

## Disable this screen and queue a scene change.
## Scene paths are relative to res://scenes/
func show_screen(scene_path: String) -> void:
	process_mode = PROCESS_MODE_DISABLED
	visible = false
	get_tree().call_deferred("change_scene_to_file", scene_path)
