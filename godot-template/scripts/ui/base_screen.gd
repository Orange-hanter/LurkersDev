class_name BaseScreen
extends Control
## Base class for all screen nodes. Provides a show_screen() helper
## that disables the current screen and loads a new scene additively.

## Disable this screen and queue a scene change.
## Scene paths are relative to res://scenes/
func show_screen(scene_path: String) -> void:
	process_mode = PROCESS_MODE_DISABLED
	visible = false
	get_tree().call_deferred("change_scene_to_file", scene_path)

