from ..models import GameState
from ..config import (
    QUALITY_STAFF_WEIGHT, QUALITY_EQUIP_WEIGHT,
    SERVICE_DURATION, SUCCESS_INCOME_MULT, SUCCESS_REP_GAIN,
    FAILURE_COST_MULT, FAILURE_REP_LOSS, GUEST_LEFT_REP_LOSS,
    EQUIP_LOW_DURABILITY, EQUIP_DEGRADE_PER_SERVICE, TOTAL_TICKS_PER_DAY,
)
from .tables import find_free_table, allocate_table, release_table, find_ready_staff


def phase_1_update_timers(state: GameState) -> list[dict]:
    events = []

    for table in state.tables:
        if table.state == "occupied":
            if table.busy_timer > 0:
                table.busy_timer -= 1

    for staff in state.staff_list:
        if staff.status == "busy":
            if staff.busy_timer > 0:
                staff.busy_timer -= 1
        elif staff.status == "resting":
            staff.stamina = min(staff.max_stamina, staff.stamina + 2)

    for equip in [state.kitchen, state.hall]:
        if equip.durability < EQUIP_LOW_DURABILITY:
            events.append({"type": "warning", "message": f"{equip.name} durability critical ({equip.durability})! Quality halved."})

    return events


def phase_2_spawn_guests(state: GameState) -> list[dict]:
    from .spawning import should_spawn_guest, spawn_guest
    events = []

    if should_spawn_guest(state):
        old_len = len(state.guest_queue)
        spawn_guest(state)
        if len(state.guest_queue) > old_len:
            guest = state.guest_queue[old_len]
            events.append({"type": "spawn", "guest": guest})

    return events


def phase_3_assign_resources(state: GameState) -> list[dict]:
    events = []

    while state.guest_queue:
        free_table = find_free_table(state.tables)
        free_staff = find_ready_staff(state.staff_list)

        if not (free_table and free_staff):
            break

        guest = state.guest_queue.pop(0)
        allocate_table(free_table, guest, free_staff, SERVICE_DURATION)
        free_staff.assign_service(SERVICE_DURATION)

        state.kitchen.degrade(EQUIP_DEGRADE_PER_SERVICE)
        state.hall.degrade(EQUIP_DEGRADE_PER_SERVICE)

        events.append({"type": "assigned", "guest": guest, "table": free_table.table_id})

    to_remove = []
    for guest in state.guest_queue:
        guest.wait_timer += 1
        if guest.wait_timer >= guest.patience_ticks:
            to_remove.append(guest)
            state.pending_rep -= GUEST_LEFT_REP_LOSS
            state.lost_guests += 1
            events.append({"type": "left", "guest": guest, "rep_loss": GUEST_LEFT_REP_LOSS})

    for guest in to_remove:
        state.guest_queue.remove(guest)

    return events


def phase_4_service_completion(state: GameState) -> list[dict]:
    events = []

    for table in state.tables:
        if table.state == "occupied" and table.busy_timer == 0:
            guest = table.guest
            staff = table.staff
            if guest is None or staff is None:
                continue

            daily_event_bonus = state.daily_event.quality_mult if state.daily_event else 1.0
            equip_avg = state.avg_equipment_quality
            quality = (staff.skill * QUALITY_STAFF_WEIGHT + equip_avg * QUALITY_EQUIP_WEIGHT) * (1 + guest.mood * 0.1) * daily_event_bonus

            if quality >= guest.expectation:
                state.pending_income += guest.budget * SUCCESS_INCOME_MULT
                state.pending_rep += SUCCESS_REP_GAIN
                state.avg_quality += quality
                events.append({"type": "success", "guest": guest, "quality": quality,
                               "income": guest.budget * SUCCESS_INCOME_MULT, "rep_gain": SUCCESS_REP_GAIN})
            else:
                state.pending_expense += guest.budget * FAILURE_COST_MULT
                state.pending_rep -= FAILURE_REP_LOSS
                state.avg_quality += quality
                events.append({"type": "failure", "guest": guest, "quality": quality,
                               "loss": guest.budget * FAILURE_COST_MULT, "rep_loss": FAILURE_REP_LOSS})

            state.guests_served += 1
            staff.release()
            release_table(table)

    return events


def phase_5_staff_rest(state: GameState) -> list[dict]:
    events = []

    for staff in state.staff_list:
        if staff.status == "ready" and staff.stamina < staff.rest_threshold:
            staff.status = "resting"
            events.append({"type": "status", "staff": staff, "message": f"Staff resting (stamina {staff.stamina})"})
        elif staff.status == "resting" and staff.stamina >= staff.rest_threshold:
            staff.status = "ready"
            events.append({"type": "status", "staff": staff, "message": "Staff ready again"})

    return events


def phase_6_tick_end(state: GameState) -> list[dict]:
    events = []
    state.tick += 1
    if state.tick >= TOTAL_TICKS_PER_DAY:
        state.day_ended = True
        events.append({"type": "day_end"})
    return events


def process_tick(state: GameState) -> list[dict]:
    events = []
    events += phase_1_update_timers(state)
    events += phase_2_spawn_guests(state)
    events += phase_3_assign_resources(state)
    events += phase_4_service_completion(state)
    events += phase_5_staff_rest(state)
    events += phase_6_tick_end(state)
    return events
