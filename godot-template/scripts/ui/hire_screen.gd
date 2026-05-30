class_name HireScreen
extends BaseScreen
## Staff hiring screen with rich card-based design.

@onready var warning_label: Label = $CenterContainer/VBoxContainer/WarningLabel
@onready var budget_label: Label = $CenterContainer/VBoxContainer/BudgetLabel
@onready var candidate1_name: Label = $CenterContainer/VBoxContainer/CandidatesHBox/Candidate1Panel/VBoxContainer/Candidate1Name
@onready var candidate1_skill: Label = $CenterContainer/VBoxContainer/CandidatesHBox/Candidate1Panel/VBoxContainer/Candidate1Skill
@onready var candidate1_stamina: Label = $CenterContainer/VBoxContainer/CandidatesHBox/Candidate1Panel/VBoxContainer/Candidate1Stamina
@onready var candidate1_salary: Label = $CenterContainer/VBoxContainer/CandidatesHBox/Candidate1Panel/VBoxContainer/Candidate1Salary
@onready var candidate1_btn: Button = $CenterContainer/VBoxContainer/CandidatesHBox/Candidate1Panel/VBoxContainer/Candidate1HireBtn

@onready var candidate2_name: Label = $CenterContainer/VBoxContainer/CandidatesHBox/Candidate2Panel/VBoxContainer/Candidate2Name
@onready var candidate2_skill: Label = $CenterContainer/VBoxContainer/CandidatesHBox/Candidate2Panel/VBoxContainer/Candidate2Skill
@onready var candidate2_stamina: Label = $CenterContainer/VBoxContainer/CandidatesHBox/Candidate2Panel/VBoxContainer/Candidate2Stamina
@onready var candidate2_salary: Label = $CenterContainer/VBoxContainer/CandidatesHBox/Candidate2Panel/VBoxContainer/Candidate2Salary
@onready var candidate2_btn: Button = $CenterContainer/VBoxContainer/CandidatesHBox/Candidate2Panel/VBoxContainer/Candidate2HireBtn

@onready var candidate3_name: Label = $CenterContainer/VBoxContainer/CandidatesHBox/Candidate3Panel/VBoxContainer/Candidate3Name
@onready var candidate3_skill: Label = $CenterContainer/VBoxContainer/CandidatesHBox/Candidate3Panel/VBoxContainer/Candidate3Skill
@onready var candidate3_stamina: Label = $CenterContainer/VBoxContainer/CandidatesHBox/Candidate3Panel/VBoxContainer/Candidate3Stamina
@onready var candidate3_salary: Label = $CenterContainer/VBoxContainer/CandidatesHBox/Candidate3Panel/VBoxContainer/Candidate3Salary
@onready var candidate3_btn: Button = $CenterContainer/VBoxContainer/CandidatesHBox/Candidate3Panel/VBoxContainer/Candidate3HireBtn

var candidates: Array[Staff] = []

func _ready() -> void:
	GameState.budget_changed.connect(_on_budget_changed)
	_generate_candidates()
	_update_ui()
	_update_warning()

func _exit_tree() -> void:
	if GameState.budget_changed.is_connected(_on_budget_changed):
		GameState.budget_changed.disconnect(_on_budget_changed)

func _generate_candidates() -> void:
	candidates.clear()
	for i in range(3):
		candidates.append(Staff.generate_candidate())

func _update_ui() -> void:
	budget_label.text = "Budget: $" + str(GameState.budget)
	_update_card(candidate1_name, candidate1_skill, candidate1_stamina, candidate1_salary, candidate1_btn, 0)
	_update_card(candidate2_name, candidate2_skill, candidate2_stamina, candidate2_salary, candidate2_btn, 1)
	_update_card(candidate3_name, candidate3_skill, candidate3_stamina, candidate3_salary, candidate3_btn, 2)

func _update_card(name_label: Label, skill_label: Label, stamina_label: Label, salary_label: Label, btn: Button, idx: int) -> void:
	if idx >= candidates.size():
		return
	var candidate := candidates[idx]
	name_label.text = candidate.staff_name
	skill_label.text = "Skill: " + str(candidate.skill) + "/10"
	stamina_label.text = "Stamina: " + str(int(candidate.max_stamina))
	salary_label.text = "Salary: $" + str(candidate.daily_salary()) + "/day"
	btn.disabled = GameState.budget < candidate.daily_salary()

func _on_budget_changed(_new: int) -> void:
	_update_ui()

func _update_warning() -> void:
	warning_label.visible = GameState.day == 1 and GameState.staff_list.is_empty()

func _on_hire_candidate(index: int) -> void:
	if index >= candidates.size():
		return
	var candidate := candidates[index]
	if GameState.budget < candidate.daily_salary():
		return
	GameState.staff_list.append(candidate)
	candidates.remove_at(index)
	_generate_candidates()
	_update_ui()
	_update_warning()

func _on_back_pressed() -> void:
	if GameState.day == 1 and GameState.staff_list.is_empty():
		_update_warning()
		return
	if GameState.day == 1 and not GameState.kitchen_equip:
		show_screen("res://scenes/shop_screen.tscn")
		return
	GameState.start_day()
	show_screen("res://scenes/game_screen.tscn")

func _on_hire_candidate_1() -> void:
	_on_hire_candidate(0)

func _on_hire_candidate_2() -> void:
	_on_hire_candidate(1)

func _on_hire_candidate_3() -> void:
	_on_hire_candidate(2)
