import random
from typing import List
from ..models import GameState
from ..config import (
    BANKRUPTCY_REP, RANDOM_EVENT_CHANCE,
    QUALITY_STAFF_WEIGHT, QUALITY_EQUIP_WEIGHT,
    SERVICE_STAMINA_PER_EXP_MULT,
    SUCCESS_INCOME_MULT, SUCCESS_REP_BASE, FAILURE_REP_BASE, GUEST_LEFT_REP_BASE,
    EQUIP_DEGRADE_PER_SERVICE,
)
from .spawning import spawn_guest, should_spawn_guest
from .events import pick_random_event


def process_tick(state: GameState) -> List[dict]:
    events: List[dict] = []
    state.tick += 1
    events.append({"type": "tick", "tick": state.tick, "time": state.current_time_str()})

    if state.tick > state.total_ticks:
        events.append({"type": "day_end"})
        return events

    if state.reputation < BANKRUPTCY_REP:
        events.append({"type": "bankruptcy"})
        return events

    for staff in state.staff_list:
        staff.tick_update(kitchen_effective_quality=state.kitchen.effective_quality)

    if RANDOM_EVENT_CHANCE > 0 and random.random() < RANDOM_EVENT_CHANCE:
        event = pick_random_event()
        if event:
            result = event.handler(state)
            events.append({"type": "event", "message": result})

    if should_spawn_guest(state):
        spawn_guest(state)
        events.append({"type": "spawn"})

    free_staff = [s for s in state.staff_list if s.is_free]
    while free_staff and state.guest_queue:
        staff = free_staff.pop(0)
        guest = state.guest_queue.pop(0)
        quality = staff.skill * QUALITY_STAFF_WEIGHT + state.avg_equipment_quality * QUALITY_EQUIP_WEIGHT
        stamina_drain = 8 + int(guest.expectation_multiplier * SERVICE_STAMINA_PER_EXP_MULT)
        staff.start_service(stamina_drain=stamina_drain)
        state.kitchen.degrade(EQUIP_DEGRADE_PER_SERVICE)
        state.hall.degrade(EQUIP_DEGRADE_PER_SERVICE)
        state.served_total += 1
        rep_mult = guest.rep_multiplier
        if quality >= guest.expectation:
            income = guest.budget * SUCCESS_INCOME_MULT
            state.budget += income
            rep_gain = SUCCESS_REP_BASE * rep_mult
            state.reputation += rep_gain
            state.served_success += 1
            events.append({"type": "success", "guest": guest, "income": income, "rep_gain": rep_gain})
        else:
            loss = guest.budget
            state.budget -= loss
            rep_loss = FAILURE_REP_BASE * rep_mult
            state.reputation -= rep_loss
            state.served_fail += 1
            events.append({"type": "failure", "guest": guest, "loss": loss, "rep_loss": rep_loss})

    for guest in list(state.guest_queue):
        guest.wait_timer += 1
        if guest.wait_timer >= guest.patience_ticks:
            state.guest_queue.remove(guest)
            rep_loss = GUEST_LEFT_REP_BASE * guest.rep_multiplier
            state.reputation -= rep_loss
            state.left_guests += 1
            events.append({"type": "left", "guest": guest, "rep_loss": rep_loss})

    total_salary = sum(s.daily_salary / state.total_ticks for s in state.staff_list)
    state.budget -= total_salary
    if state.staff_list:
        events.append({"type": "salary", "amount": total_salary})

    events.append({"type": "status", "budget": state.budget, "reputation": state.reputation, "queue_len": len(state.guest_queue)})
    return events


def run_ticks(state: GameState, n: int) -> List[dict]:
    final_events: List[dict] = []
    for _ in range(n):
        if state.tick >= state.total_ticks or state.reputation < BANKRUPTCY_REP:
            break
        final_events = process_tick(state)
    return final_events
