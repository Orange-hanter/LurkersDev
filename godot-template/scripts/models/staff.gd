class_name Staff
extends Resource
## A restaurant staff member.

enum Status { READY, BUSY, RESTING }

@export var staff_name: String = "Worker"
@export var skill: int = 1          ## 1..10
@export var stamina: float = 100.0
@export var max_stamina: float = 100.0
@export var status: Status = Status.READY
@export var busy_timer: int = 0

## Daily salary computed from skill * DAILY_SALARY_PER_SKILL
func daily_salary() -> int:
	return skill * GameConfig.DAILY_SALARY_PER_SKILL

func stamina_fraction() -> float:
	if max_stamina <= 0:
		return 0.0
	return clamp(stamina / max_stamina, 0.0, 1.0)

static func generate_candidate() -> Staff:
	var s := Staff.new()
	s.staff_name = _random_name()
	s.skill = randi_range(1, 10)
	s.max_stamina = 80.0 + randf() * 70.0
	s.stamina = s.max_stamina
	return s

const _names: Array[String] = [
	"Alice", "Bob", "Charlie", "Diana", "Evan", "Fiona", "George", "Hannah",
	"Ivan", "Julia", "Kevin", "Luna", "Mike", "Nina", "Oscar", "Paula",
	"Quinn", "Rita", "Sam", "Tina", "Uma", "Victor", "Wendy", "Xander",
	"Yara", "Zack", "Mia", "Leo", "Sofia", "Noah", "Emma", "Liam"
]

static func _random_name() -> String:
	return _names[randi_range(0, _names.size() - 1)]