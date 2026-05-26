class_name ShopScreen
extends BaseScreen
## Equipment shop. Buy/repair kitchen and front-of-house equipment.


@onready var warning_label: Label = $MarginContainer/VBoxContainer/WarningLabel


func _ready() -> void:
	pass  # populate tier cards from GameConfig.EQUIPMENT_TIERS
	_update_warning()


func _update_warning() -> void:
	warning_label.visible = GameState.day == 1 and not GameState.kitchen_equip


func _on_buy_kitchen(tier: int) -> void:
	pass  # purchase kitchen equipment at given tier


func _on_buy_hall(tier: int) -> void:
	pass  # purchase hall equipment at given tier


func _on_repair_kitchen() -> void:
	pass  # repair kitchen equipment


func _on_repair_hall() -> void:
	pass  # repair hall equipment


func _on_back_pressed() -> void:
	if GameState.day == 1 and not GameState.kitchen_equip:
		_update_warning()
		return
	show_screen("res://scenes/game_screen.tscn")