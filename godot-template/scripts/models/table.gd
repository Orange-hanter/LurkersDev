class_name Table
extends Resource
## A restaurant table that seats guests.

enum TableSize { SMALL, MEDIUM, LARGE }
enum State { FREE, OCCUPIED }

@export var table_id: int = 0
@export var table_size: TableSize = TableSize.MEDIUM
@export var capacity: int = 4
@export var state: State = State.FREE
@export var busy_timer: int = 0
@export var service_total_ticks: int = 0
@export var assigned_guest: Guest
@export var assigned_staff: Staff

func service_progress() -> float:
	if service_total_ticks <= 0:
		return 0.0
	return clampf(1.0 - (float(busy_timer) / float(service_total_ticks)), 0.0, 1.0)

static func create(id: int, size_str: String) -> Table:
	var t := Table.new()
	t.table_id = id
	match size_str.to_lower():
		"small":  t.table_size = TableSize.SMALL
		"medium": t.table_size = TableSize.MEDIUM
		"large":  t.table_size = TableSize.LARGE
	t.capacity = GameConfig.table_seat_count(size_str.to_lower())
	return t
