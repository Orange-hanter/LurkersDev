import random
from ..models import Guest, GUEST_TYPES, GameState
from ..config import (
    SPAWN_BASE_RATE, SPAWN_REP_FACTOR,
    SPAWN_VARIANCE_LOW, SPAWN_VARIANCE_HIGH,
    GUEST_BUDGET_MEAN, GUEST_BUDGET_STDDEV, GUEST_BUDGET_MIN,
    GUEST_PATIENCE_MIN, GUEST_PATIENCE_MAX,
    GUEST_BASE_EXPECTATION, GUEST_EXPECTATION_REP_FACTOR,
    TOTAL_TICKS_PER_DAY, TIME_OF_DAY_MULTIPLIERS,
)


def _get_time_of_day_multiplier(tick: int) -> float:
    for (lo, hi), mult in TIME_OF_DAY_MULTIPLIERS.items():
        if lo <= tick < hi:
            return mult
    return 1.0


def _pick_guest_type() -> str:
    total = sum(info["weight"] for info in GUEST_TYPES.values())
    roll = random.uniform(0, total)
    cumulative = 0
    for gtype, info in GUEST_TYPES.items():
        cumulative += info["weight"]
        if roll <= cumulative:
            return gtype
    return "regular"


def spawn_guest(state: GameState) -> None:
    guest_type = _pick_guest_type()
    type_info = GUEST_TYPES[guest_type]
    budget = max(GUEST_BUDGET_MIN, random.gauss(GUEST_BUDGET_MEAN * type_info["budget_mult"], GUEST_BUDGET_STDDEV))
    patience_ticks = random.randint(GUEST_PATIENCE_MIN, GUEST_PATIENCE_MAX)
    base_exp = GUEST_BASE_EXPECTATION * type_info["exp_mult"]
    expectation = base_exp + state.reputation * GUEST_EXPECTATION_REP_FACTOR
    guest = Guest(guest_type, budget, patience_ticks, expectation)
    _insert_by_priority(state.guest_queue, guest)


def _insert_by_priority(queue: list, guest: Guest) -> None:
    i = 0
    while i < len(queue) and queue[i].priority >= guest.priority:
        i += 1
    queue.insert(i, guest)


def should_spawn_guest(state: GameState) -> bool:
    base_rate = SPAWN_BASE_RATE
    if state.rush_hour_active:
        base_rate *= 2
        state.rush_hour_remaining -= 1
        if state.rush_hour_remaining <= 0:
            state.rush_hour_active = False

    time_mult = _get_time_of_day_multiplier(state.tick)
    event_mult = state.daily_event.spawn_mult if state.daily_event else 1.0
    rep_mult = max(0.1, 1 + state.reputation * SPAWN_REP_FACTOR)
    variance = random.uniform(SPAWN_VARIANCE_LOW, SPAWN_VARIANCE_HIGH)

    return random.random() < base_rate * rep_mult * time_mult * event_mult * variance
