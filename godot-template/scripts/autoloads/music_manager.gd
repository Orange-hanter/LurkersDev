extends Node
## Placeholder audio manager. In the pygame version this generates
## procedural chiptune music. Stubbed for future implementation.

var playing: bool = false
var muted: bool = false
var current_tune: String = ""

enum Tune { DAY_THEME, RUSH_HOUR, QUIET_HOUR }


func play_tune(tune_name: String) -> void:
	current_tune = tune_name
	playing = true


func stop() -> void:
	playing = false
	current_tune = ""


func set_muted(p_muted: bool) -> void:
	muted = p_muted