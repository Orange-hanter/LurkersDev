# Restaurant Simulator v4 — pygame Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refactor the restaurant simulator from a single-file terminal game into a pygame-based application with continuous real-time gameplay, adjustable speed, and procedural 8-bit chiptune music.

**Architecture:** pygame game loop at 60 FPS with tick-based simulation running on elapsed time. State machine manages screen transitions. Domain models unchanged from v3. UI rendered on pygame surfaces. Audio generated via numpy + pygame.mixer.

**Tech Stack:** pygame 2.6+, numpy 2.2+, Python 3.13

---

## File Structure Map

| File | Responsibility |
|------|---------------|
| `restaurant_simulator/__main__.py` | Entry point (`python -m restaurant_simulator`) |
| `restaurant_simulator/config.py` | Game balance constants (migrated from v3 Config class) |
| `restaurant_simulator/models/__init__.py` | Package init |
| `restaurant_simulator/models/equipment.py` | Equipment class |
| `restaurant_simulator/models/staff.py` | Staff class |
| `restaurant_simulator/models/guest.py` | Guest class + GUEST_TYPES |
| `restaurant_simulator/models/game_state.py` | GameState class |
| `restaurant_simulator/engine/__init__.py` | Package init |
| `restaurant_simulator/engine/tick.py` | process_tick(state) → List[dict] |
| `restaurant_simulator/engine/events.py` | RandomEvent + handlers |
| `restaurant_simulator/engine/spawning.py` | Guest spawning logic |
| `restaurant_simulator/ui/__init__.py` | Package init |
| `restaurant_simulator/ui/renderer.py` | Pygame drawing utilities (text, bars, colors) |
| `restaurant_simulator/ui/screens.py` | Screen classes (Menu, Game, Shop, Summary, Setup) |
| `restaurant_simulator/ui/input_handler.py` | Keyboard event routing |
| `restaurant_simulator/audio/__init__.py` | Package init |
| `restaurant_simulator/audio/music.py` | Playback controller (play/pause/mute/volume) |
| `restaurant_simulator/audio/tunes.py` | Melody definitions (note sequences) |
| `restaurant_simulator/main.py` | pygame init + game loop + state machine |

---

### Task 1: Package Skeleton + config.py

**Files:**
- Create: `restaurant_simulator/__init__.py`
- Create: `restaurant_simulator/__main__.py`
- Create: `restaurant_simulator/config.py`

- [ ] **Step 1: Create package init and entry point**

```python
# restaurant_simulator/__init__.py
"""Restaurant Simulator v4 — pygame-based restaurant management game."""
```

```python
# restaurant_simulator/__main__.py
"""Entry point: python -m restaurant_simulator"""
from .main import main

if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Create config.py with all game constants**

```python
# restaurant_simulator/config.py
"""
Game balance constants. Tweak here to rebalance the game.
"""

# Economy
DAILY_SALARY_PER_SKILL = 30
STARTING_BUDGET = 500
REPAIR_COST = 20
REPAIR_AMOUNT = 50

# Win/Lose
BANKRUPTCY_REP = -20
DEBT_LIMIT = -200
DEBT_DAYS_LIMIT = 2

# Time
WORK_START_HOUR = 9
WORK_END_HOUR = 21

# Events
RANDOM_EVENT_CHANCE = 0.08

# Spawning
SPAWN_BASE_RATE = 0.3
SPAWN_REP_FACTOR = 0.01
SPAWN_MULT_MIN = 0.1
SPAWN_VARIANCE_LOW = 0.8
SPAWN_VARIANCE_HIGH = 1.2

# Guests
GUEST_BUDGET_MEAN = 40.0
GUEST_BUDGET_STDDEV = 15.0
GUEST_BUDGET_MIN = 5.0
GUEST_PATIENCE_MIN_MINUTES = 5
GUEST_PATIENCE_MAX_MINUTES = 15
GUEST_BASE_EXPECTATION = 3.0
GUEST_EXPECTATION_REP_FACTOR = 0.05

# Service
QUALITY_STAFF_WEIGHT = 0.7
QUALITY_EQUIP_WEIGHT = 0.3
SERVICE_BASE_STAMINA_DRAIN = 8
SERVICE_STAMINA_PER_EXP_MULT = 2
SUCCESS_INCOME_MULT = 1.2
SUCCESS_REP_BASE = 3
FAILURE_REP_BASE = 10
GUEST_LEFT_REP_BASE = 5

# Stamina
STAMINA_RECOVERY_BASE = 5
STAMINA_RECOVERY_KITCHEN_BONUS = 0.5

# Equipment
EQUIP_DEGRADE_PER_SERVICE = 1

# UI (pygame-specific)
WINDOW_WIDTH = 960
WINDOW_HEIGHT = 640
BG_COLOR = (26, 26, 46)
FPS = 60
DEFAULT_TICK_INTERVAL = 0.5  # seconds between ticks at 1x speed
```

- [ ] **Step 3: Verify import works**

```bash
cd /Users/dakh/Git/LurkersDev && python -c "from restaurant_simulator.config import STARTING_BUDGET; print(f'Starting budget: ${STARTING_BUDGET}')"
```
Expected: `Starting budget: $500`

- [ ] **Step 4: Commit**

```bash
git add restaurant_simulator/__init__.py restaurant_simulator/__main__.py restaurant_simulator/config.py
git commit -m "feat: add package skeleton and config"
```

---

### Task 2: Domain Models

**Files:**
- Create: `restaurant_simulator/models/__init__.py`
- Create: `restaurant_simulator/models/equipment.py`
- Create: `restaurant_simulator/models/staff.py`
- Create: `restaurant_simulator/models/guest.py`
- Create: `restaurant_simulator/models/game_state.py`

- [ ] **Step 1: Create models/__init__.py**

```python
# restaurant_simulator/models/__init__.py
from .equipment import Equipment
from .staff import Staff
from .guest import Guest, GUEST_TYPES
from .game_state import GameState

__all__ = ["Equipment", "Staff", "Guest", "GUEST_TYPES", "GameState"]
```

- [ ] **Step 2: Create equipment.py**

```python
# restaurant_simulator/models/equipment.py
from ..config import REPAIR_AMOUNT


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
        return self.quality * (self.durability / self.max_durability)

    @property
    def durability_pct(self) -> float:
        return min(100.0, (self.durability / self.max_durability) * 100) if self.max_durability > 0 else 100.0

    def degrade(self, amount: int = 1) -> None:
        self.durability = max(0, self.durability - amount)

    def repair(self, amount: int = REPAIR_AMOUNT) -> None:
        self.durability = min(self.max_durability, self.durability + amount)

    def replace(self, new_quality: int, new_price: int, new_max_durability: int) -> None:
        self.quality = new_quality
        self.price = new_price
        self.max_durability = new_max_durability
        self.durability = new_max_durability
```

- [ ] **Step 3: Create staff.py**

```python
# restaurant_simulator/models/staff.py
from ..config import STAMINA_RECOVERY_BASE, STAMINA_RECOVERY_KITCHEN_BONUS, SERVICE_BASE_STAMINA_DRAIN


class Staff:
    def __init__(self, skill: int, daily_salary: int):
        self.skill = skill
        self.daily_salary = daily_salary
        self.max_stamina = 100
        self.stamina = self.max_stamina
        self.busy_timer = 0

    @property
    def is_free(self) -> bool:
        return self.busy_timer == 0 and self.stamina > 0

    def start_service(self, stamina_drain: int = SERVICE_BASE_STAMINA_DRAIN) -> None:
        if not self.is_free:
            raise RuntimeError("Staff is not available")
        self.busy_timer = 1
        self.stamina = max(0, self.stamina - stamina_drain)

    def tick_update(self, kitchen_effective_quality: float = 0.0) -> None:
        if self.busy_timer > 0:
            self.busy_timer -= 1
        elif self.stamina < self.max_stamina:
            recovery = STAMINA_RECOVERY_BASE + int(kitchen_effective_quality * STAMINA_RECOVERY_KITCHEN_BONUS)
            self.stamina = min(self.max_stamina, self.stamina + recovery)
```

- [ ] **Step 4: Create guest.py**

```python
# restaurant_simulator/models/guest.py
GUEST_TYPES = {
    "regular":  {"weight": 70, "budget_mult": 1.0, "exp_mult": 1.0, "rep_mult": 1.0, "icon": "🔵", "label": "Regular"},
    "business": {"weight": 20, "budget_mult": 1.5, "exp_mult": 1.2, "rep_mult": 1.5, "icon": "🟡", "label": "Business"},
    "VIP":      {"weight": 8,  "budget_mult": 2.5, "exp_mult": 1.5, "rep_mult": 2.0, "icon": "🟣", "label": "VIP"},
    "critic":   {"weight": 2,  "budget_mult": 3.0, "exp_mult": 2.0, "rep_mult": 5.0, "icon": "🔴", "label": "CRITIC"},
}


class Guest:
    def __init__(self, guest_type: str, budget: float, patience_ticks: int, expectation: float):
        self.guest_type = guest_type
        self.budget = budget
        self.patience_ticks = patience_ticks
        self.expectation = expectation
        self.wait_timer = 0

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

- [ ] **Step 5: Create game_state.py**

```python
# restaurant_simulator/models/game_state.py
from typing import List, Dict
from .equipment import Equipment
from .staff import Staff
from .guest import Guest
from ..config import STARTING_BUDGET, WORK_START_HOUR


class GameState:
    def __init__(self):
        self.budget = STARTING_BUDGET
        self.reputation = 0.0
        self.kitchen = Equipment("Kitchen", 0, 0)
        self.hall = Equipment("Hall", 0, 0)
        self.staff_list: List[Staff] = []
        self.guest_queue: List[Guest] = []
        self.tick = 0
        self.tick_minutes = 5
        self.total_ticks = 144
        self.start_minute = WORK_START_HOUR * 60
        self.served_total = 0
        self.served_success = 0
        self.served_fail = 0
        self.left_guests = 0
        self.day = 1
        self.day_history: List[Dict] = []
        self.debt_days = 0
        self.rush_hour_active = False
        self.rush_hour_remaining = 0

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
        minutes = self.start_minute + self.tick * self.tick_minutes
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
```

- [ ] **Step 6: Verify models import and work**

```bash
cd /Users/dakh/Git/LurkersDev && python -c "
from restaurant_simulator.models import Equipment, Staff, Guest, GameState
state = GameState()
state.hire_staff(5, 150)
print(f'Staff: {len(state.staff_list)}, Free: {state.staff_list[0].is_free}')
state.kitchen = Equipment('Kitchen', 3, 100, 120)
print(f'Kitchen: Q={state.kitchen.effective_quality}, Dur={state.kitchen.durability_pct:.0f}%')
"
```
Expected: Staff: 1, Free: True + Kitchen: Q=3.0, Dur=100%

- [ ] **Step 7: Commit**

```bash
git add restaurant_simulator/models/
git commit -m "feat: add domain models (Equipment, Staff, Guest, GameState)"
```

---

### Task 3: Engine — Spawning + Events

**Files:**
- Create: `restaurant_simulator/engine/__init__.py`
- Create: `restaurant_simulator/engine/spawning.py`
- Create: `restaurant_simulator/engine/events.py`

- [ ] **Step 1: Create engine/__init__.py**

```python
# restaurant_simulator/engine/__init__.py
from .tick import process_tick, run_ticks
from .spawning import spawn_guest, should_spawn_guest
from .events import RandomEvent, RANDOM_EVENTS, pick_random_event

__all__ = [
    "process_tick", "run_ticks",
    "spawn_guest", "should_spawn_guest",
    "RandomEvent", "RANDOM_EVENTS", "pick_random_event",
]
```

- [ ] **Step 2: Create spawning.py**

```python
# restaurant_simulator/engine/spawning.py
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
```

- [ ] **Step 3: Create events.py**

```python
# restaurant_simulator/engine/events.py
from typing import Callable, List, Optional
import random
from ..models import Guest, GameState
from ..config import REPAIR_AMOUNT


class RandomEvent:
    def __init__(self, event_id: str, weight: int, handler: Callable[[GameState], str]):
        self.id = event_id
        self.weight = weight
        self.handler = handler


def _event_inspector(state: GameState) -> str:
    avg_dur = state.avg_durability_pct
    if avg_dur < 30:
        state.reputation -= 15
        return f"🔍 Health Inspector! Equipment in bad shape ({avg_dur:.0f}%). Rep -15"
    elif avg_dur < 60:
        state.reputation -= 5
        return f"🔍 Health Inspector: Equipment needs attention ({avg_dur:.0f}%). Rep -5"
    else:
        state.reputation += 5
        return f"🔍 Health Inspector: Equipment in great shape! Rep +5"


def _event_rush_hour(state: GameState) -> str:
    state.rush_hour_active = True
    state.rush_hour_remaining = 5
    return "⚡ RUSH HOUR! Spawn rate doubled for 5 ticks!"


def _event_equipment_break(state: GameState) -> str:
    equip = random.choice([state.kitchen, state.hall])
    if equip.quality == 0:
        return "💥 Equipment malfunction, but nothing to break!"
    equip.degrade(20)
    return f"💥 {equip.name} malfunction! Durability -20 (now {equip.durability_pct:.0f}%)"


def _event_investor(state: GameState) -> str:
    amount = 50 + state.reputation * 2
    state.budget += amount
    state.reputation += 0.5
    return f"💰 Investor visit! +${amount:.2f}, Rep +0.5"


def _event_party(state: GameState) -> str:
    from .spawning import spawn_guest
    for _ in range(3):
        spawn_guest(state)
    return "🎉 Large party! 3 guests arrived!"


def _event_food_critic(state: GameState) -> str:
    state.guest_queue.append(Guest("critic", 0, 0, 0))
    return "📝 Food Critic arrived! High risk, high reward!"


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
```

- [ ] **Step 4: Verify engine imports**

```bash
cd /Users/dakh/Git/LurkersDev && python -c "
from restaurant_simulator.engine import spawn_guest, pick_random_event, should_spawn_guest
from restaurant_simulator.models import GameState
state = GameState()
state.kitchen.quality = 3; state.hall.quality = 3
state.kitchen.durability = 120; state.hall.durability = 120
spawn_guest(state)
print(f'Queue: {len(state.guest_queue)}, Guest: {state.guest_queue[0].guest_type}')
event = pick_random_event()
print(f'Event: {event.id if event else None}')
"
```

- [ ] **Step 5: Commit**

```bash
git add restaurant_simulator/engine/
git commit -m "feat: add engine (spawning, events)"
```

---

### Task 4: Engine — Tick Processing

**Files:**
- Create: `restaurant_simulator/engine/tick.py`

- [ ] **Step 1: Create tick.py**

```python
# restaurant_simulator/engine/tick.py
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

    if RANDOM_EVENT_CHANCE > 0 and __import__("random").random() < RANDOM_EVENT_CHANCE:
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
```

- [ ] **Step 2: Verify tick processing**

```bash
cd /Users/dakh/Git/LurkersDev && python -c "
from restaurant_simulator.engine.tick import process_tick
from restaurant_simulator.models import GameState
state = GameState()
state.kitchen.quality = 3; state.hall.quality = 3
state.kitchen.durability = 120; state.hall.durability = 120
state.hire_staff(5, 150)
for _ in range(5):
    from restaurant_simulator.engine.spawning import spawn_guest
    spawn_guest(state)
events = process_tick(state)
print(f'Events: {[e[\"type\"] for e in events]}')
print(f'Budget: \${state.budget:.2f}, Rep: {state.reputation}')
"
```

- [ ] **Step 3: Commit**

```bash
git add restaurant_simulator/engine/tick.py
git commit -m "feat: add tick processing engine"
```

---

### Task 5: UI — Renderer

**Files:**
- Create: `restaurant_simulator/ui/__init__.py`
- Create: `restaurant_simulator/ui/renderer.py`

- [ ] **Step 1: Create ui/__init__.py**

```python
# restaurant_simulator/ui/__init__.py
from .renderer import Renderer
from .screens import MainMenu, DaySetupScreen, GameScreen, DaySummaryScreen, ShopScreen, HireScreen
from .input_handler import InputHandler

__all__ = [
    "Renderer", "InputHandler",
    "MainMenu", "DaySetupScreen", "GameScreen", "DaySummaryScreen", "ShopScreen", "HireScreen",
]
```

- [ ] **Step 2: Create renderer.py**

```python
# restaurant_simulator/ui/renderer.py
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
        self.colors = {
            "green": (50, 205, 50),
            "red": (255, 69, 69),
            "yellow": (255, 215, 0),
            "cyan": (0, 255, 255),
            "magenta": (255, 105, 180),
            "white": (255, 255, 255),
            "dim": (150, 150, 150),
            "bar_bg": (60, 60, 60),
        }

    def clear(self) -> None:
        self.surface.fill(BG_COLOR)

    def draw_text(self, text: str, x: int, y: int, color: str = "white", font: str = "normal") -> None:
        f = self.font_bold if font == "bold" else self.font_large if font == "large" else self.font_small if font == "small" else self.font
        surf = f.render(str(text), True, self.colors.get(color, self.colors["white"]))
        self.surface.blit(surf, (x, y))

    def draw_text_centered(self, text: str, y: int, color: str = "white", font: str = "normal") -> int:
        f = self.font_bold if font == "bold" else self.font_large if font == "large" else self.font_small if font == "small" else self.font
        surf = f.render(str(text), True, self.colors.get(color, self.colors["white"]))
        x = (self.width - surf.get_width()) // 2
        self.surface.blit(surf, (x, y))
        return surf.get_width()

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
```

- [ ] **Step 3: Commit**

```bash
git add restaurant_simulator/ui/__init__.py restaurant_simulator/ui/renderer.py
git commit -m "feat: add UI renderer"
```

---

### Task 6: UI — Input Handler

**Files:**
- Create: `restaurant_simulator/ui/input_handler.py`

- [ ] **Step 1: Create input_handler.py**

```python
# restaurant_simulator/ui/input_handler.py
from typing import Callable, Dict, List, Tuple
import pygame


class InputHandler:
    def __init__(self):
        self.key_handlers: Dict[int, Callable] = {}
        self.text_input_active = False
        self.text_input = ""

    def register_key(self, key: int, handler: Callable) -> None:
        self.key_handlers[key] = handler

    def unregister_key(self, key: int) -> None:
        self.key_handlers.pop(key, None)

    def clear(self) -> None:
        self.key_handlers.clear()

    def handle_events(self, events: List[pygame.event.Event]) -> None:
        for event in events:
            if event.type == pygame.QUIT:
                raise SystemExit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    raise SystemExit()
                if event.key in self.key_handlers:
                    self.key_handlers[event.key]()
            if self.text_input_active and event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    self.text_input_active = False
                elif event.key == pygame.K_BACKSPACE:
                    self.text_input = self.text_input[:-1]
                elif event.unicode.isprintable():
                    self.text_input += event.unicode
```

- [ ] **Step 2: Commit**

```bash
git add restaurant_simulator/ui/input_handler.py
git commit -m "feat: add input handler"
```

---

### Task 7: UI — Screens (Part 1: MainMenu + DaySetup)

**Files:**
- Modify: `restaurant_simulator/ui/screens.py` (create)

- [ ] **Step 1: Create screens.py with MainMenu and DaySetupScreen**

```python
# restaurant_simulator/ui/screens.py
import pygame
from typing import List
from ..models import GameState, Equipment
from ..config import (
    WINDOW_WIDTH, WINDOW_HEIGHT, WORK_START_HOUR, WORK_END_HOUR,
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
        self.renderer.draw_text_centered("🌟 Restaurant Simulator v4 🌟", 200, "cyan", "large")
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
        self.options = [1, 5, 10, 15, 30]
        self.input.register_key(pygame.K_UP, self._prev)
        self.input.register_key(pygame.K_DOWN, self._next)
        self.input.register_key(pygame.K_RETURN, self._confirm)

    def _prev(self) -> None:
        idx = self.options.index(self.selection)
        self.selection = self.options[max(0, idx - 1)]

    def _next(self) -> None:
        idx = self.options.index(self.selection)
        self.selection = self.options[min(len(self.options) - 1, idx + 1)]

    def _confirm(self) -> None:
        self.state.tick_minutes = self.selection
        self.state.total_ticks = (WORK_END_HOUR - WORK_START_HOUR) * 60 // self.selection
        self.result = self.selection
        self.exit()

    def render(self) -> None:
        self.renderer.clear()
        self.renderer.draw_text_centered("⏱️ Select Tick Duration", 100, "cyan", "large")
        for i, opt in enumerate(self.options):
            color = "green" if opt == self.selection else "white"
            label = f"{'> ' if opt == self.selection else '  '}{opt} min/tick  ({(WORK_END_HOUR - WORK_START_HOUR) * 60 // opt} ticks/day)"
            self.renderer.draw_text_centered(label, 200 + i * 40, color)
        self.renderer.draw_text_centered("UP/DOWN to select, ENTER to confirm", 450, "dim", "small")
        if not self.is_first_day:
            self.renderer.draw_text_centered(f"Carrying over: Budget=${self.state.budget:.2f} Rep={self.state.reputation:.0f}", 500, "yellow", "small")
```

- [ ] **Step 2: Commit**

```bash
git add restaurant_simulator/ui/screens.py
git commit -m "feat: add MainMenu and DaySetup screens"
```

---

### Task 8: UI — Screens (Part 2: GameScreen)

**Files:**
- Modify: `restaurant_simulator/ui/screens.py` (append)

- [ ] **Step 1: Append GameScreen to screens.py**

```python
# Append to restaurant_simulator/ui/screens.py


class GameScreen(Screen):
    def __init__(self, renderer: Renderer, input_handler: InputHandler, state: GameState):
        super().__init__(renderer, input_handler)
        self.state = state
        self.event_log: List[str] = []
        self.paused = False
        self.game_speed = 1.0
        self.music_muted = False
        self.input.register_key(pygame.K_SPACE, self._toggle_pause)
        self.input.register_key(pygame.K_EQUALS, self._speed_up)
        self.input.register_key(pygame.K_MINUS, self._slow_down)
        self.input.register_key(pygame.K_m, self._toggle_music)
        self.input.register_key(pygame.K_s, self._open_shop)
        self.input.register_key(pygame.K_h, self._open_hire)
        self.input.register_key(pygame.K_q, self._quit_day)
        self.pending_action = None

    def _toggle_pause(self) -> None:
        self.paused = not self.paused

    def _speed_up(self) -> None:
        self.game_speed = min(4.0, self.game_speed * 1.5)

    def _slow_down(self) -> None:
        self.game_speed = max(0.25, self.game_speed / 1.5)

    def _toggle_music(self) -> None:
        self.music_muted = not self.music_muted

    def _open_shop(self) -> None:
        self.pending_action = "shop"

    def _open_hire(self) -> None:
        self.pending_action = "hire"

    def _quit_day(self) -> None:
        self.result = "quit_day"
        self.exit()

    def log_event(self, message: str) -> None:
        self.event_log.append(message)
        self.event_log = self.event_log[-15:]

    def handle_events(self, events: List[pygame.event.Event]) -> None:
        super().handle_events(events)

    def update(self, dt: float) -> None:
        pass

    def render(self) -> None:
        self.renderer.clear()
        s = self.state

        # Top bar
        self.renderer.draw_rect(0, 0, WINDOW_WIDTH, 30, "bar_bg")
        speed_label = f"PAUSED" if self.paused else f"{self.game_speed:.1f}x"
        speed_color = "yellow" if self.paused else "green"
        self.renderer.draw_text(f"  {s.current_time_str()} | Day {s.day} | T {s.tick+1}/{s.total_ticks} | \${s.budget:.2f} | Rep {s.reputation:+.0f} | Queue: {len(s.guest_queue)} | Speed: {speed_label}", 0, 5, speed_color, "bold")

        # Event log
        y = 45
        self.renderer.draw_text("Events:", 10, y, "cyan", "bold")
        y += 20
        for msg in self.event_log[-12:]:
            color = "white"
            if "Success" in msg or "Success" in msg:
                color = "green"
            elif "Failed" in msg or "Failed" in msg or "malfunction" in msg:
                color = "red"
            elif "left" in msg.lower():
                color = "yellow"
            self.renderer.draw_text(f"  {msg}", 10, y, color, "small")
            y += 18

        # Right panel: Equipment
        rx = 600
        self.renderer.draw_text("Equipment:", rx, 45, "cyan", "bold")
        self.renderer.draw_text(f"Kitchen Q={s.kitchen.quality}", rx, 70, "white", "small")
        self.renderer.draw_progress_bar(rx, 85, s.kitchen.durability, s.kitchen.max_durability, 150, 10)
        self.renderer.draw_text(f"Hall    Q={s.hall.quality}", rx, 110, "white", "small")
        self.renderer.draw_progress_bar(rx, 125, s.hall.durability, s.hall.max_durability, 150, 10)

        # Right panel: Staff
        self.renderer.draw_text(f"Staff ({len(s.staff_list)}):", rx, 160, "cyan", "bold")
        for i, staff in enumerate(s.staff_list):
            status = "Free" if staff.is_free else "Busy"
            self.renderer.draw_text(f"#{i+1} Sk={staff.skill} {status}", rx, 180 + i * 35, "white", "small")
            self.renderer.draw_progress_bar(rx, 195 + i * 35, staff.stamina, staff.max_stamina, 150, 8)

        # Guest queue
        self.renderer.draw_text(f"Queue ({len(s.guest_queue)}):", 10, WINDOW_HEIGHT - 100, "cyan", "bold")
        for i, guest in enumerate(s.guest_queue[:5]):
            self.renderer.draw_text(f"  {guest.icon} {guest.label} Budget=\${guest.budget:.0f} Exp={guest.expectation:.1f}", 10, WINDOW_HEIGHT - 80 + i * 18, "white", "small")
        if len(s.guest_queue) > 5:
            self.renderer.draw_text(f"  ... +{len(s.guest_queue) - 5} more", 10, WINDOW_HEIGHT - 80 + 5 * 18, "dim", "small")

        # Controls hint
        self.renderer.draw_text("Space:Pause  +/-:Speed  M:Music  S:Shop  H:Hire  Q:End Day  ESC:Quit", 10, WINDOW_HEIGHT - 18, "dim", "small")
```

- [ ] **Step 2: Commit**

```bash
git add restaurant_simulator/ui/screens.py
git commit -m "feat: add GameScreen"
```

---

### Task 9: UI — Screens (Part 3: Shop + Hire + DaySummary)

**Files:**
- Modify: `restaurant_simulator/ui/screens.py` (append)

- [ ] **Step 1: Append remaining screens to screens.py**

```python
# Append to restaurant_simulator/ui/screens.py


EQUIPMENT_TIERS = {
    0: ("🟢 Basic", 50, 1, 80),
    1: ("🟡 Standard", 100, 3, 120),
    2: ("🔴 Premium", 180, 5, 150),
}


class ShopScreen(Screen):
    def __init__(self, renderer: Renderer, input_handler: InputHandler, state: GameState):
        super().__init__(renderer, input_handler)
        self.state = state
        self.cursor = 0
        self.tier_keys = list(EQUIPMENT_TIERS.keys())
        self.input.register_key(pygame.K_UP, self._prev)
        self.input.register_key(pygame.K_DOWN, self._next)
        self.input.register_key(pygame.K_RETURN, self._buy)
        self.input.register_key(pygame.K_ESCAPE, self._cancel)
        self.input.register_key(pygame.K_r, self._repair)
        self.mode = "upgrade"
        self.slot = "kitchen"

    def _prev(self) -> None:
        self.cursor = max(0, self.cursor - 1)

    def _next(self) -> None:
        self.cursor = min(len(self.tier_keys) - 1, self.cursor + 1)

    def _buy(self) -> None:
        name, price, quality, max_dur = EQUIPMENT_TIERS[self.cursor]
        if self.state.budget >= price:
            self.state.budget -= price
            equip = self.state.kitchen if self.slot == "kitchen" else self.state.hall
            equip.replace(quality, price, max_dur)
            self.result = "bought"
            self.exit()

    def _repair(self) -> None:
        from ..config import REPAIR_COST
        equip = self.state.kitchen if self.slot == "kitchen" else self.state.hall
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
        self.renderer.draw_text_centered("🛒 Equipment Shop", 100, "cyan", "large")
        self.renderer.draw_text_centered(f"Budget: \${self.state.budget:.2f}", 140, "green", "bold")
        self.renderer.draw_text_centered("K: Switch Kitchen  L: Switch Hall  R: Repair  ESC: Close", 180, "dim", "small")
        self.renderer.draw_text_centered(f"Current: {self.slot.title()} Q={getattr(self.state, self.slot).quality} Dur={getattr(self.state, self.slot).durability_pct:.0f}%", 210, "white", "small")
        for i, (name, price, quality, max_dur) in EQUIPMENT_TIERS.items():
            color = "green" if i == self.cursor else "white"
            prefix = "> " if i == self.cursor else "  "
            self.renderer.draw_text_centered(f"{prefix}{name}: \${price} | Q={quality} | MaxDur={max_dur}", 260 + i * 40, color)
        self.renderer.draw_text_centered("UP/DOWN to select, ENTER to buy, R to repair", 420, "dim", "small")


class HireScreen(Screen):
    def __init__(self, renderer: Renderer, input_handler: InputHandler, state: GameState):
        super().__init__(renderer, input_handler)
        self.state = state
        import random
        self.candidate_skill = random.randint(1, 10)
        self.candidate_salary = self.candidate_skill * 30
        self.input.register_key(pygame.K_y, self._hire)
        self.input.register_key(pygame.K_n, self._skip)
        self.input.register_key(pygame.K_ESCAPE, self._cancel)
        self.input.register_key(pygame.K_r, self._reroll)

    def _hire(self) -> None:
        if self.state.budget >= self.candidate_salary:
            self.state.hire_staff(self.candidate_skill, self.candidate_salary)
            self.result = "hired"
            self.exit()

    def _skip(self) -> None:
        self._reroll()

    def _reroll(self) -> None:
        import random
        self.candidate_skill = random.randint(1, 10)
        self.candidate_salary = self.candidate_skill * 30

    def _cancel(self) -> None:
        self.result = "cancelled"
        self.exit()

    def render(self) -> None:
        self.renderer.clear()
        self.renderer.draw_dimmed_overlay()
        self.renderer.draw_text_centered("👥 Hire Staff", 150, "cyan", "large")
        recovery = 5 + int(self.state.kitchen.effective_quality * 0.5)
        per_tick = self.candidate_salary / self.state.total_ticks if self.state.total_ticks > 0 else 0
        self.renderer.draw_text_centered(f"Skill: {self.candidate_skill}", 220, "white", "large")
        self.renderer.draw_text_centered(f"Salary: \${self.candidate_salary}/day (\${per_tick:.2f}/tick)", 260, "yellow", "bold")
        self.renderer.draw_text_centered(f"Stamina recovery: +{recovery}/tick when idle", 300, "white", "small")
        self.renderer.draw_text_centered("Y: Hire  N/R: New Candidate  ESC: Close", 380, "dim", "small")


class DaySummaryScreen(Screen):
    def __init__(self, renderer: Renderer, input_handler: InputHandler, state: GameState):
        super().__init__(renderer, input_handler)
        self.state = state
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
        self.renderer.draw_text_centered(f"📊 Day {s.day} Summary", 50, "cyan", "large")
        start = s.day_history[-1]["end_budget"] if s.day_history else 500
        profit = s.budget - start
        self.renderer.draw_text_centered(f"Budget: \${start:.2f} → \${s.budget:.2f}", 100, "green" if profit >= 0 else "red", "bold")
        self.renderer.draw_text_centered(f"Profit: {'+' if profit >= 0 else ''}\${profit:.2f}", 130, "green" if profit >= 0 else "red")
        self.renderer.draw_text_centered(f"Reputation: {s.reputation:+.0f}", 160, "yellow")
        success_rate = (s.served_success / s.served_total * 100) if s.served_total > 0 else 0
        self.renderer.draw_text_centered(f"Served: {s.served_total} (Success: {s.served_success}, Failed: {s.served_fail}, Left: {s.left_guests})", 200, "white", "small")
        self.renderer.draw_text_centered(f"Success rate: {success_rate:.0f}%", 220, "white", "small")
        self.renderer.draw_text_centered(f"Staff: {len(s.staff_list)} | Kitchen Q={s.kitchen.quality} ({s.kitchen.durability_pct:.0f}%) | Hall Q={s.hall.quality} ({s.hall.durability_pct:.0f}%)", 260, "dim", "small")
        if s.reputation < -20:
            self.renderer.draw_text_centered("💥 BANKRUPT!", 310, "red", "large")
        self.renderer.draw_text_centered("ENTER: Next Day  ESC: Quit", 380, "dim", "small")
```

- [ ] **Step 2: Commit**

```bash
git add restaurant_simulator/ui/screens.py
git commit -m "feat: add Shop, Hire, and DaySummary screens"
```

---

### Task 10: Audio — Chiptune Music

**Files:**
- Create: `restaurant_simulator/audio/__init__.py`
- Create: `restaurant_simulator/audio/tunes.py`
- Create: `restaurant_simulator/audio/music.py`

- [ ] **Step 1: Create audio/__init__.py**

```python
# restaurant_simulator/audio/__init__.py
from .music import MusicPlayer
from .tunes import TUNES

__all__ = ["MusicPlayer", "TUNES"]
```

- [ ] **Step 2: Create tunes.py**

```python
# restaurant_simulator/audio/tunes.py
"""
Procedural chiptune melody definitions.
Each tune is a dict with:
  - notes: list of (frequency_hz, duration_beats) tuples. None = rest.
  - bpm: beats per minute
  - waveform: "square" or "triangle"
  - loop: bool (whether to repeat)
"""

# Simple melodies using basic frequencies
C4, D4, E4, F4, G4, A4, B4 = 261.63, 293.66, 329.63, 349.23, 392.00, 440.00, 493.88
C5 = C4 * 2

TUNES = {
    "day_theme": {
        "notes": [
            (C4, 1), (E4, 1), (G4, 1), (C5, 2),
            (B4, 1), (G4, 1), (E4, 1), (C4, 2),
            (A4, 1), (F4, 1), (D4, 1), (F4, 2),
            (E4, 1), (G4, 1), (C4, 2), (None, 2),
        ],
        "bpm": 120,
        "waveform": "square",
        "loop": True,
    },
    "rush_hour": {
        "notes": [
            (G4, 0.5), (G4, 0.5), (G4, 0.5), (G4, 0.5),
            (E4, 1), (F4, 1), (G4, 2),
            (A4, 0.5), (G4, 0.5), (E4, 0.5), (D4, 0.5),
            (C4, 1), (D4, 1), (E4, 2),
            (G4, 1), (G4, 1), (E4, 1), (C4, 2),
        ],
        "bpm": 160,
        "waveform": "square",
        "loop": True,
    },
    "quiet_hour": {
        "notes": [
            (E4, 2), (D4, 2), (C4, 2), (D4, 2),
            (E4, 2), (E4, 2), (E4, 4),
            (D4, 2), (D4, 2), (D4, 4),
            (E4, 2), (G4, 2), (G4, 4),
        ],
        "bpm": 80,
        "waveform": "triangle",
        "loop": True,
    },
}
```

- [ ] **Step 3: Create music.py**

```python
# restaurant_simulator/audio/music.py
import numpy as np
import pygame
from .tunes import TUNES


class MusicPlayer:
    def __init__(self, sample_rate: int = 44100):
        self.sample_rate = sample_rate
        self.current_tune = None
        self.playing = False
        self.muted = False
        self.volume = 0.3
        self._channel = None

    def _generate_tone(self, freq: float, duration: float, waveform: str = "square") -> np.ndarray:
        """Generate audio samples for a single note."""
        t = np.linspace(0, duration, int(self.sample_rate * duration), False)
        if waveform == "triangle":
            samples = 2 * np.abs(2 * (t * freq - np.floor(0.5 + t * freq))) - 1
        else:  # square
            samples = np.sign(np.sin(2 * np.pi * freq * t))
        # Fade out to avoid clicks
        fade_len = int(self.sample_rate * 0.02)
        if len(samples) > fade_len * 2:
            fade = np.linspace(0, 1, fade_len)
            samples[:fade_len] *= fade
            samples[-fade_len:] *= fade[::-1]
        return samples

    def play_tune(self, tune_name: str) -> None:
        """Start playing a tune. Stops current if playing."""
        if tune_name not in TUNES:
            return
        tune = TUNES[tune_name]
        if self.current_tune == tune_name and self.playing:
            return
        self.current_tune = tune_name

        beat_duration = 60.0 / tune["bpm"]
        all_samples = []
        for freq, beats in tune["notes"]:
            duration = beats * beat_duration
            if freq is not None:
                samples = self._generate_tone(freq, duration, tune["waveform"])
            else:
                samples = np.zeros(int(self.sample_rate * duration))
            all_samples.append(samples)

        audio = np.concatenate(all_samples)
        audio = (audio * 32767 * self.volume).astype(np.int16)
        # Stereo
        stereo = np.column_stack((audio, audio))

        sound = pygame.mixer.Sound(buffer=stereo.tobytes())
        sound.set_volume(self.volume)
        if self._channel:
            self._channel.stop()
        self._channel = sound.play(-1 if tune["loop"] else 0)
        self.playing = True
        self.muted = False

    def set_muted(self, muted: bool) -> None:
        self.muted = muted
        if self._channel:
            self._channel.set_volume(0 if muted else self.volume)

    def set_volume(self, volume: float) -> None:
        self.volume = max(0, min(1, volume))
        if self._channel and not self.muted:
            self._channel.set_volume(self.volume)

    def stop(self) -> None:
        if self._channel:
            self._channel.stop()
            self._channel = None
        self.playing = False

    def get_current_tune(self) -> str:
        """Return the tune name based on game time of day."""
        return "rush_hour"  # Default; caller decides based on state
```

- [ ] **Step 4: Commit**

```bash
git add restaurant_simulator/audio/
git commit -m "feat: add chiptune music system"
```

---

### Task 11: Main — Game Loop + State Machine

**Files:**
- Create: `restaurant_simulator/main.py`

- [ ] **Step 1: Create main.py**

```python
# restaurant_simulator/main.py
"""Main entry point: pygame init, game loop, state machine."""
import pygame
import random
from .config import WINDOW_WIDTH, WINDOW_HEIGHT, FPS, DEFAULT_TICK_INTERVAL
from .models import GameState, Equipment
from .ui import Renderer, InputHandler, MainMenu, DaySetupScreen, GameScreen, DaySummaryScreen, ShopScreen, HireScreen
from .audio import MusicPlayer


def _restore_from_history(state: GameState, prev: dict) -> None:
    state.budget = prev["end_budget"]
    state.reputation = max(0, prev["end_reputation"] * 0.8)
    state.kitchen = prev["kitchen"]
    state.hall = prev["hall"]
    state.staff_list = prev["staff_list"]
    for s in state.staff_list:
        s.stamina = s.max_stamina
        s.busy_timer = 0
    state.day_history = prev["day_history"]


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
        "day_history": [],
    })


def main() -> None:
    pygame.init()
    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
    screen_surface = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Restaurant Simulator v4")
    clock = pygame.time.Clock()

    renderer = Renderer(screen_surface)
    music = MusicPlayer()

    state = GameState()
    is_first_day = True

    # State machine
    current_screen = MainMenu(renderer, InputHandler())

    elapsed = 0.0
    tick_interval = DEFAULT_TICK_INTERVAL
    running = True

    while running:
        dt = clock.tick(FPS) / 1000.0

        try:
            events = pygame.event.get()
            current_screen.handle_events(events)
        except SystemExit:
            running = False
            break

        current_screen.update(dt)
        current_screen.render()
        pygame.display.flip()

        if not current_screen.running:
            result = current_screen.result

            if isinstance(current_screen, MainMenu):
                if result == "start":
                    state = GameState()
                    is_first_day = True
                    current_screen = DaySetupScreen(renderer, InputHandler(), state, is_first_day)

            elif isinstance(current_screen, DaySetupScreen):
                tick_interval = DEFAULT_TICK_INTERVAL / current_screen.selection * 5
                if not is_first_day:
                    current_screen = _between_day_screen(renderer, state)
                    continue
                # Equipment purchase for first day
                from .ui.screens import ShopScreen
                current_screen = ShopScreen(renderer, InputHandler(), state)

            elif isinstance(current_screen, ShopScreen):
                if result == "cancelled" and is_first_day:
                    current_screen = MainMenu(renderer, InputHandler())
                    continue
                # Check if staff needed
                if not state.staff_list:
                    from .ui.screens import HireScreen
                    current_screen = HireScreen(renderer, InputHandler(), state)
                else:
                    _start_playing(renderer, state, music, current_screen)

            elif isinstance(current_screen, HireScreen):
                if result == "cancelled":
                    if not state.staff_list:
                        current_screen = MainMenu(renderer, InputHandler())
                        continue
                if state.staff_list:
                    _start_playing(renderer, state, music, current_screen)

            elif isinstance(current_screen, GameScreen):
                music.stop()
                if result == "quit_day" or state.tick >= state.total_ticks:
                    state.day_history[-1]["end_budget"] = state.budget
                    state.day_history[-1]["end_reputation"] = state.reputation
                current_screen = DaySummaryScreen(renderer, InputHandler(), state)

            elif isinstance(current_screen, DaySummaryScreen):
                if result == "next_day" and state.reputation >= -20:
                    state.day += 1
                    is_first_day = False
                    current_screen = DaySetupScreen(renderer, InputHandler(), state, is_first_day)
                else:
                    running = False

            elif hasattr(current_screen, 'pending_action') and current_screen.pending_action:
                action = current_screen.pending_action
                current_screen.pending_action = None
                if action == "shop":
                    current_screen = ShopScreen(renderer, InputHandler(), state)
                elif action == "hire":
                    current_screen = HireScreen(renderer, InputHandler(), state)

    music.stop()
    pygame.quit()


def _between_day_screen(renderer, state):
    """Simplified flow: go straight to setup, player can press S/H for shop/hire during game."""
    return DaySetupScreen(renderer, InputHandler(), state, is_first_day=False)


def _start_playing(renderer, state, music, prev_screen):
    from .ui.screens import GameScreen
    _record_snapshot(state)
    game_screen = GameScreen(renderer, InputHandler(), state)
    prev_screen = game_screen
    # We need to replace current_screen - handled by caller
    raise _ScreenSwitch(GameScreen(renderer, InputHandler(), state))


class _ScreenSwitch(Exception):
    def __init__(self, screen):
        self.screen = screen
```

Wait, this approach is messy. Let me restructure the main loop properly:

```python
# restaurant_simulator/main.py
"""Main entry point: pygame init, game loop, state machine."""
import pygame
import random
from .config import WINDOW_WIDTH, WINDOW_HEIGHT, FPS, DEFAULT_TICK_INTERVAL
from .models import GameState, Equipment
from .ui import Renderer, InputHandler, MainMenu, DaySetupScreen, GameScreen, DaySummaryScreen, ShopScreen, HireScreen
from .audio import MusicPlayer
from .engine.tick import process_tick


class _ScreenSwitch(Exception):
    def __init__(self, screen):
        self.screen = screen


def main() -> None:
    pygame.init()
    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
    screen_surface = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Restaurant Simulator v4")
    clock = pygame.time.Clock()

    renderer = Renderer(screen_surface)
    music = MusicPlayer()
    state = GameState()
    is_first_day = True
    phase = "menu"

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
            try:
                current_screen = _transition(phase, current_screen, renderer, state, music, is_first_day)
            except _ScreenSwitch as sw:
                current_screen = sw.screen
                continue

            if current_screen is None:
                break

            if isinstance(current_screen, GameScreen):
                phase = "playing"
                elapsed = 0.0
                tick_interval = DEFAULT_TICK_INTERVAL / state.tick_minutes * 5
                music.play_tune("day_theme")
            elif isinstance(current_screen, (MainMenu, DaySummaryScreen)):
                phase = "menu"
            elif isinstance(current_screen, (DaySetupScreen, ShopScreen, HireScreen)):
                phase = "setup"

        # Game tick processing
        if isinstance(current_screen, GameScreen) and not current_screen.paused:
            elapsed += dt * current_screen.game_speed
            if elapsed >= tick_interval:
                evts = process_tick(state)
                for e in evts:
                    if e["type"] == "event":
                        current_screen.log_event(e["message"])
                    elif e["type"] == "success":
                        g = e["guest"]
                        current_screen.log_event(f"{g.icon} Success! {g.label} served +${e['income']:.2f} rep +{e['rep_gain']}")
                    elif e["type"] == "failure":
                        g = e["guest"]
                        current_screen.log_event(f"{g.icon} Failed! {g.label} unhappy -${e['loss']:.2f} rep -{e['rep_loss']}")
                    elif e["type"] == "left":
                        g = e["guest"]
                        current_screen.log_event(f"{g.icon} {g.label} left (waited too long) rep -{e['rep_loss']}")
                    elif e["type"] == "day_end" or e["type"] == "bankruptcy":
                        current_screen.result = "quit_day"
                        current_screen.exit()
                elapsed = 0

            # Handle pending screen switches from GameScreen
            if hasattr(current_screen, 'pending_action') and current_screen.pending_action:
                action = current_screen.pending_action
                current_screen.pending_action = None
                if action == "shop":
                    try:
                        raise _ScreenSwitch(ShopScreen(renderer, InputHandler(), state))
                    except _ScreenSwitch as sw:
                        current_screen = sw.screen
                elif action == "hire":
                    try:
                        raise _ScreenSwitch(HireScreen(renderer, InputHandler(), state))
                    except _ScreenSwitch as sw:
                        current_screen = sw.screen

            # Handle shop/hire return to game
            if isinstance(current_screen, (ShopScreen, HireScreen)):
                if not current_screen.running:
                    current_screen = GameScreen(renderer, InputHandler(), state)

    music.stop()
    pygame.quit()


def _transition(phase, screen, renderer, state, music, is_first_day):
    """Handle screen transitions based on current screen result."""
    if isinstance(screen, MainMenu):
        if screen.result == "start":
            state = GameState()
            is_first_day = True
            return DaySetupScreen(renderer, InputHandler(), state, is_first_day)

    elif isinstance(screen, DaySetupScreen):
        if not is_first_day:
            return DaySetupScreen(renderer, InputHandler(), state, is_first_day)
        return ShopScreen(renderer, InputHandler(), state)

    elif isinstance(screen, ShopScreen):
        if screen.result == "cancelled" and is_first_day:
            return MainMenu(renderer, InputHandler())
        if not state.staff_list:
            return HireScreen(renderer, InputHandler(), state)
        _record_snapshot(state)
        return GameScreen(renderer, InputHandler(), state)

    elif isinstance(screen, HireScreen):
        if screen.result == "cancelled" and not state.staff_list:
            return MainMenu(renderer, InputHandler())
        _record_snapshot(state)
        return GameScreen(renderer, InputHandler(), state)

    elif isinstance(screen, GameScreen):
        state.day_history[-1]["end_budget"] = state.budget
        state.day_history[-1]["end_reputation"] = state.reputation
        music.stop()
        return DaySummaryScreen(renderer, InputHandler(), state)

    elif isinstance(screen, DaySummaryScreen):
        if screen.result == "next_day" and state.reputation >= -20:
            state.day += 1
            is_first_day = False
            return DaySetupScreen(renderer, InputHandler(), state, is_first_day)
        return None

    return None


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
        "day_history": [],
    })
```

- [ ] **Step 2: Commit**

```bash
git add restaurant_simulator/main.py
git commit -m "feat: add main game loop and state machine"
```

---

### Task 12: Integration Test + Run

**Files:**
- No new files

- [ ] **Step 1: Verify full import chain**

```bash
cd /Users/dakh/Git/LurkersDev && python -c "
from restaurant_simulator.main import main
from restaurant_simulator.config import STARTING_BUDGET, WINDOW_WIDTH, WINDOW_HEIGHT
from restaurant_simulator.models import Equipment, Staff, Guest, GameState
from restaurant_simulator.engine import process_tick, spawn_guest
from restaurant_simulator.ui import Renderer, GameScreen
from restaurant_simulator.audio import MusicPlayer, TUNES
print('✅ All imports successful')
print(f'Window: {WINDOW_WIDTH}x{WINDOW_HEIGHT}')
print(f'Budget: \${STARTING_BUDGET}')
print(f'Tunes: {list(TUNES.keys())}')
"
```

- [ ] **Step 2: Run the game (manual test)**

```bash
cd /Users/dakh/Git/LurkersDev && python -m restaurant_simulator
```

Expected: Window opens with main menu, press ENTER to start, gameplay runs continuously with adjustable speed.

- [ ] **Step 3: Commit**

```bash
git add -A
git commit -m "feat: restaurant simulator v4 complete"
```

---

## Self-Review

### Spec Coverage Check
- ✅ File structure — all files mapped
- ✅ Continuous real-time loop — elapsed time × game_speed in main.py
- ✅ Speed control (+/-) — GameScreen._speed_up/_slow_down
- ✅ Pause (Space) — GameScreen._toggle_pause
- ✅ Chiptune music — audio/music.py + audio/tunes.py
- ✅ Domain models unchanged — Equipment, Staff, Guest, GameState
- ✅ Engine split — tick.py, spawning.py, events.py
- ✅ UI screens — MainMenu, DaySetup, Game, Shop, Hire, DaySummary
- ✅ State machine — _transition() in main.py

### Placeholder Scan
- ✅ No TBD/TODO
- ✅ No "add tests for the above"
- ✅ All code shown inline

### Type Consistency
- ✅ process_tick returns List[dict] — used consistently
- ✅ GameState used throughout
- ✅ Screen base class pattern consistent
