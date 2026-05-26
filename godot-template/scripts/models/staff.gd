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