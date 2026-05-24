from typing import Callable, List, Optional
import random
from ..models import Guest, GameState
from .spawning import spawn_guest


class RandomEvent:
    def __init__(self, event_id: str, weight: int, handler: Callable[[GameState], str]):
        self.id = event_id
        self.weight = weight
        self.handler = handler


def _event_inspector(state: GameState) -> str:
    avg_dur = state.avg_durability_pct
    if avg_dur < 30:
        state.reputation -= 15
        return f"Health Inspector! Equipment in bad shape ({avg_dur:.0f}%). Rep -15"
    elif avg_dur < 60:
        state.reputation -= 5
        return f"Health Inspector: Equipment needs attention ({avg_dur:.0f}%). Rep -5"
    else:
        state.reputation += 5
        return f"Health Inspector: Equipment in great shape! Rep +5"


def _event_rush_hour(state: GameState) -> str:
    state.rush_hour_active = True
    state.rush_hour_remaining = 5
    return "RUSH HOUR! Spawn rate doubled for 5 ticks!"


def _event_equipment_break(state: GameState) -> str:
    equip = random.choice([state.kitchen, state.hall])
    if equip.quality == 0:
        return "Equipment malfunction, but nothing to break!"
    equip.degrade(20)
    return f"{equip.name} malfunction! Durability -20 (now {equip.durability_pct:.0f}%)"


def _event_investor(state: GameState) -> str:
    amount = 50 + state.reputation * 2
    state.budget += amount
    state.reputation += 0.5
    return f"Investor visit! +${amount:.2f}, Rep +0.5"


def _event_party(state: GameState) -> str:
    for _ in range(3):
        spawn_guest(state)
    return "Large party! 3 guests arrived!"


def _event_food_critic(state: GameState) -> str:
    # Critic: budget=0 (no income), patience=0 (served immediately if staff available), expectation=0 (always succeeds)
    # Real impact comes from rep_multiplier=5.0 on success/failure
    state.guest_queue.append(Guest("critic", 0, 0, 0))
    return "Food Critic arrived! High risk, high reward!"


RANDOM_EVENTS: List[RandomEvent] = [
    RandomEvent("inspector", 25, _event_inspector),
    RandomEvent("rush_hour", 20, _event_rush_hour),
    RandomEvent("equipment_break", 15, _event_equipment_break),
    RandomEvent("investor", 15, _event_investor),
    RandomEvent("party", 15, _event_party),
    RandomEvent("food_critic", 10, _event_food_critic),
]


def pick_random_event() -> Optional[RandomEvent]:
    total = sum(e.weight for e in RANDOM_EVENTS)
    roll = random.uniform(0, total)
    cumulative = 0
    for event in RANDOM_EVENTS:
        cumulative += event.weight
        if roll <= cumulative:
            return event
    return None
