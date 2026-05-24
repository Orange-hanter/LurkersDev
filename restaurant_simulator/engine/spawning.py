import random
from ..models import Guest, GUEST_TYPES, GameState
from ..config import (
    SPAWN_BASE_RATE, SPAWN_REP_FACTOR, SPAWN_MULT_MIN,
    SPAWN_VARIANCE_LOW, SPAWN_VARIANCE_HIGH,
    GUEST_BUDGET_MEAN, GUEST_BUDGET_STDDEV, GUEST_BUDGET_MIN,
    GUEST_PATIENCE_MIN_MINUTES, GUEST_PATIENCE_MAX_MINUTES,
    GUEST_BASE_EXPECTATION, GUEST_EXPECTATION_REP_FACTOR,
)


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
    base_patience = random.randint(GUEST_PATIENCE_MIN_MINUTES, GUEST_PATIENCE_MAX_MINUTES)
    patience_ticks = max(1, base_patience // state.tick_minutes)
    base_exp = GUEST_BASE_EXPECTATION * type_info["exp_mult"]
    expectation = base_exp + state.reputation * GUEST_EXPECTATION_REP_FACTOR
    state.guest_queue.append(Guest(guest_type, budget, patience_ticks, expectation))


def should_spawn_guest(state: GameState) -> bool:
    base_rate = SPAWN_BASE_RATE
    if state.rush_hour_active:
        base_rate *= 2
        state.rush_hour_remaining -= 1
        if state.rush_hour_remaining <= 0:
            state.rush_hour_active = False
    rep_mult = max(SPAWN_MULT_MIN, 1 + state.reputation * SPAWN_REP_FACTOR)
    variance = random.uniform(SPAWN_VARIANCE_LOW, SPAWN_VARIANCE_HIGH)
    return random.random() < base_rate * rep_mult * variance
