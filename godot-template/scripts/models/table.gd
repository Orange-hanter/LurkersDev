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
@export var assigned_guest: Guest
@export var assigned_staff: Staff