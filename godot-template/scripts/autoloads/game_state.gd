extends Node
## Central game state singleton. Holds all runtime data and emits signals
## for reactive UI updates.

# --- Signals ---
signal guest_queued(guest: Guest)
signal guest_served(guest: Guest, quality: float, income: float)
signal guest_left(guest: Guest)
signal day_started(day: int)
signal day_ended(stats: Dictionary)
signal bankruptcy()
signal budget_changed(new_value: int)
signal rep_changed(new_value: int)
signal event_occurred(message: String)
signal tick_advanced(tick: int)
signal tables_refreshed()
signal staff_refreshed()

# --- Game Data ---
var budget: int = GameConfig.STARTING_BUDGET
var reputation: int = 0
var day: int = 1
var tick: int = 0
var paused: bool = false
var game_speed: float = 1.0
var rush_hour_active: bool = false
var current_phase: int = 0  ## 1..6 for the six tick phases

# Collections
var kitchen_equip: Equipment
var hall_equip: Equipment
var staff_list: Array[Staff] = []
var guest_queue: Array[Guest] = []
var tables: Array[Table] = []
var table_size_chosen: String = "medium"
var table_count_chosen: int = 4
var tick_interval_chosen: float = GameConfig.DEFAULT_TICK_INTERVAL
var tick_duration_minutes: int = 5
var menu_price: int = GameConfig.BASE_MENU_PRICE
var marketing_level: int = 0
var decor_level: int = 0

# Pending economy (resolved at end of day)
var pending_income: float = 0.0
var pending_expense: float = 0.0
var pending_rep: float = 0.0
var day_total_income: float = 0.0
var day_total_guests_served: int = 0
var day_total_guests_lost: int = 0
var day_total_seats_sold: int = 0
var day_service_qualities: Array = []

# History
var day_history: Array = []

# --- Internal ---
var _tick_timer: float = 0.0

func _process(delta: float) -> void:
	if paused or tick >= GameConfig.TOTAL_TICKS_PER_DAY:
		return
	_tick_timer += delta * game_speed
	if _tick_timer >= tick_interval_chosen:
		_tick_timer -= tick_interval_chosen
		_advance_tick()


func _advance_tick() -> void:
	tick += 1
	tick_advanced.emit(tick)
	if tick > GameConfig.TOTAL_TICKS_PER_DAY:
		return

	# Phase calculation (1..6)
	var phase := clampi((tick - 1) / (GameConfig.TOTAL_TICKS_PER_DAY / 6) + 1, 1, 6)
	if phase != current_phase:
		current_phase = phase

	# Random tick event
	var evt := EventManager.trigger_tick_event()
	if not evt.is_empty():
		event_occurred.emit("EVENT: " + evt["name"])
		_apply_tick_event(evt["name"])

	# Spawn guests
	_spawn_guests()

	# Assign and service
	_assign_and_service()

	# Process busy timers / stamina
	_process_busy_and_stamina()

	# Check bankruptcy mid-day
	if budget < 0:
		paused = true
		bankruptcy.emit()


func _spawn_guests() -> void:
	if guest_queue.size() >= GameConfig.QUEUE_SOFT_CAP:
		return
	var base := GameConfig.SPAWN_BASE_RATE
	var rep_factor := GameConfig.SPAWN_REP_FACTOR * reputation
	var mult := GameConfig.SPAWN_VARIANCE_LOW + randf() * (GameConfig.SPAWN_VARIANCE_HIGH - GameConfig.SPAWN_VARIANCE_LOW)
	# Time of day multiplier
	var time_mult: float = 1.0
	for range_key in GameConfig.TIME_OF_DAY_MULTIPLIERS.keys():
		if tick >= range_key.x and tick < range_key.y:
			time_mult = GameConfig.TIME_OF_DAY_MULTIPLIERS[range_key]
			break
	if rush_hour_active:
		time_mult *= 2.0
	var marketing_info: Dictionary = GameConfig.MARKETING_LEVELS[marketing_level]
	var spawn_prob := (base + rep_factor) * mult * time_mult * float(marketing_info["demand_mult"])
	spawn_prob *= maxf(0.25, 1.0 - float(guest_queue.size()) / float(GameConfig.QUEUE_SOFT_CAP * 2))
	while spawn_prob >= 1.0:
		_add_guest_to_queue(Guest.generate_random())
		spawn_prob -= 1.0
	if randf() < spawn_prob:
		_add_guest_to_queue(Guest.generate_random())


func _add_guest_to_queue(guest: Guest) -> void:
	guest_queue.append(guest)
	# Sort by priority descending (VIP/critic first)
	guest_queue.sort_custom(func(a: Guest, b: Guest) -> bool:
		return a.priority() > b.priority()
	)
	guest_queued.emit(guest)


func _assign_and_service() -> void:
	# Guests leaving due to impatience
	var leaving: Array[Guest] = []
	for guest in guest_queue:
		guest.wait_timer += 1
		guest.mood = clampf(1.0 - (float(guest.wait_timer) / maxf(1.0, float(guest.patience_ticks))), 0.0, 1.0)
		if guest.wait_timer >= guest.patience_ticks:
			leaving.append(guest)
	for guest in leaving:
		guest_queue.erase(guest)
		day_total_guests_lost += 1
		pending_rep -= GameConfig.GUEST_LEFT_REP_LOSS * GameConfig.guest_types()[guest.type_key()]["rep_mult"]
		guest_left.emit(guest)
		budget_changed.emit(budget)

	# Assign free staff to free tables with guests
	for table in tables:
		if table.state == Table.State.FREE and guest_queue.size() > 0:
			var staff := _find_ready_staff()
			if staff:
				var guest := _take_guest_for_capacity(table.capacity)
				if guest == null:
					continue
				table.state = Table.State.OCCUPIED
				var duration := _service_duration(guest, staff)
				table.busy_timer = duration
				table.service_total_ticks = duration
				table.assigned_guest = guest
				table.assigned_staff = staff
				staff.status = Staff.Status.BUSY
				staff.busy_timer = duration
				staff.stamina -= randi_range(4, 10) + guest.party_size
				staff.stamina = maxf(staff.stamina, 0.0)

	# Service progress and completion
	for table in tables:
		if table.state == Table.State.OCCUPIED and table.busy_timer > 0:
			table.busy_timer -= 1
			if table.assigned_staff:
				table.assigned_staff.busy_timer -= 1

			if table.busy_timer <= 0:
				# Service complete
				var guest: Guest = table.assigned_guest
				var staff: Staff = table.assigned_staff
				var equip_quality := 0.0
				if is_instance_valid(kitchen_equip) and is_instance_valid(hall_equip):
					equip_quality = (kitchen_equip.effective_quality() + hall_equip.effective_quality()) / 2.0
					kitchen_equip.durability = maxf(0.0, kitchen_equip.durability - GameConfig.EQUIP_DEGRADE_PER_SERVICE)
					hall_equip.durability = maxf(0.0, hall_equip.durability - GameConfig.EQUIP_DEGRADE_PER_SERVICE)
				elif is_instance_valid(kitchen_equip):
					equip_quality = kitchen_equip.effective_quality()
					kitchen_equip.durability = maxf(0.0, kitchen_equip.durability - GameConfig.EQUIP_DEGRADE_PER_SERVICE)
				elif is_instance_valid(hall_equip):
					equip_quality = hall_equip.effective_quality()
					hall_equip.durability = maxf(0.0, hall_equip.durability - GameConfig.EQUIP_DEGRADE_PER_SERVICE)
				else:
					equip_quality = 0.5

				var quality := (staff.skill * GameConfig.QUALITY_STAFF_WEIGHT) + (equip_quality * GameConfig.QUALITY_EQUIP_WEIGHT)
				quality += decor_level * GameConfig.DECOR_QUALITY_BONUS
				quality -= guest.price_pressure(menu_price)
				quality = clampf(quality, 0.0, 10.0)
				day_service_qualities.append(quality)

				var base_check := guest.check_value(menu_price)
				var income := base_check
				var success := quality >= guest.expectation
				if success:
					var tip_mult := 1.0 + maxf(0.0, quality - guest.expectation) * GameConfig.TIP_PER_QUALITY_POINT
					income *= GameConfig.SUCCESS_INCOME_MULT * tip_mult
					pending_rep += GameConfig.SUCCESS_REP_GAIN * GameConfig.guest_types()[guest.type_key()]["rep_mult"]
					day_total_guests_served += 1
				else:
					income *= GameConfig.FAILURE_COST_MULT
					pending_rep -= GameConfig.FAILURE_REP_LOSS * GameConfig.guest_types()[guest.type_key()]["rep_mult"]
					day_total_guests_served += 1
				pending_income += income
				day_total_seats_sold += guest.party_size
				guest_served.emit(guest, quality, income)

				# Reset table and staff
				table.state = Table.State.FREE
				table.busy_timer = 0
				table.service_total_ticks = 0
				table.assigned_guest = null
				if staff.stamina <= GameConfig.REST_THRESHOLD * staff.max_stamina:
					staff.status = Staff.Status.RESTING
				else:
					staff.status = Staff.Status.READY
				staff.busy_timer = 0
				table.assigned_staff = null

	staff_refreshed.emit()
	tables_refreshed.emit()


func _find_ready_staff() -> Staff:
	var candidates: Array[Staff] = []
	for s in staff_list:
		if s.status == Staff.Status.READY:
			candidates.append(s)
	if candidates.is_empty():
		return null
	# Pick highest stamina to distribute load
	candidates.sort_custom(func(a: Staff, b: Staff) -> bool:
		return a.stamina > b.stamina
	)
	return candidates[0]


func _take_guest_for_capacity(capacity: int) -> Guest:
	var best_index := -1
	var best_priority := -999
	for i in range(guest_queue.size()):
		var guest: Guest = guest_queue[i]
		if guest.party_size > capacity:
			continue
		var score := guest.priority() * 100 + guest.wait_timer
		if score > best_priority:
			best_priority = score
			best_index = i
	if best_index == -1:
		return null
	var picked: Guest = guest_queue[best_index]
	guest_queue.remove_at(best_index)
	return picked


func _service_duration(guest: Guest, staff: Staff) -> int:
	var duration := float(GameConfig.SERVICE_DURATION)
	duration += float(guest.party_size - 1) * GameConfig.SERVICE_PARTY_SIZE_FACTOR
	duration -= float(staff.skill) * GameConfig.SERVICE_SKILL_DISCOUNT
	if is_instance_valid(kitchen_equip):
		duration -= kitchen_equip.effective_quality() * 0.08
	return maxi(2, ceili(duration))


func _process_busy_and_stamina() -> void:
	for s in staff_list:
		if s.status == Staff.Status.RESTING:
			s.stamina = minf(s.max_stamina, s.stamina + GameConfig.REST_RECOVERY_RATE)
			if s.stamina >= s.max_stamina * 0.6:
				s.status = Staff.Status.READY


func _apply_tick_event(event_name: String) -> void:
	match event_name:
		"rush_hour":
			rush_hour_active = true
			await get_tree().create_timer(3.0 / game_speed).timeout
			rush_hour_active = false
		"inspector":
			if is_instance_valid(kitchen_equip) and kitchen_equip.durability < GameConfig.EQUIP_LOW_DURABILITY:
				pending_rep -= 10
			if is_instance_valid(hall_equip) and hall_equip.durability < GameConfig.EQUIP_LOW_DURABILITY:
				pending_rep -= 10
		"equipment_break":
			if is_instance_valid(kitchen_equip):
				kitchen_equip.durability = maxf(0.0, kitchen_equip.durability - randi_range(10, 25))
			if is_instance_valid(hall_equip):
				hall_equip.durability = maxf(0.0, hall_equip.durability - randi_range(10, 25))
		"investor":
			pending_income += randi_range(50, 150)
		"party":
			for i in range(randi_range(2, 4)):
				_add_guest_to_queue(Guest.generate_random())
		"food_critic":
			var critic_guest := Guest.generate_random({"critic": GameConfig.guest_types()["critic"]})
			_add_guest_to_queue(critic_guest)


func start_day() -> void:
	reset_daily()
	# Forecast operating costs; applied once in end_day with the day's revenue.
	var salaries := 0
	for s in staff_list:
		salaries += s.daily_salary()
	pending_expense += salaries
	pending_expense += GameConfig.UTILITY_COST_PER_DAY
	pending_expense += table_count_chosen * GameConfig.TABLE_RENT_PER_DAY
	pending_expense += int(GameConfig.MARKETING_LEVELS[marketing_level]["cost"])

	# Create tables
	tables.clear()
	for i in range(table_count_chosen):
		tables.append(Table.create(i + 1, table_size_chosen))

	# Daily event
	var daily_evt := EventManager.trigger_daily_event()
	if not daily_evt.is_empty():
		event_occurred.emit("DAILY EVENT: " + daily_evt["name"])
		_apply_daily_event(daily_evt["name"])

	day_started.emit(day)


func _apply_daily_event(event_name: String) -> void:
	match event_name:
		"health_inspection":
			var penalty := 0
			if is_instance_valid(kitchen_equip) and kitchen_equip.durability < GameConfig.EQUIP_LOW_DURABILITY:
				penalty += 15
			if is_instance_valid(hall_equip) and hall_equip.durability < GameConfig.EQUIP_LOW_DURABILITY:
				penalty += 15
			pending_rep -= penalty
		"vip_guest":
			var vip_guest := Guest.generate_random({"vip": GameConfig.guest_types()["vip"]})
			_add_guest_to_queue(vip_guest)
		"equipment_breakdown":
			if is_instance_valid(kitchen_equip):
				kitchen_equip.durability = maxf(0.0, kitchen_equip.durability - randi_range(20, 40))
			if is_instance_valid(hall_equip):
				hall_equip.durability = maxf(0.0, hall_equip.durability - randi_range(20, 40))
		"good_press":
			pending_rep += randi_range(5, 15)


func end_day() -> void:
	paused = true
	budget += int(pending_income)
	budget -= int(pending_expense)
	reputation += int(pending_rep)
	reputation = clampi(reputation, GameConfig.REP_MIN, GameConfig.REP_MAX)
	budget_changed.emit(budget)
	rep_changed.emit(reputation)

	var avg_quality := 0.0
	if not day_service_qualities.is_empty():
		var sum := 0.0
		for q in day_service_qualities:
			sum += q
		avg_quality = sum / day_service_qualities.size()

	var stats := {
		"day": day,
		"income": pending_income,
		"expense": pending_expense,
		"profit": pending_income - pending_expense,
		"rep_change": int(pending_rep),
		"guests_served": day_total_guests_served,
		"guests_lost": day_total_guests_lost,
		"seats_sold": day_total_seats_sold,
		"avg_quality": avg_quality,
		"budget": budget,
		"reputation": reputation,
		"menu_price": menu_price,
		"decor_level": decor_level,
		"marketing_level": marketing_level,
	}
	day_history.append(stats)
	day_ended.emit(stats)

	if budget < 0:
		bankruptcy.emit()


func reset_daily() -> void:
	tick = 0
	paused = false
	game_speed = 1.0
	rush_hour_active = false
	current_phase = 0
	guest_queue.clear()
	pending_income = 0.0
	pending_expense = 0.0
	pending_rep = 0.0
	day_total_income = 0.0
	day_total_guests_served = 0
	day_total_guests_lost = 0
	day_total_seats_sold = 0
	day_service_qualities.clear()
	_tick_timer = 0.0

	for t in tables:
		t.state = Table.State.FREE
		t.busy_timer = 0
		t.service_total_ticks = 0
		t.assigned_guest = null
		t.assigned_staff = null

	for s in staff_list:
		s.status = Staff.Status.READY
		s.stamina = s.max_stamina
		s.busy_timer = 0


func spend_budget(amount: int) -> bool:
	if budget >= amount:
		budget -= amount
		budget_changed.emit(budget)
		return true
	return false


func daily_cost_forecast() -> int:
	var salaries := 0
	for s in staff_list:
		salaries += s.daily_salary()
	return salaries + GameConfig.UTILITY_COST_PER_DAY + table_count_chosen * GameConfig.TABLE_RENT_PER_DAY + int(GameConfig.MARKETING_LEVELS[marketing_level]["cost"])


func upgrade_decor_cost() -> int:
	return GameConfig.DECOR_UPGRADE_BASE_COST + decor_level * 70


func can_upgrade_decor() -> bool:
	return decor_level < GameConfig.DECOR_MAX_LEVEL and budget >= upgrade_decor_cost()


func upgrade_decor() -> bool:
	if not can_upgrade_decor():
		return false
	var cost := upgrade_decor_cost()
	budget -= cost
	decor_level += 1
	budget_changed.emit(budget)
	rep_changed.emit(reputation)
	return true


func set_menu_price(value: int) -> void:
	menu_price = clampi(value, GameConfig.MIN_MENU_PRICE, GameConfig.MAX_MENU_PRICE)
	budget_changed.emit(budget)


func set_marketing_level(value: int) -> void:
	marketing_level = clampi(value, 0, GameConfig.MARKETING_LEVELS.size() - 1)
	budget_changed.emit(budget)
