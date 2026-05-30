class_name RestaurantFloor
extends Control
## Draws the restaurant as a live 2D tycoon floor plan.

const STORY_LIFETIME: float = 5.5
const MAX_STORY_EVENTS: int = 6

var _clock: float = 0.0
var _story_events: Array[Dictionary] = []


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	set_process(true)
	_connect_state_signals()


func _exit_tree() -> void:
	_disconnect_state_signals()


func _process(delta: float) -> void:
	_clock = fmod(_clock + delta, 1000.0)
	for event in _story_events:
		event["age"] = float(event["age"]) + delta
	_story_events = _story_events.filter(func(event: Dictionary) -> bool:
		return float(event["age"]) < STORY_LIFETIME
	)
	queue_redraw()


func _connect_state_signals() -> void:
	if not GameState.tables_refreshed.is_connected(queue_redraw):
		GameState.tables_refreshed.connect(queue_redraw)
	if not GameState.guest_queued.is_connected(_on_guest_queued):
		GameState.guest_queued.connect(_on_guest_queued)
	if not GameState.guest_left.is_connected(_on_guest_left):
		GameState.guest_left.connect(_on_guest_left)
	if not GameState.guest_served.is_connected(_on_guest_served):
		GameState.guest_served.connect(_on_guest_served)
	if not GameState.tick_advanced.is_connected(_on_tick):
		GameState.tick_advanced.connect(_on_tick)
	if not GameState.event_occurred.is_connected(_on_event_occurred):
		GameState.event_occurred.connect(_on_event_occurred)


func _disconnect_state_signals() -> void:
	if GameState.tables_refreshed.is_connected(queue_redraw):
		GameState.tables_refreshed.disconnect(queue_redraw)
	if GameState.guest_queued.is_connected(_on_guest_queued):
		GameState.guest_queued.disconnect(_on_guest_queued)
	if GameState.guest_left.is_connected(_on_guest_left):
		GameState.guest_left.disconnect(_on_guest_left)
	if GameState.guest_served.is_connected(_on_guest_served):
		GameState.guest_served.disconnect(_on_guest_served)
	if GameState.tick_advanced.is_connected(_on_tick):
		GameState.tick_advanced.disconnect(_on_tick)
	if GameState.event_occurred.is_connected(_on_event_occurred):
		GameState.event_occurred.disconnect(_on_event_occurred)


func _on_guest_queued(guest: Guest) -> void:
	_add_story(guest.type_label() + " party x" + str(guest.party_size) + " arrives", _guest_color(guest))


func _on_guest_left(guest: Guest) -> void:
	_add_story(guest.type_label() + " walked out", Color(0.94, 0.28, 0.22, 1))


func _on_guest_served(guest: Guest, quality: float, income: float) -> void:
	var color := Color(0.37, 0.92, 0.48, 1) if quality >= guest.expectation else Color(0.95, 0.42, 0.28, 1)
	_add_story("Table served: $" + str(int(income)) + " / Q " + str(snapped(quality, 0.1)), color)


func _on_event_occurred(message: String) -> void:
	_add_story(message.replace("EVENT: ", ""), Color(1.0, 0.78, 0.28, 1))


func _on_tick(_tick: int) -> void:
	queue_redraw()


func _add_story(text: String, color: Color) -> void:
	_story_events.push_front({"text": text, "age": 0.0, "color": color})
	if _story_events.size() > MAX_STORY_EVENTS:
		_story_events.resize(MAX_STORY_EVENTS)
	queue_redraw()


func _draw() -> void:
	var rect := Rect2(Vector2.ZERO, size)
	if rect.size.x <= 8.0 or rect.size.y <= 8.0:
		return
	var layout: Dictionary = _floor_layout(rect)
	_draw_wall_and_floor(rect, layout)
	_draw_kitchen(layout["kitchen"])
	_draw_hall(layout["hall"])
	_draw_paths(layout)
	_draw_tables(layout["hall"])
	_draw_queue(layout)
	_draw_staff(layout)
	_draw_story_events(rect)
	_draw_floor_stats(rect)


func _floor_layout(rect: Rect2) -> Dictionary:
	var margin := 18.0
	var story_width := minf(300.0, rect.size.x * 0.26) if not _story_events.is_empty() else 12.0
	var stats_height := 50.0
	var kitchen_width := maxf(190.0, rect.size.x * 0.19)
	var kitchen := Rect2(Vector2(margin, 86.0), Vector2(kitchen_width, rect.size.y - 172.0))
	var hall := Rect2(Vector2(kitchen.end.x + 18.0, 86.0), Vector2(rect.size.x - kitchen.size.x - story_width - 58.0, rect.size.y - 172.0))
	if hall.size.x < 420.0:
		hall.size.x = maxf(360.0, rect.size.x - kitchen.size.x - 54.0)
	var queue_lane := Rect2(Vector2(margin, rect.size.y - stats_height - 12.0), Vector2(rect.size.x - margin * 2.0, 46.0))
	var entrance := Vector2(queue_lane.position.x + 96.0, queue_lane.position.y + 23.0)
	var pass_counter := Vector2(kitchen.end.x - 18.0, kitchen.position.y + kitchen.size.y * 0.48)
	return {
		"kitchen": kitchen,
		"hall": hall,
		"queue": queue_lane,
		"entrance": entrance,
		"pass": pass_counter,
	}


func _draw_wall_and_floor(rect: Rect2, layout: Dictionary) -> void:
	var wall_height := 82.0
	draw_rect(rect, Color(0.25, 0.17, 0.11, 1), true)
	draw_rect(Rect2(Vector2.ZERO, Vector2(rect.size.x, wall_height)), Color(0.36, 0.22, 0.14, 1), true)

	for i in range(7):
		var x := 28.0 + float(i) * 92.0
		var window := Rect2(Vector2(x, 18.0), Vector2(58.0, 40.0))
		draw_rect(window, Color(0.08, 0.12, 0.18, 1), true)
		draw_rect(window, Color(0.92, 0.63, 0.28, 0.8), false, 2.0)
		for tower in range(3):
			var building := Rect2(window.position + Vector2(8.0 + tower * 15.0, 14.0 - tower * 4.0), Vector2(9.0, 20.0 + tower * 4.0))
			draw_rect(building, Color(0.14, 0.18, 0.24, 1), true)

	var floor_rect := Rect2(Vector2(0, wall_height), Vector2(rect.size.x, rect.size.y - wall_height))
	draw_rect(floor_rect, Color(0.52, 0.34, 0.18, 1), true)
	for y in range(int(floor_rect.position.y), int(rect.size.y), 34):
		var plank_color := Color(0.42, 0.25, 0.12, 0.42) if int(y / 34) % 2 == 0 else Color(0.66, 0.42, 0.22, 0.28)
		draw_rect(Rect2(Vector2(0, float(y)), Vector2(rect.size.x, 3.0)), plank_color, true)
	for x in range(0, int(rect.size.x), 120):
		draw_line(Vector2(float(x), wall_height), Vector2(float(x) + 80.0, rect.size.y), Color(0.25, 0.12, 0.06, 0.18), 1.0)

	var hall: Rect2 = layout["hall"]
	var carpet := Rect2(hall.position + Vector2(18.0, 28.0), hall.size - Vector2(36.0, 56.0))
	draw_rect(carpet, Color(0.32, 0.12, 0.11, 0.52), true)
	draw_rect(carpet, Color(0.88, 0.58, 0.31, 0.55), false, 2.0)


func _draw_kitchen(kitchen: Rect2) -> void:
	draw_rect(kitchen, Color(0.34, 0.31, 0.27, 1), true)
	draw_rect(kitchen, Color(0.86, 0.65, 0.42, 1), false, 3.0)
	_draw_label(kitchen.position + Vector2(16.0, 27.0), "Kitchen", 18, Color(1.0, 0.83, 0.48, 1))

	for y in range(int(kitchen.position.y + 46.0), int(kitchen.end.y), 28):
		draw_line(Vector2(kitchen.position.x, float(y)), Vector2(kitchen.end.x, float(y)), Color(0.42, 0.39, 0.34, 0.75), 1.0)
	for x in range(int(kitchen.position.x), int(kitchen.end.x), 28):
		draw_line(Vector2(float(x), kitchen.position.y + 44.0), Vector2(float(x), kitchen.end.y), Color(0.42, 0.39, 0.34, 0.75), 1.0)

	var stove := Rect2(kitchen.position + Vector2(18.0, 62.0), Vector2(kitchen.size.x - 36.0, 48.0))
	var prep := Rect2(kitchen.position + Vector2(18.0, 130.0), Vector2(kitchen.size.x - 36.0, 38.0))
	var rest := Rect2(kitchen.position + Vector2(18.0, kitchen.size.y - 76.0), Vector2(kitchen.size.x - 36.0, 48.0))
	draw_rect(stove, Color(0.1, 0.1, 0.1, 1), true)
	draw_rect(stove, Color(0.94, 0.55, 0.24, 1), false, 2.0)
	draw_rect(prep, Color(0.64, 0.57, 0.48, 1), true)
	draw_rect(prep, Color(0.98, 0.83, 0.55, 1), false, 2.0)
	draw_rect(rest, Color(0.22, 0.2, 0.18, 1), true)
	draw_rect(rest, Color(0.6, 0.46, 0.32, 1), false, 2.0)
	for i in range(4):
		var c := stove.position + Vector2(28.0 + i * 36.0, 24.0)
		draw_circle(c, 11.0, Color(0.32, 0.32, 0.33, 1))
		draw_circle(c, 5.0 + sin(_clock * 6.0 + i) * 1.4, Color(1.0, 0.33, 0.12, 0.88))


func _draw_hall(hall: Rect2) -> void:
	draw_rect(hall, Color(0.28, 0.2, 0.13, 0.18), true)
	draw_rect(hall, Color(0.91, 0.64, 0.35, 0.82), false, 3.0)
	_draw_label(hall.position + Vector2(16.0, 27.0), "Dining floor", 18, Color(1.0, 0.88, 0.64, 1))
	for i in range(GameState.decor_level):
		var lamp_x := hall.position.x + 52.0 + i * 70.0
		if lamp_x > hall.end.x - 42.0:
			break
		draw_line(Vector2(lamp_x, hall.position.y), Vector2(lamp_x, hall.position.y + 28.0), Color(0.18, 0.12, 0.06, 1), 2.0)
		draw_circle(Vector2(lamp_x, hall.position.y + 34.0), 16.0 + sin(_clock * 2.0 + i) * 1.2, Color(1.0, 0.76, 0.32, 0.24))
		draw_circle(Vector2(lamp_x, hall.position.y + 34.0), 7.0, Color(1.0, 0.76, 0.32, 1))


func _draw_paths(layout: Dictionary) -> void:
	var hall: Rect2 = layout["hall"]
	var queue_lane: Rect2 = layout["queue"]
	var pass_counter: Vector2 = layout["pass"]
	var entrance: Vector2 = layout["entrance"]
	draw_line(entrance, Vector2(hall.position.x + 28.0, entrance.y), Color(0.92, 0.62, 0.31, 0.45), 10.0)
	draw_line(pass_counter, Vector2(hall.position.x + 18.0, pass_counter.y), Color(0.92, 0.62, 0.31, 0.35), 8.0)
	draw_rect(queue_lane, Color(0.22, 0.14, 0.1, 0.92), true)
	draw_rect(queue_lane, Color(0.97, 0.72, 0.38, 0.82), false, 2.0)
	_draw_label(queue_lane.position + Vector2(14.0, 29.0), "Entrance queue", 14, Color(0.95, 0.84, 0.66, 1))


func _draw_tables(hall: Rect2) -> void:
	var table_count: int = GameState.tables.size()
	var count: int = maxi(1, table_count)
	var columns: int = clampi(ceili(sqrt(float(count) * 1.35)), 1, 7)
	var rows: int = maxi(1, ceili(float(count) / float(columns)))
	var grid_rect := Rect2(hall.position + Vector2(36.0, 62.0), hall.size - Vector2(72.0, 114.0))
	var cell := Vector2(grid_rect.size.x / float(columns), grid_rect.size.y / float(rows))
	for i in range(table_count):
		var table: Table = GameState.tables[i]
		var center := _table_center(i, grid_rect, columns, cell)
		_draw_table(table, center, minf(cell.x, cell.y) * 0.29)


func _table_center(index: int, grid_rect: Rect2, columns: int, cell: Vector2) -> Vector2:
	var col: int = index % columns
	var row: int = int(index / columns)
	return grid_rect.position + Vector2(cell.x * (float(col) + 0.5), cell.y * (float(row) + 0.5))


func _draw_table(table: Table, center: Vector2, radius: float) -> void:
	var occupied := table.state == Table.State.OCCUPIED
	var table_color := Color(0.56, 0.30, 0.13, 1.0) if not occupied else Color(0.66, 0.22, 0.16, 1.0)
	var rim_color := Color(1.0, 0.78, 0.43, 1.0) if not occupied else Color(1.0, 0.49, 0.35, 1.0)
	_draw_shadow(center + Vector2(0, 9), radius + 16.0, 0.22)
	draw_circle(center, radius, table_color)
	draw_arc(center, radius, 0.0, TAU, 42, rim_color, 3.0)

	for i in range(table.capacity):
		var angle := TAU * float(i) / float(table.capacity)
		var seat_pos := center + Vector2(cos(angle), sin(angle)) * (radius + 15.0)
		draw_circle(seat_pos + Vector2(0, 3), 8.0, Color(0.08, 0.05, 0.03, 0.28))
		draw_circle(seat_pos, 7.5, Color(0.12, 0.31, 0.29, 1.0))

	_draw_label(center + Vector2(-10.0, 5.0), str(table.table_id), 14, Color(1.0, 0.96, 0.8, 1))
	if occupied and table.assigned_guest:
		_draw_guest_party(table.assigned_guest, center, radius)
		_draw_progress(center, radius + 28.0, table.service_progress())


func _draw_guest_party(guest: Guest, center: Vector2, radius: float) -> void:
	for i in range(guest.party_size):
		var angle := TAU * float(i) / float(maxi(1, guest.party_size)) + 0.35
		var pos := center + Vector2(cos(angle), sin(angle)) * (radius * 0.55)
		_draw_person(pos, _guest_color(guest), Color(0.18, 0.11, 0.08, 1), 0.0, false)


func _draw_progress(center: Vector2, radius: float, progress: float) -> void:
	var start_angle := -PI * 0.5
	draw_arc(center, radius, 0.0, TAU, 48, Color(0.09, 0.05, 0.03, 0.45), 5.0)
	draw_arc(center, radius, start_angle, start_angle + TAU * clampf(progress, 0.0, 1.0), 48, Color(0.48, 0.95, 0.58, 1), 5.0)


func _draw_queue(layout: Dictionary) -> void:
	var queue_lane: Rect2 = layout["queue"]
	var start := Vector2(queue_lane.position.x + 132.0, queue_lane.position.y + 22.0)
	var spacing := 33.0
	for i in range(min(GameState.guest_queue.size(), 20)):
		var guest: Guest = GameState.guest_queue[i]
		var pos := start + Vector2(float(i) * spacing, sin(_clock * 4.0 + i) * 1.8)
		var patience := 1.0 - clampf(float(guest.wait_timer) / maxf(1.0, float(guest.patience_ticks)), 0.0, 1.0)
		_draw_person(pos, _guest_color(guest), Color(0.16, 0.09, 0.06, 1), _clock * 5.0 + i, true)
		draw_rect(Rect2(pos + Vector2(-10.0, 15.0), Vector2(20.0, 3.0)), Color(0.18, 0.08, 0.05, 0.6), true)
		draw_rect(Rect2(pos + Vector2(-10.0, 15.0), Vector2(20.0 * patience, 3.0)), Color(0.5, 0.95, 0.42, 1), true)
		if guest.party_size > 1:
			_draw_label(pos + Vector2(8.0, -8.0), str(guest.party_size), 12, Color(1.0, 0.94, 0.62, 1))


func _draw_staff(layout: Dictionary) -> void:
	var kitchen: Rect2 = layout["kitchen"]
	var hall: Rect2 = layout["hall"]
	var pass_counter: Vector2 = layout["pass"]
	var grid_rect := Rect2(hall.position + Vector2(36.0, 62.0), hall.size - Vector2(72.0, 114.0))
	var count: int = maxi(1, GameState.tables.size())
	var columns: int = clampi(ceili(sqrt(float(count) * 1.35)), 1, 7)
	var rows: int = maxi(1, ceili(float(count) / float(columns)))
	var cell := Vector2(grid_rect.size.x / float(columns), grid_rect.size.y / float(rows))

	for i in range(GameState.staff_list.size()):
		var staff: Staff = GameState.staff_list[i]
		var table_index := _table_index_for_staff(staff)
		var pos: Vector2
		var walking := false
		if table_index >= 0:
			var target := _table_center(table_index, grid_rect, columns, cell)
			var t := 0.5 + sin(_clock * 5.0 + float(i) * 1.7) * 0.5
			pos = pass_counter.lerp(target + Vector2(0.0, -34.0), t)
			walking = true
			draw_line(pass_counter, target + Vector2(0.0, -34.0), Color(1.0, 0.82, 0.44, 0.22), 3.0)
		elif staff.status == Staff.Status.RESTING:
			pos = kitchen.position + Vector2(56.0 + float(i % 3) * 38.0, kitchen.size.y - 52.0)
		else:
			pos = pass_counter + Vector2(-24.0 - float(i % 3) * 24.0, -28.0 + float(i / 3) * 26.0)
		_draw_waiter(staff, pos, _clock * 8.0 + float(i), walking)


func _table_index_for_staff(staff: Staff) -> int:
	for i in range(GameState.tables.size()):
		var table: Table = GameState.tables[i]
		if table.assigned_staff == staff:
			return i
	return -1


func _draw_waiter(staff: Staff, pos: Vector2, phase: float, walking: bool) -> void:
	var body_color := Color(0.1, 0.18, 0.34, 1) if staff.stamina_fraction() > 0.35 else Color(0.38, 0.24, 0.16, 1)
	var bob := sin(phase) * 2.0 if walking else sin(phase * 0.4) * 0.8
	var p := pos + Vector2(0.0, bob)
	_draw_shadow(p + Vector2(0, 16), 14.0, 0.25)
	draw_circle(p + Vector2(0, -10), 7.0, Color(0.88, 0.68, 0.48, 1))
	draw_rect(Rect2(p + Vector2(-7, -3), Vector2(14, 18)), body_color, true)
	draw_rect(Rect2(p + Vector2(-6, 0), Vector2(12, 4)), Color(1, 1, 1, 0.9), true)
	var leg := sin(phase) * 4.0 if walking else 0.0
	draw_line(p + Vector2(-4, 15), p + Vector2(-7 + leg, 25), Color(0.08, 0.08, 0.1, 1), 3.0)
	draw_line(p + Vector2(4, 15), p + Vector2(7 - leg, 25), Color(0.08, 0.08, 0.1, 1), 3.0)
	draw_circle(p + Vector2(12, -1), 4.0, Color(0.92, 0.84, 0.66, 1))
	draw_circle(p + Vector2(15, -1), 3.0, Color(0.95, 0.38, 0.18, 1))


func _draw_person(pos: Vector2, shirt: Color, hair: Color, phase: float, walking: bool) -> void:
	var p := pos + Vector2(0.0, sin(phase) * 1.5 if walking else 0.0)
	_draw_shadow(p + Vector2(0, 11), 10.0, 0.18)
	draw_circle(p + Vector2(0, -8), 6.0, Color(0.86, 0.66, 0.48, 1))
	draw_arc(p + Vector2(0, -10), 6.0, PI, TAU, 12, hair, 3.0)
	draw_rect(Rect2(p + Vector2(-6, -2), Vector2(12, 14)), shirt, true)
	var leg := sin(phase) * 2.5 if walking else 0.0
	draw_line(p + Vector2(-3, 12), p + Vector2(-5 + leg, 19), Color(0.12, 0.1, 0.09, 1), 2.0)
	draw_line(p + Vector2(3, 12), p + Vector2(5 - leg, 19), Color(0.12, 0.1, 0.09, 1), 2.0)


func _draw_story_events(rect: Rect2) -> void:
	if _story_events.is_empty():
		return
	var font := get_theme_default_font()
	var width := minf(300.0, rect.size.x * 0.28)
	var x := rect.size.x - width - 20.0
	var y := 96.0
	for i in range(_story_events.size()):
		var event: Dictionary = _story_events[i]
		var age := float(event["age"])
		var alpha := clampf(1.0 - maxf(0.0, age - 3.7) / 1.8, 0.0, 1.0)
		var card := Rect2(Vector2(x, y + i * 44.0 - minf(age * 12.0, 14.0)), Vector2(width, 34.0))
		var color: Color = event["color"]
		draw_rect(card, Color(0.16, 0.10, 0.07, 0.72 * alpha), true)
		draw_rect(card, Color(color.r, color.g, color.b, 0.9 * alpha), false, 2.0)
		draw_circle(card.position + Vector2(17.0, 17.0), 5.0, Color(color.r, color.g, color.b, alpha))
		draw_string(font, card.position + Vector2(30.0, 22.0), _short_story_text(str(event["text"])), HORIZONTAL_ALIGNMENT_LEFT, width - 40.0, 13, Color(1.0, 0.91, 0.78, alpha))


func _draw_floor_stats(rect: Rect2) -> void:
	var bar := Rect2(Vector2(18.0, 18.0), Vector2(rect.size.x - 36.0, 40.0))
	draw_rect(bar, Color(0.16, 0.10, 0.07, 0.78), true)
	draw_rect(bar, Color(0.82, 0.55, 0.28, 0.72), false, 2.0)
	var cashflow := int(GameState.pending_income - GameState.pending_expense)
	var marketing: Dictionary = GameConfig.MARKETING_LEVELS[GameState.marketing_level]
	var chips: Array[String] = [
		"Seats " + str(GameState.day_total_seats_sold),
		"Q " + str(GameState.guest_queue.size()),
		"$" + str(int(GameState.pending_income)),
		"Cost " + str(int(GameState.pending_expense)),
		("Net +" if cashflow >= 0 else "Net -") + str(abs(cashflow)),
		_marketing_short(str(marketing["label"])),
	]
	var x := bar.position.x + 12.0
	for chip in chips:
		var width := _chip_width(chip)
		if x + width > bar.end.x - 8.0:
			break
		_draw_chip(Rect2(Vector2(x, bar.position.y + 7.0), Vector2(width, 26.0)), chip)
		x += width + 7.0


func _draw_chip(rect: Rect2, text: String) -> void:
	draw_rect(rect, Color(0.22, 0.13, 0.08, 0.9), true)
	draw_rect(rect, Color(0.76, 0.48, 0.23, 0.75), false, 1.5)
	draw_string(get_theme_default_font(), rect.position + Vector2(9.0, 18.0), text, HORIZONTAL_ALIGNMENT_LEFT, rect.size.x - 12.0, 13, Color(1.0, 0.90, 0.72, 1))


func _chip_width(text: String) -> float:
	return clampf(34.0 + float(text.length()) * 7.2, 52.0, 118.0)


func _marketing_short(label: String) -> String:
	match label:
		"Word of mouth":
			return "WoM"
		"Radio ads":
			return "Radio"
		"City campaign":
			return "City"
	return label


func _short_story_text(text: String) -> String:
	if text.length() <= 34:
		return text
	return text.substr(0, 31) + "..."


func _draw_label(pos: Vector2, text: String, size_px: int, color: Color) -> void:
	draw_string(get_theme_default_font(), pos, text, HORIZONTAL_ALIGNMENT_LEFT, -1, size_px, color)


func _draw_shadow(pos: Vector2, radius: float, alpha: float) -> void:
	draw_ellipse(pos, radius, radius * 0.35, Color(0, 0, 0, alpha))


func _guest_color(guest: Guest) -> Color:
	match guest.guest_type:
		Guest.GuestType.REGULAR:
			return Color(0.72, 0.56, 0.38, 1)
		Guest.GuestType.BUSINESS:
			return Color(0.28, 0.48, 0.78, 1)
		Guest.GuestType.VIP:
			return Color(0.98, 0.72, 0.2, 1)
		Guest.GuestType.CRITIC:
			return Color(0.82, 0.16, 0.19, 1)
	return Color.WHITE
