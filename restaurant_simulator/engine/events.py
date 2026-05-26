import random
from ..models import GameState
from .spawning import spawn_guest


class RandomEvent:
    def __init__(self, event_id: str, weight: int, handler):
        self.id = event_id
        self.weight = weight
        self.handler = handler
        self.spawn_mult = 1.0
        self.quality_mult = 1.0


def _event_inspector(state: GameState) -> str:
    avg_dur = state.avg_durability_pct
    if avg_dur < 30:
        state.reputation -= 15
        return f"Health Inspector! Equipment in bad shape ({avg_dur:.0f}%). Rep -15"
    elif avg_dur < 60:
        state.reputation -= 5
        return f"Health Inspector: Needs attention ({avg_dur:.0f}%). Rep -5"
    else:
        state.reputation += 5
        return f"Health Inspector: Great shape! Rep +5"


def _event_rush_hour(state: GameState) -> str:
    state.rush_hour_active = True
    state.rush_hour_remaining = 5
    return "RUSH HOUR! Spawn rate doubled for 5 ticks!"


def _event_equipment_break(state: GameState) -> str:
    equip = random.choice([state.kitchen, state.hall])
    if equip.quality == 0:
        return "Equipment malfunction, but nothing to break!"
    equip.degrade(20)
    return f"{equip.name} malfunction! Durability -20"


def _event_investor(state: GameState) -> str:
    amount = 50 + state.reputation * 2
    state.budget += amount
    state.reputation += 0.5
    return f"Investor! +${amount:.2f}, Rep +0.5"


def _event_party(state: GameState) -> str:
    for _ in range(3):
        spawn_guest(state)
    return "Large party! 3 guests arrived!"


def _event_food_critic(state: GameState) -> str:
    from ..models import Guest
    state.guest_queue.append(Guest("critic", 0, 0, 0))
    return "Food Critic arrived!"


TICK_EVENTS = [
    RandomEvent("inspector", 25, _event_inspector),
    RandomEvent("rush_hour", 20, _event_rush_hour),
    RandomEvent("equipment_break", 15, _event_equipment_break),
    RandomEvent("investor", 15, _event_investor),
    RandomEvent("party", 15, _event_party),
    RandomEvent("food_critic", 10, _event_food_critic),
]


def _daily_health_inspection(state: GameState) -> str:
    avg_dur = state.avg_durability_pct
    if avg_dur < 30:
        state.pending_rep -= 15
        return "Daily: Health Inspector! Equipment bad shape. Rep -15 pending."
    elif avg_dur < 60:
        state.pending_rep -= 5
        return "Daily: Health Inspector. Needs attention. Rep -5 pending."
    else:
        state.pending_rep += 5
        return "Daily: Health Inspector. Great shape! Rep +5 pending."


def _daily_vip_guest(state: GameState) -> str:
    state.daily_event = RandomEvent("vip_guest", 0, None)
    state.daily_event.spawn_mult = 1.0
    state.daily_event.quality_mult = 0.8
    return "Daily: VIP Guest expected today! Higher standards."


def _daily_equipment_breakdown(state: GameState) -> str:
    equip = random.choice([state.kitchen, state.hall])
    if equip.quality == 0:
        return "Daily: Equipment breakdown, but nothing to break!"
    equip.degrade(30)
    return f"Daily: {equip.name} broke down overnight! Durability -30"


def _daily_good_press(state: GameState) -> str:
    state.daily_event = RandomEvent("good_press", 0, None)
    state.daily_event.spawn_mult = 1.5
    state.daily_event.quality_mult = 1.0
    state.pending_rep += 5
    return "Daily: Good press! More guests, +5 Rep pending."


DAILY_EVENTS = [
    RandomEvent("health_inspection", 25, _daily_health_inspection),
    RandomEvent("vip_guest", 25, _daily_vip_guest),
    RandomEvent("equipment_breakdown", 25, _daily_equipment_breakdown),
    RandomEvent("good_press", 25, _daily_good_press),
]


def pick_random_event(events) -> RandomEvent | None:
    total = sum(e.weight for e in events)
    roll = random.uniform(0, total)
    cumulative = 0
    for event in events:
        cumulative += event.weight
        if roll <= cumulative:
            return event
    return None
