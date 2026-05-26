# Game Loop Upgrade Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rewrite the restaurant simulator engine and extend models to achieve full spec compliance with the `gameLoop copy.md` flowchart.

**Architecture:** Engine is split into modules by responsibility: `phases.py` (6 pure phase functions), `economy.py` (pending settlement), `tables.py` (table lifecycle), `spawning.py` (enhanced guest generation), `events.py` (daily + tick events). Models get new `Table` class and field extensions. UI adapts to show tables, staff statuses, and queue priority.

**Tech Stack:** Python 3.12+, pygame, dataclasses

---

### Task 1: Delete legacy files and consumed docs

**Files:**
- Delete: `game.py`
- Delete: `game_v2_FINAL.py`
- Delete: `game_v3.py`
- Delete: `gameLoop copy.md`

- [ ] **Step 1: Delete legacy files**

```bash
rm /Users/dakh/Git/LurkersDev/game.py /Users/dakh/Git/LurkersDev/game_v2_FINAL.py /Users/dakh/Git/LurkersDev/game_v3.py /Users/dakh/Git/LurkersDev/gameLoop\ copy.md
```

- [ ] **Step 2: Commit**

```bash
git -C /Users/dakh/Git/LurkersDev add -u && git -C /Users/dakh/Git/LurkersDev commit -m "chore: remove legacy terminal versions and consumed spec doc"
```

---

### Task 2: Extend config.py

**Files:**
- Modify: `restaurant_simulator/config.py`

- [ ] **Step 1: Replace config.py with extended constants**

Read `restaurant_simulator/config.py` and replace its entire content with:

```python
"""
Game balance constants. Tweak here to rebalance the game.
"""

# Economy
DAILY_SALARY_PER_SKILL = 30
STARTING_BUDGET = 500
REPAIR_COST = 20
REPAIR_AMOUNT = 50

# Win/Lose (bankruptcy)
REP_MIN = -50
REP_MAX = 100
DAILY_EVENT_CHANCE = 0.20
EQUIP_LOW_DURABILITY = 20

# Time
WORK_START_HOUR = 9
WORK_END_HOUR = 21
TOTAL_TICKS_PER_DAY = 100

# Events (tick)
RANDOM_EVENT_CHANCE = 0.08

# Spawning
SPAWN_BASE_RATE = 0.3
SPAWN_REP_FACTOR = 0.01
SPAWN_VARIANCE_LOW = 0.8
SPAWN_VARIANCE_HIGH = 1.2

TIME_OF_DAY_MULTIPLIERS = {
    (0, 20): 0.5,
    (20, 40): 1.5,
    (40, 60): 2.0,
    (60, 80): 1.5,
    (80, 100): 0.5,
}

# Guests
GUEST_BUDGET_MEAN = 40.0
GUEST_BUDGET_STDDEV = 15.0
GUEST_BUDGET_MIN = 5.0
GUEST_PATIENCE_MIN = 3
GUEST_PATIENCE_MAX = 8
GUEST_BASE_EXPECTATION = 3.0
GUEST_EXPECTATION_REP_FACTOR = 0.05

# Service
QUALITY_STAFF_WEIGHT = 0.7
QUALITY_EQUIP_WEIGHT = 0.3
SERVICE_DURATION = 5
SUCCESS_INCOME_MULT = 1.2
SUCCESS_REP_GAIN = 3
FAILURE_COST_MULT = 0.3
FAILURE_REP_LOSS = 10
GUEST_LEFT_REP_LOSS = 2

# Stamina
REST_THRESHOLD = 0.3
REST_RECOVERY_RATE = 2

# Equipment
EQUIP_DEGRADE_PER_SERVICE = 1

# Tables
MAX_TABLES = 20
TABLE_CAPACITIES = {"small": 2, "medium": 4, "large": 6}

# UI (pygame-specific)
WINDOW_WIDTH = 960
WINDOW_HEIGHT = 640
BG_COLOR = (26, 26, 46)
FPS = 60
DEFAULT_TICK_INTERVAL = 0.5

# Equipment shop tiers: (display_name, price, quality, max_durability)
EQUIPMENT_TIERS = {
    0: ("Basic", 50, 1, 80),
    1: ("Standard", 100, 3, 120),
    2: ("Premium", 180, 5, 150),
}
```

- [ ] **Step 2: Commit**

```bash
git -C /Users/dakh/Git/LurkersDev add restaurant_simulator/config.py && git -C /Users/dakh/Git/LurkersDev commit -m "feat: extend config with spec-compliant constants"
```

---

### Task 3: Create Table model

**Files:**
- Create: `restaurant_simulator/models/table.py`

- [ ] **Step 1: Write table.py**

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .guest import Guest
    from .staff import Staff


class Table:
    def __init__(self, table_id: int, capacity: int):
        self.table_id = table_id
        self.capacity = capacity
        self.state = "free"
        self.busy_timer = 0
        self.guest: "Guest | None" = None
        self.staff: "Staff | None" = None

    @property
    def is_free(self) -> bool:
        return self.state == "free"
```

- [ ] **Step 2: Commit**

```bash
git -C /Users/dakh/Git/LurkersDev add restaurant_simulator/models/table.py && git -C /Users/dakh/Git/LurkersDev commit -m "feat: add Table model"
```

---

### Task 4: Extend Staff model

**Files:**
- Modify: `restaurant_simulator/models/staff.py`

- [ ] **Step 1: Rewrite staff.py with status and RestThreshold**

Replace the content of `restaurant_simulator/models/staff.py` with:

```python
from ..config import REST_THRESHOLD, REST_RECOVERY_RATE


class Staff:
    def __init__(self, skill: int, daily_salary: int):
        self.skill = skill
        self.daily_salary = daily_salary
        self.max_stamina = 100
        self.stamina = self.max_stamina
        self.rest_threshold = int(self.max_stamina * REST_THRESHOLD)
        self.status = "ready"
        self.busy_timer = 0

    @property
    def is_ready(self) -> bool:
        return self.status == "ready"

    @property
    def is_free(self) -> bool:
        return self.status in ("ready", "resting") and self.busy_timer == 0

    def assign_service(self, duration: int) -> None:
        self.status = "busy"
        self.busy_timer = duration

    def release(self) -> None:
        self.busy_timer = 0
        self.status = "ready"

    def tick_update(self) -> None:
        if self.status == "busy":
            if self.busy_timer > 0:
                self.busy_timer -= 1
        elif self.status == "resting":
            self.stamina = min(self.max_stamina, self.stamina + REST_RECOVERY_RATE)
```

- [ ] **Step 2: Commit**

```bash
git -C /Users/dakh/Git/LurkersDev add restaurant_simulator/models/staff.py && git -C /Users/dakh/Git/LurkersDev commit -m "feat: extend Staff with status, rest_threshold, fixed recovery"
```

---

### Task 5: Extend Guest model

**Files:**
- Modify: `restaurant_simulator/models/guest.py`

- [ ] **Step 1: Rewrite guest.py with priority and mood**

Replace the content of `restaurant_simulator/models/guest.py` with:

```python
GUEST_TYPES = {
    "regular":  {"weight": 70, "budget_mult": 1.0, "exp_mult": 1.0, "rep_mult": 1.0, "icon": "r", "label": "Regular", "priority": 0},
    "business": {"weight": 20, "budget_mult": 1.5, "exp_mult": 1.2, "rep_mult": 1.5, "icon": "b", "label": "Business", "priority": 0},
    "VIP":      {"weight": 8,  "budget_mult": 2.5, "exp_mult": 1.5, "rep_mult": 2.0, "icon": "V", "label": "VIP", "priority": 1},
    "critic":   {"weight": 2,  "budget_mult": 3.0, "exp_mult": 2.0, "rep_mult": 5.0, "icon": "C", "label": "CRITIC", "priority": 1},
}


class Guest:
    def __init__(self, guest_type: str, budget: float, patience_ticks: int, expectation: float):
        self.guest_type = guest_type
        self.budget = budget
        self.patience_ticks = patience_ticks
        self.expectation = expectation
        self.wait_timer = 0
        self.mood = 1.0
        self.priority = GUEST_TYPES[guest_type]["priority"]

    @property
    def type_info(self) -> dict:
        return GUEST_TYPES[self.guest_type]

    @property
    def icon(self) -> str:
        return self.type_info["icon"]

    @property
    def label(self) -> str:
        return self.type_info["label"]

    @property
    def rep_multiplier(self) -> float:
        return self.type_info["rep_mult"]

    @property
    def expectation_multiplier(self) -> float:
        return self.type_info["exp_mult"]
```

- [ ] **Step 2: Commit**

```bash
git -C /Users/dakh/Git/LurkersDev add restaurant_simulator/models/guest.py && git -C /Users/dakh/Git/LurkersDev commit -m "feat: add priority and mood to Guest"
```

---

### Task 6: Extend Equipment model (step-function penalty)

**Files:**
- Modify: `restaurant_simulator/models/equipment.py`

- [ ] **Step 1: Modify effective_quality to use step-function**

Replace `restaurant_simulator/models/equipment.py` with:

```python
from ..config import EQUIP_LOW_DURABILITY


class Equipment:
    def __init__(self, name: str, quality: int, price: int, max_durability: int = 100):
        self.name = name
        self.quality = quality
        self.price = price
        self.max_durability = max_durability
        self.durability = max_durability

    @property
    def effective_quality(self) -> float:
        if self.durability <= 0:
            return 0.0
        if self.durability < EQUIP_LOW_DURABILITY:
            return self.quality * 0.5
        return float(self.quality)

    @property
    def durability_pct(self) -> float:
        return min(100.0, (self.durability / self.max_durability) * 100) if self.max_durability > 0 else 100.0

    @property
    def needs_repair(self) -> bool:
        return self.durability < EQUIP_LOW_DURABILITY

    def degrade(self, amount: int = 1) -> None:
        self.durability = max(0, self.durability - amount)

    def repair(self, amount: int = 50) -> None:
        self.durability = min(self.max_durability, self.durability + amount)

    def replace(self, new_quality: int, new_price: int, new_max_durability: int) -> None:
        self.quality = new_quality
        self.price = new_price
        self.max_durability = new_max_durability
        self.durability = new_max_durability
```

- [ ] **Step 2: Commit**

```bash
git -C /Users/dakh/Git/LurkersDev add restaurant_simulator/models/equipment.py && git -C /Users/dakh/Git/LurkersDev commit -m "feat: equipment uses step-function quality penalty below 20 durability"
```

---

### Task 7: Extend GameState model

**Files:**
- Modify: `restaurant_simulator/models/game_state.py`

- [ ] **Step 1: Rewrite game_state.py with tables and pending economy**

Replace `restaurant_simulator/models/game_state.py` with:

```python
from typing import List, Dict
from .equipment import Equipment
from .staff import Staff
from .guest import Guest
from .table import Table
from ..config import STARTING_BUDGET, WORK_START_HOUR


class GameState:
    def __init__(self):
        self.budget = STARTING_BUDGET
        self.reputation = 0.0
        self.kitchen = Equipment("Kitchen", 0, 0)
        self.hall = Equipment("Hall", 0, 0)
        self.staff_list: List[Staff] = []
        self.guest_queue: List[Guest] = []
        self.tables: List[Table] = []
        self.tick = 0
        self.total_ticks = 100
        self.start_minute = WORK_START_HOUR * 60
        self.day = 1
        self.day_history: List[Dict] = []
        self.rush_hour_active = False
        self.rush_hour_remaining = 0
        self.day_ended = False

        self.pending_income: float = 0.0
        self.pending_expense: float = 0.0
        self.pending_rep: float = 0.0
        self.guests_served: int = 0
        self.avg_quality: float = 0.0
        self.lost_guests: int = 0
        self.daily_event = None

    @property
    def avg_equipment_quality(self) -> float:
        return (self.kitchen.effective_quality + self.hall.effective_quality) / 2.0

    @property
    def avg_durability_pct(self) -> float:
        total_max = self.kitchen.max_durability + self.hall.max_durability
        if total_max == 0:
            return 100.0
        return ((self.kitchen.durability + self.hall.durability) / total_max) * 100

    def current_time_str(self) -> str:
        minutes = self.start_minute + self.tick * 5
        h = (minutes // 60) % 24
        m = minutes % 60
        return f"{h:02d}:{m:02d}"

    def time_remaining(self) -> int:
        return max(0, self.total_ticks - self.tick)

    def hire_staff(self, skill: int, daily_salary: int) -> None:
        self.staff_list.append(Staff(skill, daily_salary))

    def fire_staff(self, index: int) -> None:
        if 0 <= index < len(self.staff_list):
            self.staff_list.pop(index)

    def reset_daily(self) -> None:
        for table in self.tables:
            table.state = "free"
            table.busy_timer = 0
            table.guest = None
            table.staff = None
        self.guest_queue.clear()
        for staff in self.staff_list:
            staff.status = "ready"
            staff.busy_timer = 0
            staff.stamina = staff.max_stamina
        self.pending_income = 0.0
        self.pending_expense = 0.0
        self.pending_rep = 0.0
        self.guests_served = 0
        self.avg_quality = 0.0
        self.lost_guests = 0
        self.tick = 0
        self.day_ended = False
        self.daily_event = None
```

- [ ] **Step 2: Commit**

```bash
git -C /Users/dakh/Git/LurkersDev add restaurant_simulator/models/game_state.py && git -C /Users/dakh/Git/LurkersDev commit -m "feat: extend GameState with tables, pending economy, daily reset"
```

---

### Task 8: Update models __init__.py

**Files:**
- Modify: `restaurant_simulator/models/__init__.py`

- [ ] **Step 1: Add Table export**

Replace `restaurant_simulator/models/__init__.py` with:

```python
from .equipment import Equipment
from .staff import Staff
from .guest import Guest, GUEST_TYPES
from .game_state import GameState
from .table import Table

__all__ = ["Equipment", "Staff", "Guest", "GUEST_TYPES", "GameState", "Table"]
```

- [ ] **Step 2: Commit**

```bash
git -C /Users/dakh/Git/LurkersDev add restaurant_simulator/models/__init__.py && git -C /Users/dakh/Git/LurkersDev commit -m "feat: export Table from models"
```

---

### Task 9: Create engine/tables.py

**Files:**
- Create: `restaurant_simulator/engine/tables.py`

- [ ] **Step 1: Write tables.py**

```python
from ..models import Table, Guest, Staff


def create_tables(count: int, capacity: int) -> list[Table]:
    return [Table(table_id=i, capacity=capacity) for i in range(count)]


def find_free_table(tables: list[Table]) -> Table | None:
    for t in tables:
        if t.is_free:
            return t
    return None


def allocate_table(table: Table, guest: Guest, staff: Staff, duration: int) -> None:
    table.state = "occupied"
    table.guest = guest
    table.staff = staff
    table.busy_timer = duration


def release_table(table: Table) -> None:
    table.state = "free"
    table.guest = None
    table.staff = None
    table.busy_timer = 0


def find_ready_staff(staff_list: list[Staff]) -> Staff | None:
    for s in staff_list:
        if s.is_ready and s.stamina > s.rest_threshold:
            return s
    return None
```

- [ ] **Step 2: Commit**

```bash
git -C /Users/dakh/Git/LurkersDev add restaurant_simulator/engine/tables.py && git -C /Users/dakh/Git/LurkersDev commit -m "feat: add table management module"
```

---

### Task 10: Create engine/economy.py

**Files:**
- Create: `restaurant_simulator/engine/economy.py`

- [ ] **Step 1: Write economy.py**

```python
from ..models import GameState
from ..config import REP_MIN, REP_MAX


def end_of_day(state: GameState) -> str:
    total_salary = sum(s.daily_salary for s in state.staff_list)
    state.pending_expense += total_salary

    state.budget += state.pending_income
    state.budget -= state.pending_expense
    state.reputation += state.pending_rep

    state.reputation = max(REP_MIN, min(REP_MAX, state.reputation))

    if state.budget <= 0 or state.reputation <= REP_MIN:
        return "bankruptcy"
    return "next_day"
```

- [ ] **Step 2: Commit**

```bash
git -C /Users/dakh/Git/LurkersDev add restaurant_simulator/engine/economy.py && git -C /Users/dakh/Git/LurkersDev commit -m "feat: add pending economy and end-of-day settlement"
```

---

### Task 11: Rewrite engine/events.py

**Files:**
- Rewrite: `restaurant_simulator/engine/events.py`

- [ ] **Step 1: Write events.py with daily events + tick events**

```python
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
```

- [ ] **Step 2: Commit**

```bash
git -C /Users/dakh/Git/LurkersDev add restaurant_simulator/engine/events.py && git -C /Users/dakh/Git/LurkersDev commit -m "feat: rewrite events with daily events + tick events split"
```

---

### Task 12: Rewrite engine/spawning.py

**Files:**
- Rewrite: `restaurant_simulator/engine/spawning.py`

- [ ] **Step 1: Rewrite spawning.py with time-of-day and priority queue**

Replace `restaurant_simulator/engine/spawning.py` with:

```python
import random
import bisect
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


def _insert_by_priority(queue: list[Guest], guest: Guest) -> None:
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
```

- [ ] **Step 2: Commit**

```bash
git -C /Users/dakh/Git/LurkersDev add restaurant_simulator/engine/spawning.py && git -C /Users/dakh/Git/LurkersDev commit -m "feat: rewrite spawning with time-of-day multiplier and priority queue"
```

---

### Task 13: Create engine/phases.py

**Files:**
- Create: `restaurant_simulator/engine/phases.py`

- [ ] **Step 1: Write phases.py with 6 pure phase functions**

```python
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
```

- [ ] **Step 2: Commit**

```bash
git -C /Users/dakh/Git/LurkersDev add restaurant_simulator/engine/phases.py && git -C /Users/dakh/Git/LurkersDev commit -m "feat: add 6-phase tick loop engine"
```

---

### Task 14: Rewrite engine/__init__.py and delete old tick.py

**Files:**
- Rewrite: `restaurant_simulator/engine/__init__.py`
- Delete: `restaurant_simulator/engine/tick.py`

- [ ] **Step 1: Rewrite __init__.py**

```python
from .phases import process_tick, phase_1_update_timers, phase_2_spawn_guests, phase_3_assign_resources, phase_4_service_completion, phase_5_staff_rest, phase_6_tick_end
from .spawning import spawn_guest, should_spawn_guest
from .events import RandomEvent, TICK_EVENTS, DAILY_EVENTS, pick_random_event
from .tables import create_tables, find_free_table, allocate_table, release_table, find_ready_staff
from .economy import end_of_day

__all__ = [
    "process_tick",
    "phase_1_update_timers", "phase_2_spawn_guests", "phase_3_assign_resources",
    "phase_4_service_completion", "phase_5_staff_rest", "phase_6_tick_end",
    "spawn_guest", "should_spawn_guest",
    "RandomEvent", "TICK_EVENTS", "DAILY_EVENTS", "pick_random_event",
    "create_tables", "find_free_table", "allocate_table", "release_table", "find_ready_staff",
    "end_of_day",
]
```

- [ ] **Step 2: Delete old tick.py**

```bash
rm /Users/dakh/Git/LurkersDev/restaurant_simulator/engine/tick.py
```

- [ ] **Step 3: Commit**

```bash
git -C /Users/dakh/Git/LurkersDev add restaurant_simulator/engine/__init__.py && git -C /Users/dakh/Git/LurkersDev add -u && git -C /Users/dakh/Git/LurkersDev commit -m "feat: rewrite engine __init__, delete old tick.py"
```

---

### Task 15: Extend Renderer with table and staff card primitives

**Files:**
- Modify: `restaurant_simulator/ui/renderer.py`

- [ ] **Step 1: Add new drawing methods to renderer.py**

Replace `restaurant_simulator/ui/renderer.py` with:

```python
import pygame
from ..config import BG_COLOR


class Renderer:
    def __init__(self, surface: pygame.Surface):
        self.surface = surface
        self.width, self.height = surface.get_size()
        self.font = pygame.font.SysFont("monospace", 16)
        self.font_bold = pygame.font.SysFont("monospace", 16, bold=True)
        self.font_large = pygame.font.SysFont("monospace", 24, bold=True)
        self.font_small = pygame.font.SysFont("monospace", 14)
        self.font_tiny = pygame.font.SysFont("monospace", 12)
        self.colors = {
            "green": (50, 205, 50),
            "red": (255, 69, 69),
            "yellow": (255, 215, 0),
            "cyan": (0, 255, 255),
            "magenta": (255, 105, 180),
            "white": (255, 255, 255),
            "dim": (150, 150, 150),
            "bar_bg": (60, 60, 60),
            "panel": (40, 40, 60),
            "blue": (70, 130, 255),
        }

    def clear(self) -> None:
        self.surface.fill(BG_COLOR)

    def draw_text(self, text: str, x: int, y: int, color: str = "white", font: str = "normal") -> None:
        f = self.font_bold if font == "bold" else self.font_large if font == "large" else self.font_small if font == "small" else self.font_tiny if font == "tiny" else self.font
        surf = f.render(str(text), True, self.colors.get(color, self.colors["white"]))
        self.surface.blit(surf, (x, y))

    def draw_text_centered(self, text: str, y: int, color: str = "white", font: str = "normal") -> int:
        f = self.font_bold if font == "bold" else self.font_large if font == "large" else self.font_small if font == "small" else self.font
        surf = f.render(str(text), True, self.colors.get(color, self.colors["white"]))
        x = (self.width - surf.get_width()) // 2
        self.surface.blit(surf, (x, y))
        return surf.get_width()

    def text_width(self, text: str, font: str = "normal") -> int:
        f = self.font_bold if font == "bold" else self.font_large if font == "large" else self.font_small if font == "small" else self.font
        return f.render(str(text), True, self.colors["white"]).get_width()

    def draw_progress_bar(self, x: int, y: int, current: float, maximum: float, width: int = 100, height: int = 12) -> None:
        ratio = max(0, min(1, current / maximum)) if maximum > 0 else 0
        filled = int(width * ratio)
        pygame.draw.rect(self.surface, self.colors["bar_bg"], (x, y, width, height))
        if ratio > 0.6:
            color = self.colors["green"]
        elif ratio > 0.3:
            color = self.colors["yellow"]
        else:
            color = self.colors["red"]
        if filled > 0:
            pygame.draw.rect(self.surface, color, (x, y, filled, height))

    def draw_rect(self, x: int, y: int, w: int, h: int, color: str, outline: int = 0) -> None:
        pygame.draw.rect(self.surface, self.colors.get(color, self.colors["white"]), (x, y, w, h), outline)

    def draw_dimmed_overlay(self, alpha: int = 128) -> None:
        overlay = pygame.Surface((self.width, self.height))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(alpha)
        self.surface.blit(overlay, (0, 0))

    def draw_table_sprite(self, x: int, y: int, state: str, busy_pct: float, guest_label: str = "") -> None:
        if state == "free":
            color = self.colors["dim"]
            label = "Free"
        else:
            color = self.colors["green"]
            label = guest_label
        pygame.draw.rect(self.surface, self.colors["panel"], (x, y, 80, 50), 0, 4)
        pygame.draw.rect(self.surface, color, (x, y, 80, 50), 2, 4)
        self.draw_text(label, x + 5, y + 5, "white", "tiny")
        if state == "occupied":
            prog_width = int(76 * busy_pct)
            prog_color = self.colors["green"] if busy_pct > 0.5 else self.colors["yellow"] if busy_pct > 0.25 else self.colors["red"]
            pygame.draw.rect(self.surface, prog_color, (x + 2, y + 38, prog_width, 4))

    def draw_staff_card(self, x: int, y: int, staff, width: int = 180) -> None:
        pygame.draw.rect(self.surface, self.colors["panel"], (x, y, width, 50), 0, 4)
        status_colors = {"ready": "green", "busy": "yellow", "resting": "blue"}
        sc = status_colors.get(staff.status, "red")
        pygame.draw.rect(self.surface, self.colors[sc], (x, y, 4, 50), 0, 4, 0, 0, 4, 0)
        self.draw_text(f"Sk={staff.skill} {staff.status.upper()}", x + 10, y + 3, "white", "tiny")
        self.draw_progress_bar(x + 10, y + 22, staff.stamina, staff.max_stamina, width - 20, 8)
        self.draw_text(f"${staff.daily_salary}/d", x + 10, y + 35, "dim", "tiny")

    def draw_phase_indicator(self, phase: int) -> None:
        names = {1: "Timers", 2: "Spawn", 3: "Assign", 4: "Serve", 5: "Rest", 6: "End"}
        self.draw_text(f"Phase: {names.get(phase, '?')}", self.width - 120, self.height - 18, "dim", "tiny")
```

- [ ] **Step 2: Commit**

```bash
git -C /Users/dakh/Git/LurkersDev add restaurant_simulator/ui/renderer.py && git -C /Users/dakh/Git/LurkersDev commit -m "feat: add table and staff card drawing primitives to renderer"
```

---

### Task 16: Rewrite UI screens

**Files:**
- Rewrite: `restaurant_simulator/ui/screens.py`

- [ ] **Step 1: Rewrite screens.py with table setup, table display, queue cards, expanded summary**

Replace `restaurant_simulator/ui/screens.py` with:

```python
import pygame
import random
from typing import List
from ..models import GameState
from ..config import (
    WINDOW_WIDTH, WINDOW_HEIGHT, WORK_START_HOUR, WORK_END_HOUR,
    REPAIR_COST, DAILY_SALARY_PER_SKILL, EQUIPMENT_TIERS, STARTING_BUDGET,
    TOTAL_TICKS_PER_DAY, MAX_TABLES, TABLE_CAPACITIES,
    REP_MIN, EQUIP_LOW_DURABILITY,
)
from .renderer import Renderer
from .input_handler import InputHandler


class Screen:
    base_class = True
    def __init__(self, renderer: Renderer, input_handler: InputHandler):
        self.renderer = renderer
        self.input = input_handler
        self.running = True
        self.result = None

    def handle_events(self, events: List[pygame.event.Event]) -> None:
        self.input.handle_events(events)

    def update(self, dt: float) -> None:
        pass

    def render(self) -> None:
        pass

    def exit(self) -> None:
        self.running = False


class MainMenu(Screen):
    def __init__(self, renderer: Renderer, input_handler: InputHandler):
        super().__init__(renderer, input_handler)
        self.input.register_key(pygame.K_RETURN, self._start)
        self.input.register_key(pygame.K_SPACE, self._start)

    def _start(self) -> None:
        self.result = "start"
        self.exit()

    def render(self) -> None:
        self.renderer.clear()
        self.renderer.draw_text_centered("Restaurant Simulator v5", 200, "cyan", "large")
        self.renderer.draw_text_centered("Manage your restaurant across multiple days!", 250, "dim", "small")
        self.renderer.draw_text_centered("Press ENTER or SPACE to start", 400, "green", "bold")
        self.renderer.draw_text_centered("ESC to quit", 430, "dim", "small")
        self.renderer.draw_text_centered("Controls: +/- Speed  Space Pause  M Music", 500, "dim", "small")


class DaySetupScreen(Screen):
    def __init__(self, renderer: Renderer, input_handler: InputHandler, state: GameState, is_first_day: bool):
        super().__init__(renderer, input_handler)
        self.state = state
        self.is_first_day = is_first_day
        self.selection = 5
        self.table_count = 5
        self.table_capacity = "medium"
        self.cap_keys = list(TABLE_CAPACITIES.keys())
        self.cap_index = 1
        self.focus = "tick"

        self.input.register_key(pygame.K_UP, self._up)
        self.input.register_key(pygame.K_DOWN, self._down)
        self.input.register_key(pygame.K_LEFT, self._left)
        self.input.register_key(pygame.K_RIGHT, self._right)
        self.input.register_key(pygame.K_TAB, self._tab)
        self.input.register_key(pygame.K_RETURN, self._confirm)

    def _up(self) -> None:
        if self.focus == "tick":
            idx = [1, 5, 10, 15, 30].index(self.selection)
            self.selection = [1, 5, 10, 15, 30][max(0, idx - 1)]
        elif self.focus == "tables":
            self.table_count = min(MAX_TABLES, self.table_count + 1)
        elif self.focus == "capacity":
            self.cap_index = min(len(self.cap_keys) - 1, self.cap_index + 1)
            self.table_capacity = self.cap_keys[self.cap_index]

    def _down(self) -> None:
        if self.focus == "tick":
            idx = [1, 5, 10, 15, 30].index(self.selection)
            self.selection = [1, 5, 10, 15, 30][min(4, idx + 1)]
        elif self.focus == "tables":
            self.table_count = max(1, self.table_count - 1)
        elif self.focus == "capacity":
            self.cap_index = max(0, self.cap_index - 1)
            self.table_capacity = self.cap_keys[self.cap_index]

    def _left(self) -> None:
        if self.focus == "tables":
            self.table_count = max(1, self.table_count - 1)

    def _right(self) -> None:
        if self.focus == "tables":
            self.table_count = min(MAX_TABLES, self.table_count + 1)

    def _tab(self) -> None:
        options = ["tick", "tables", "capacity"]
        idx = options.index(self.focus)
        self.focus = options[(idx + 1) % len(options)]

    def _confirm(self) -> None:
        self.state.total_ticks = TOTAL_TICKS_PER_DAY
        from ..engine import create_tables
        capacity = TABLE_CAPACITIES[self.table_capacity]
        self.state.tables = create_tables(self.table_count, capacity)
        self.result = self.selection
        self.exit()

    def render(self) -> None:
        self.renderer.clear()
        self.renderer.draw_text_centered("Day Setup", 80, "cyan", "large")

        tc = "green" if self.focus == "tick" else "white"
        self.renderer.draw_text_centered(f"{'>' if self.focus == 'tick' else ' '} Tick Duration: {self.selection} min", 160, tc)
        self.renderer.draw_text_centered(f"  ({TOTAL_TICKS_PER_DAY} ticks/day)", 185, "dim", "small")

        tblc = "green" if self.focus == "tables" else "white"
        self.renderer.draw_text_centered(f"{'>' if self.focus == 'tables' else ' '} Tables: {self.table_count} (1-{MAX_TABLES})", 230, tblc)

        caplc = "green" if self.focus == "capacity" else "white"
        cap = TABLE_CAPACITIES[self.table_capacity]
        self.renderer.draw_text_centered(f"{'>' if self.focus == 'capacity' else ' '} Seating: {self.table_capacity} ({cap} seats)", 270, caplc)

        self.renderer.draw_text_centered("UP/DOWN/LEFT/RIGHT to adjust, TAB to switch, ENTER to confirm", 450, "dim", "small")
        if not self.is_first_day:
            self.renderer.draw_text_centered(f"Carrying over: Budget=${self.state.budget:.2f} Rep={self.state.reputation:.0f}", 500, "yellow", "small")


class GameScreen(Screen):
    def __init__(self, renderer: Renderer, input_handler: InputHandler, state: GameState):
        super().__init__(renderer, input_handler)
        self.state = state
        self.event_log: List[str] = []
        self.paused = False
        self.game_speed = 1.0
        self.music_muted = False
        self.current_phase = 1
        self.pending_action = None

        self.input.register_key(pygame.K_SPACE, self._toggle_pause)
        self.input.register_key(pygame.K_EQUALS, self._speed_up)
        self.input.register_key(pygame.K_MINUS, self._slow_down)
        self.input.register_key(pygame.K_m, self._toggle_music)
        self.input.register_key(pygame.K_s, self._open_shop)
        self.input.register_key(pygame.K_h, self._open_hire)
        self.input.register_key(pygame.K_q, self._quit_day)

    def _toggle_pause(self) -> None: self.paused = not self.paused
    def _speed_up(self) -> None: self.game_speed = min(4.0, self.game_speed * 1.5)
    def _slow_down(self) -> None: self.game_speed = max(0.25, self.game_speed / 1.5)
    def _toggle_music(self) -> None: self.music_muted = not self.music_muted
    def _open_shop(self) -> None: self.pending_action = "shop"
    def _open_hire(self) -> None: self.pending_action = "hire"
    def _quit_day(self) -> None:
        self.result = "quit_day"
        self.exit()

    def log_event(self, message: str) -> None:
        self.event_log.append(message)
        self.event_log = self.event_log[-15:]

    def render(self) -> None:
        self.renderer.clear()
        s = self.state

        speed_label = "PAUSED" if self.paused else f"{self.game_speed:.1f}x"
        speed_color = "yellow" if self.paused else "green"
        self.renderer.draw_rect(0, 0, WINDOW_WIDTH, 28, "bar_bg")
        pending_str = f" P+I${s.pending_income:.1f} -E${s.pending_expense:.1f} R{s.pending_rep:+.0f}"
        self.renderer.draw_text(f"Day {s.day} | {s.current_time_str()} | T {s.tick}/{s.total_ticks} | ${s.budget:.2f} | Rep {s.reputation:+.0f} | {speed_label}", 5, 5, speed_color, "bold")

        self.renderer.draw_text("Tables:", 10, 40, "cyan", "bold")
        bx, by = 10, 60
        cols = 5
        for i, table in enumerate(s.tables):
            col = i % cols
            row = i // cols
            tx = bx + col * 90
            ty = by + row * 60
            busy_pct = 0
            guest_label = ""
            if table.state == "occupied" and table.busy_timer > 0:
                busy_pct = (table.busy_timer / 5) if table.busy_timer <= 5 else 1.0
                guest_label = table.guest.label[:4] if table.guest else "?"
            self.renderer.draw_table_sprite(tx, ty, table.state, busy_pct, guest_label)
            if table.state == "occupied":
                self.renderer.draw_text(f"T:{table.busy_timer}", tx + 30, ty + 22, "yellow", "tiny")

        queue_x = 490
        self.renderer.draw_text("Queue:", queue_x, 40, "cyan", "bold")
        for i, guest in enumerate(s.guest_queue[:8]):
            gy = 60 + i * 35
            prio = "V" if guest.priority > 0 else " "
            self.renderer.draw_text(f"{prio}{guest.icon} {guest.label} W:{guest.wait_timer}/{guest.patience_ticks}", queue_x, gy, "white", "small")
            self.renderer.draw_progress_bar(queue_x + 140, gy, guest.wait_timer, guest.patience_ticks, 50, 8)

        staff_x = 10
        staff_y = WINDOW_HEIGHT - 280
        self.renderer.draw_text("Staff:", staff_x, staff_y - 18, "cyan", "bold")
        for i, staff in enumerate(s.staff_list):
            sx = staff_x + i * 100
            self.renderer.draw_staff_card(sx, staff_y + 10, staff, 90)

        equip_x = 490
        equip_y = WINDOW_HEIGHT - 280
        self.renderer.draw_text("Equipment:", equip_x, equip_y - 18, "cyan", "bold")
        self.renderer.draw_text(f"Kitchen Q={s.kitchen.effective_quality:.1f}", equip_x, equip_y + 5, "white", "small")
        self.renderer.draw_progress_bar(equip_x, equip_y + 20, s.kitchen.durability, s.kitchen.max_durability, 150, 10)
        kw = "!" if s.kitchen.needs_repair else ""
        if kw:
            self.renderer.draw_text(f"{kw} LOW!", equip_x + 155, equip_y + 18, "red", "tiny")

        self.renderer.draw_text(f"Hall Q={s.hall.effective_quality:.1f}", equip_x, equip_y + 40, "white", "small")
        self.renderer.draw_progress_bar(equip_x, equip_y + 55, s.hall.durability, s.hall.max_durability, 150, 10)
        hw = "!" if s.hall.needs_repair else ""
        if hw:
            self.renderer.draw_text(f"{hw} LOW!", equip_x + 155, equip_y + 53, "red", "tiny")

        log_y = WINDOW_HEIGHT - 150
        self.renderer.draw_text("Log:", 10, log_y, "cyan", "bold")
        for i, msg in enumerate(self.event_log[-6:]):
            color = "white"
            if "Success" in msg:
                color = "green"
            elif "Failed" in msg or "malfunction" in msg:
                color = "red"
            elif "left" in msg.lower() or "Left" in msg:
                color = "yellow"
            self.renderer.draw_text(f"  {msg}", 10, log_y + 18 + i * 16, color, "tiny")

        self.renderer.draw_text("Space:Pause  +/-:Speed  M:Music  S:Shop  H:Hire  Q:End  ESC:Quit", 10, WINDOW_HEIGHT - 15, "dim", "tiny")
        self.renderer.draw_phase_indicator(self.current_phase)


class ShopScreen(Screen):
    def __init__(self, renderer: Renderer, input_handler: InputHandler, state: GameState):
        super().__init__(renderer, input_handler)
        self.state = state
        self.cursor = 0
        self.tier_keys = list(EQUIPMENT_TIERS.keys())
        self.slot = "kitchen"
        self.input.register_key(pygame.K_UP, self._prev)
        self.input.register_key(pygame.K_DOWN, self._next)
        self.input.register_key(pygame.K_RETURN, self._buy)
        self.input.register_key(pygame.K_ESCAPE, self._cancel)
        self.input.register_key(pygame.K_r, self._repair)
        self.input.register_key(pygame.K_k, self._switch_kitchen)
        self.input.register_key(pygame.K_l, self._switch_hall)

    def _prev(self) -> None: self.cursor = max(0, self.cursor - 1)
    def _next(self) -> None: self.cursor = min(len(self.tier_keys) - 1, self.cursor + 1)
    def _switch_kitchen(self) -> None: self.slot = "kitchen"
    def _switch_hall(self) -> None: self.slot = "hall"

    def _buy(self) -> None:
        name, price, quality, max_dur = EQUIPMENT_TIERS[self.cursor]
        if self.state.budget >= price:
            self.state.budget -= price
            equip = getattr(self.state, self.slot)
            equip.replace(quality, price, max_dur)
            self.result = "bought"
            self.exit()

    def _repair(self) -> None:
        equip = getattr(self.state, self.slot)
        if self.state.budget >= REPAIR_COST and equip.durability < equip.max_durability:
            self.state.budget -= REPAIR_COST
            equip.repair()
            self.result = "repaired"
            self.exit()

    def _cancel(self) -> None:
        self.result = "cancelled"
        self.exit()

    def render(self) -> None:
        self.renderer.clear()
        self.renderer.draw_dimmed_overlay()
        self.renderer.draw_text_centered("Equipment Shop", 100, "cyan", "large")
        self.renderer.draw_text_centered(f"Budget: ${self.state.budget:.2f}", 140, "green", "bold")
        self.renderer.draw_text_centered("K: Kitchen  L: Hall  R: Repair  ESC: Close", 175, "dim", "small")
        equip = getattr(self.state, self.slot)
        self.renderer.draw_text_centered(f"Current: {self.slot.title()} Q={equip.effective_quality:.1f} Dur={equip.durability_pct:.0f}%", 200, "white", "small")
        self.renderer.draw_text_centered("Note: Quality halves when durability < 20", 225, "red", "small")
        for i, (name, price, quality, max_dur) in EQUIPMENT_TIERS.items():
            color = "green" if i == self.cursor else "white"
            prefix = "> " if i == self.cursor else "  "
            self.renderer.draw_text_centered(f"{prefix}{name}: ${price} | Q={quality} | Dur={max_dur}", 270 + i * 40, color)
        self.renderer.draw_text_centered("UP/DOWN select, ENTER buy, R repair", 440, "dim", "small")


class HireScreen(Screen):
    def __init__(self, renderer: Renderer, input_handler: InputHandler, state: GameState):
        super().__init__(renderer, input_handler)
        self.state = state
        self.candidate_skill = random.randint(1, 10)
        self.candidate_salary = self.candidate_skill * DAILY_SALARY_PER_SKILL
        self.input.register_key(pygame.K_y, self._hire)
        self.input.register_key(pygame.K_n, self._skip)
        self.input.register_key(pygame.K_ESCAPE, self._cancel)
        self.input.register_key(pygame.K_r, self._reroll)

    def _hire(self) -> None:
        if self.state.budget >= self.candidate_salary:
            self.state.hire_staff(self.candidate_skill, self.candidate_salary)
            self.result = "hired"
            self.exit()

    def _skip(self) -> None: self._reroll()

    def _reroll(self) -> None:
        self.candidate_skill = random.randint(1, 10)
        self.candidate_salary = self.candidate_skill * DAILY_SALARY_PER_SKILL

    def _cancel(self) -> None:
        self.result = "cancelled"
        self.exit()

    def render(self) -> None:
        self.renderer.clear()
        self.renderer.draw_dimmed_overlay()
        self.renderer.draw_text_centered("Hire Staff", 150, "cyan", "large")
        self.renderer.draw_text_centered(f"Skill: {self.candidate_skill}", 220, "white", "large")
        self.renderer.draw_text_centered(f"Salary: ${self.candidate_salary}/day (lump sum at end of day)", 260, "yellow", "bold")
        self.renderer.draw_text_centered(f"Stamina recovery: +2/tick when resting (threshold 30%)", 300, "white", "small")
        self.renderer.draw_text_centered("Y: Hire  N/R: New Candidate  ESC: Close", 380, "dim", "small")


class DaySummaryScreen(Screen):
    def __init__(self, renderer: Renderer, input_handler: InputHandler, state: GameState):
        super().__init__(renderer, input_handler)
        self.state = state
        self.result = "next_day"
        self.input.register_key(pygame.K_RETURN, self._continue)
        self.input.register_key(pygame.K_ESCAPE, self._quit)

    def _continue(self) -> None:
        self.result = "next_day"
        self.exit()

    def _quit(self) -> None:
        self.result = "quit"
        self.exit()

    def render(self) -> None:
        self.renderer.clear()
        s = self.state

        self.renderer.draw_text_centered(f"Day {s.day} Summary", 50, "cyan", "large")

        if s.day_history:
            start = s.day_history[-1]["start_budget"]
        else:
            start = STARTING_BUDGET
        profit = s.budget - start

        self.renderer.draw_text_centered(f"Budget: ${start:.2f} -> ${s.budget:.2f} ({'+' if profit >= 0 else ''}${profit:.2f})", 90, "green" if profit >= 0 else "red", "bold")

        rep_start = s.day_history[-1]["start_reputation"] if s.day_history else 0
        self.renderer.draw_text_centered(f"Reputation: {rep_start:+.0f} -> {s.reputation:+.0f} (clamped [{REP_MIN}, 100])", 120, "yellow")

        avg_q = (s.avg_quality / s.guests_served) if s.guests_served > 0 else 0
        served_income = s.pending_income if hasattr(s, 'pending_income') else 0
        served_expense = s.pending_expense if hasattr(s, 'pending_expense') else 0

        self.renderer.draw_text_centered(f"Served: {s.guests_served} | Lost: {s.lost_guests} | Avg Quality: {avg_q:.1f}", 160, "white", "small")
        salary_total = sum(st.daily_salary for st in s.staff_list)
        self.renderer.draw_text_centered(f"Income +${served_income:.2f} | Expenses -${served_expense:.2f} | Salaries -${salary_total:.2f}", 185, "white", "small")
        self.renderer.draw_text_centered(f"Kitchen Q={s.kitchen.effective_quality:.1f} ({s.kitchen.durability_pct:.0f}%) | Hall Q={s.hall.effective_quality:.1f} ({s.hall.durability_pct:.0f}%) | Staff: {len(s.staff_list)}", 220, "dim", "small")

        if s.kitchen.needs_repair or s.hall.needs_repair:
            self.renderer.draw_text_centered("WARNING: Equipment durability critical! Quality halved.", 250, "red", "bold")

        if s.budget <= 0 or s.reputation <= REP_MIN:
            self.renderer.draw_text_centered("BANKRUPT! GAME OVER", 310, "red", "large")
            self.result = "quit"
        else:
            self.renderer.draw_text_centered("ENTER: Next Day  ESC: Quit", 380, "dim", "small")
```

- [ ] **Step 2: Commit**

```bash
git -C /Users/dakh/Git/LurkersDev add restaurant_simulator/ui/screens.py && git -C /Users/dakh/Git/LurkersDev commit -m "feat: rewrite screens with table setup, expanded game view, enhanced summary"
```

---

### Task 17: Rewrite main.py

**Files:**
- Rewrite: `restaurant_simulator/main.py`

- [ ] **Step 1: Rewrite main.py with daily events, pending economy, 6-phase tick, phase tracking**

Replace `restaurant_simulator/main.py` with:

```python
import pygame
from .config import WINDOW_WIDTH, WINDOW_HEIGHT, FPS, DEFAULT_TICK_INTERVAL, DAILY_EVENT_CHANCE, TOTAL_TICKS_PER_DAY
from .models import GameState
from .ui import Renderer, InputHandler, MainMenu, DaySetupScreen, GameScreen, DaySummaryScreen, ShopScreen, HireScreen
from .audio import MusicPlayer
from .engine import process_tick, DAILY_EVENTS, TICK_EVENTS, pick_random_event, end_of_day


class _ScreenSwitch(Exception):
    def __init__(self, screen):
        self.screen = screen


def _record_snapshot(state: GameState) -> None:
    state.day_history.append({
        "day": state.day,
        "start_budget": state.budget,
        "end_budget": state.budget,
        "start_reputation": state.reputation,
        "end_reputation": state.reputation,
        "kitchen": state.kitchen,
        "hall": state.hall,
        "staff_list": state.staff_list,
    })


def _transition(screen, renderer, state, is_first_day):
    if isinstance(screen, MainMenu):
        if screen.result == "start":
            return DaySetupScreen(renderer, InputHandler(), GameState(), True), True

    elif isinstance(screen, DaySetupScreen):
        if not is_first_day:
            return DaySetupScreen(renderer, InputHandler(), state, is_first_day), is_first_day
        return ShopScreen(renderer, InputHandler(), state), is_first_day

    elif isinstance(screen, ShopScreen):
        if screen.result == "cancelled" and is_first_day:
            return MainMenu(renderer, InputHandler()), is_first_day
        if not state.staff_list:
            return HireScreen(renderer, InputHandler(), state), is_first_day
        _record_snapshot(state)
        return GameScreen(renderer, InputHandler(), state), is_first_day

    elif isinstance(screen, HireScreen):
        if screen.result == "cancelled" and not state.staff_list:
            return MainMenu(renderer, InputHandler()), is_first_day
        _record_snapshot(state)
        return GameScreen(renderer, InputHandler(), state), is_first_day

    elif isinstance(screen, GameScreen):
        if state.day_history:
            state.day_history[-1]["end_budget"] = state.budget
            state.day_history[-1]["end_reputation"] = state.reputation
        return DaySummaryScreen(renderer, InputHandler(), state), is_first_day

    elif isinstance(screen, DaySummaryScreen):
        if screen.result == "next_day":
            state.day += 1
            state.reputation = int(state.reputation * 0.8)
            return DaySetupScreen(renderer, InputHandler(), state, False), False
        return None, is_first_day

    return screen, is_first_day


def _start_day(state: GameState) -> str:
    state.reset_daily()

    if random.random() < DAILY_EVENT_CHANCE:
        daily_event = pick_random_event(DAILY_EVENTS)
        if daily_event:
            msg = daily_event.handler(state)
            return msg
    return ""


def main() -> None:
    import random
    pygame.init()
    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
    screen_surface = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Restaurant Simulator v5")
    clock = pygame.time.Clock()

    renderer = Renderer(screen_surface)
    music = MusicPlayer()
    state = GameState()
    is_first_day = True

    current_screen = MainMenu(renderer, InputHandler())
    elapsed = 0.0
    tick_interval = DEFAULT_TICK_INTERVAL

    while True:
        dt = clock.tick(FPS) / 1000.0

        try:
            events = pygame.event.get()
            current_screen.handle_events(events)
        except SystemExit:
            break

        current_screen.update(dt)
        current_screen.render()
        pygame.display.flip()

        if not current_screen.running:
            next_screen, is_first_day = _transition(current_screen, renderer, state, is_first_day)

            if next_screen is None:
                break

            current_screen = next_screen

            if isinstance(current_screen, GameScreen):
                elapsed = 0.0
                tick_interval = DEFAULT_TICK_INTERVAL
                daily_msg = _start_day(state)
                if daily_msg:
                    current_screen.log_event(daily_msg)
                music.play_tune("day_theme")
            elif isinstance(current_screen, (MainMenu, DaySummaryScreen)):
                music.stop()

        if isinstance(current_screen, GameScreen) and not current_screen.paused:
            elapsed += dt * current_screen.game_speed
            if elapsed >= tick_interval:
                evts = process_tick(state)
                for e in evts:
                    if e["type"] == "event":
                        current_screen.log_event(e["message"])
                    elif e["type"] == "success":
                        g = e["guest"]
                        current_screen.log_event(f"{g.icon} Success! {g.label} Q={e['quality']:.1f} +${e['income']:.2f} Rep+{e['rep_gain']}")
                    elif e["type"] == "failure":
                        g = e["guest"]
                        current_screen.log_event(f"{g.icon} Failed! {g.label} Q={e['quality']:.1f} -${e['loss']:.2f} Rep-{e['rep_loss']}")
                    elif e["type"] == "left":
                        g = e["guest"]
                        current_screen.log_event(f"{g.icon} {g.label} left (waited {g.wait_timer}/{g.patience_ticks}) Rep-{e['rep_loss']}")
                    elif e["type"] == "warning":
                        current_screen.log_event(f"WARNING: {e['message']}")
                    elif e["type"] == "spawn":
                        g = e["guest"]
                        current_screen.log_event(f"{g.icon} {g.label} arrived! B=${g.budget:.0f}")
                    elif e["type"] == "day_end":
                        result = end_of_day(state)
                        if result == "bankruptcy":
                            current_screen.log_event("DAY OVER - BANKRUPTCY!")
                        current_screen.result = "quit_day"
                        current_screen.exit()
                elapsed = 0

                current_screen.current_phase = ((state.tick - 1) % 6) + 1

            if isinstance(current_screen, GameScreen) and current_screen.pending_action and current_screen.running:
                action = current_screen.pending_action
                current_screen.pending_action = None
                if action == "shop":
                    current_screen = ShopScreen(renderer, InputHandler(), state)
                elif action == "hire":
                    current_screen = HireScreen(renderer, InputHandler(), state)

            if isinstance(current_screen, (ShopScreen, HireScreen)) and not current_screen.running:
                current_screen = GameScreen(renderer, InputHandler(), state)

            if isinstance(current_screen, GameScreen) and music.playing:
                if state.rush_hour_active and music.current_tune != "rush_hour":
                    music.play_tune("rush_hour")
                elif not state.rush_hour_active and music.current_tune != "day_theme":
                    music.play_tune("day_theme")
                if music.muted != current_screen.music_muted:
                    music.set_muted(current_screen.music_muted)

            # Roll tick events
            if isinstance(current_screen, GameScreen) and not current_screen.paused and elapsed == 0:
                from .config import RANDOM_EVENT_CHANCE
                if random.random() < RANDOM_EVENT_CHANCE:
                    tick_event = pick_random_event(TICK_EVENTS)
                    if tick_event:
                        result = tick_event.handler(state)
                        current_screen.log_event(result)

    music.stop()
    pygame.quit()
```

- [ ] **Step 2: Commit**

```bash
git -C /Users/dakh/Git/LurkersDev add restaurant_simulator/main.py && git -C /Users/dakh/Git/LurkersDev commit -m "feat: rewrite main.py with daily events, 6-phase tick, pending economy, phase tracking"
```

---

### Task 18: Run lint and verify

- [ ] **Step 1: Run Python syntax check on all new/modified files**

```bash
cd /Users/dakh/Git/LurkersDev && python -m py_compile restaurant_simulator/config.py && python -m py_compile restaurant_simulator/models/table.py && python -m py_compile restaurant_simulator/models/staff.py && python -m py_compile restaurant_simulator/models/guest.py && python -m py_compile restaurant_simulator/models/equipment.py && python -m py_compile restaurant_simulator/models/game_state.py && python -m py_compile restaurant_simulator/engine/tables.py && python -m py_compile restaurant_simulator/engine/economy.py && python -m py_compile restaurant_simulator/engine/events.py && python -m py_compile restaurant_simulator/engine/spawning.py && python -m py_compile restaurant_simulator/engine/phases.py && python -m py_compile restaurant_simulator/main.py
```

Expected: No output (all compile successfully).

- [ ] **Step 2: Attempt to import the package**

```bash
cd /Users/dakh/Git/LurkersDev && python -c "from restaurant_simulator.models import Table, GameState, Staff, Guest, GUEST_TYPES, Equipment; from restaurant_simulator.engine import process_tick, end_of_day, create_tables, DAILY_EVENTS, TICK_EVENTS; print('All imports OK')"
```

Expected: `All imports OK`

- [ ] **Step 3: Commit if needed**

```bash
git -C /Users/dakh/Git/LurkersDev add -A && git -C /Users/dakh/Git/LurkersDev commit -m "chore: final verification pass"
```
