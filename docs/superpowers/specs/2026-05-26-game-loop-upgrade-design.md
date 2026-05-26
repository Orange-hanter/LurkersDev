# Restaurant Simulator — Game Loop Upgrade Spec

**Date:** 2026-05-26
**Status:** Approved
**Scope:** Full spec compliance with `gameLoop copy.md`

## Overview

Rewrite the pygame-based restaurant simulator engine to match the complete game loop spec. Legacy terminal versions (game.py, game_v2_FINAL.py, game_v3.py) are removed.

## Architecture

```
restaurant_simulator/
  engine/                          # REWRITTEN
    __init__.py
    phases.py                      # 6 tick phases (pure functions)
    economy.py                     # Pending economy + end-of-day settlement
    spawning.py                    # Enhanced: time-of-day multiplier, priority queue
    events.py                      # Daily events (start-of-day) + tick events
    tables.py                      # Table management (new module)
  models/                          # EXTENDED
    table.py                       # NEW: Table class
    staff.py                       # +status, rest_threshold, fixed recovery rate
    guest.py                       # +priority, mood in quality calc
    equipment.py                   # +step-function quality penalty at <20%
    game_state.py                  # +tables[], pending_income/expense/rep
  ui/                              # ADAPTED
    screens.py                     # DaySetup: table count, GameScreen: tables+queue+phase
    renderer.py                    # New draw primitives for tables/staff
    input_handler.py               # Minimal additions
  main.py                          # Orchestrator: daily event → tick loop → end-of-day
  config.py                        # Extended constants
  audio/                           # Unchanged
```

## Models

### NEW — Table (`models/table.py`)

```python
@dataclass
class Table:
    table_id: int
    capacity: int           # seats (2, 4, or 6)
    state: str              # "free" | "occupied"
    busy_timer: int         # counts down to 0
    guest: Guest | None     # bound when occupied
    staff: Staff | None     # serving staff when occupied
```

### EXTENDED — Staff (`models/staff.py`)

| Field | Old | New |
|---|---|---|
| status | None (`is_free` via timer) | `"ready"` / `"busy"` / `"resting"` |
| rest_threshold | None | `max_stamina * config.REST_THRESHOLD` (30%) |
| recovery_rate | Variable: 5 + kitchen*0.5 | Fixed: `config.REST_RECOVERY_RATE` (2/tick) |
| skill | 1-10 | Unchanged |
| max_stamina | 100 | Unchanged |
| daily_salary | float | Unchanged |
| busy_timer | int | Unchanged |

Logic:
- Status transitions: `ready → busy` (assigned), `busy → ready` (service done)
- If free and `stamina < rest_threshold` → `resting` (Phase 5)
- If resting and `stamina >= rest_threshold` → `ready` (Phase 5)
- While resting: +2 stamina/tick, cannot accept orders

### EXTENDED — Guest (`models/guest.py`)

| Field | Old | New |
|---|---|---|
| priority | None | `int`: 0=normal, 1=VIP |
| mood | Unused field | Used in quality: `(1 + mood * 0.1)` |
| budget | float | Unchanged |
| patience | int (ticks) | Unchanged |
| expectation | float | Unchanged |
| wait_timer | int | Unchanged |

### EXTENDED — Equipment (`models/equipment.py`)

`effective_quality` changes from linear `quality * durability_pct` to step-function:
- `durability >= config.EQUIP_LOW_DURABILITY (20)` → returns `quality` (full)
- `durability < 20` → returns `quality * 0.5`

### EXTENDED — GameState (`models/game_state.py`)

New fields:
- `tables: list[Table]`
- `pending_income: float = 0`
- `pending_expense: float = 0`
- `pending_rep: float = 0`
- `guests_served: int = 0`
- `avg_quality: float = 0`
- `lost_guests: int = 0`
- `daily_event: RandomEvent | None = None`
- `day_ended: bool = False`

Removed fields:
- `debt_days` (bankruptcy now: `budget <= 0 or rep <= -50`)

### EXTENDED — Config (`config.py`)

```python
REST_THRESHOLD = 0.3
REST_RECOVERY_RATE = 2
REP_MIN = -50
REP_MAX = 100
DAILY_EVENT_CHANCE = 0.20
EQUIP_LOW_DURABILITY = 20
MAX_TABLES = 20
TOTAL_TICKS_PER_DAY = 100
SERVICE_DURATION = 5      # ticks for a table to serve a guest

# Time-of-day spawn multipliers
# tick range → multiplier
TIME_OF_DAY_MULTIPLIERS = {
    (0, 20): 0.5,      # early morning
    (20, 40): 1.5,     # rush
    (40, 60): 2.0,     # peak
    (60, 80): 1.5,     # evening
    (80, 100): 0.5,    # late night
}
```

## Engine — 6-Phase Tick Loop (`engine/phases.py`)

Each phase is a pure function: `phase_N(state: GameState) -> list[Event]`.

### Phase 1: Update Timers & Equipment
```
for table in state.tables:
    if table.state == "occupied":
        table.busy_timer -= 1
for staff in state.staff:
    if staff.status == "busy":
        staff.busy_timer -= 1
    if staff.status == "resting":
        staff.stamina += REST_RECOVERY_RATE
        staff.stamina = min(staff.stamina, staff.max_stamina)
for equip in [state.kitchen, state.hall]:
    if equip.durability < EQUIP_LOW_DURABILITY:
        emit warning event
```

### Phase 2: Guest Spawning
```
tick_pct = state.tick / TOTAL_TICKS_PER_DAY
time_mult = lookup_time_of_day_multiplier(tick_pct)
event_mult = state.daily_event.multiplier if state.daily_event else 1.0
spawn_chance = BASE_RATE * (1 + state.reputation * 0.01) * time_mult * event_mult * random(0.8, 1.2)

if random() < spawn_chance:
    guest = Guest(
        budget=NORMAL_DISTRIBUTION(mean, sigma),
        patience=UNIFORM(3, 8),
        expectation=BASE_EXP + state.reputation * 0.05,
        priority=VIP if roll else NORMAL,
    )
    state.guest_queue.append(guest)     # Insert by priority, then FIFO within priority
```

### Phase 3: Resource Assignment
```
while state.guest_queue:
    free_table = find_free_table(state.tables)
    free_staff = find_ready_staff(state.staff_list)   # status == "ready" AND stamina > rest_threshold
    if not (free_table and free_staff):
        break

    guest = state.guest_queue.pop(0)
    free_table.state = "occupied"
    free_table.busy_timer = SERVICE_DURATION
    free_table.guest = guest
    free_table.staff = free_staff
    free_staff.status = "busy"
    free_staff.busy_timer = SERVICE_DURATION

# Age unassigned guests
for guest in state.guest_queue:
    guest.wait_timer += 1
    if guest.wait_timer >= guest.patience:
        state.pending_rep -= 2
        state.lost_guests += 1
        state.guest_queue.remove(guest)
```

### Phase 4: Service Completion
```
for table in state.tables:
    if table.state == "occupied" and table.busy_timer == 0:
        guest = table.guest
        staff = table.staff

        daily_event_bonus = state.daily_event.quality_mult if state.daily_event else 1.0
        quality = (staff.skill * 0.7 + state.avg_equipment_quality * 0.3) * (1 + guest.mood * 0.1) * daily_event_bonus

        if quality >= guest.expectation:
            state.pending_income += guest.budget * 1.2
            state.pending_rep += 3
            state.avg_quality += quality
        else:
            state.pending_expense += guest.budget * 0.3
            state.pending_rep -= 10

        state.guests_served += 1
        release_table(table)    # table.state = "free", table.guest = None, table.staff = None
        release_staff(staff)    # staff.status = "ready"
```

### Phase 5: Staff Rest
```
for staff in state.staff_list:
    if staff.status == "ready" and staff.stamina < staff.rest_threshold:
        staff.status = "resting"
    elif staff.status == "resting" and staff.stamina >= staff.rest_threshold:
        staff.status = "ready"
```

### Phase 6: Tick End
```
state.tick += 1
if state.tick >= TOTAL_TICKS_PER_DAY:
    state.day_ended = True
```

## Engine — Pending Economy (`engine/economy.py`)

Called once at end of day:

```python
def end_of_day(state: GameState):
    # Pay salaries (lump sum, not per-tick)
    total_salary = sum(s.daily_salary for s in state.staff_list)
    state.pending_expense += total_salary

    # Settle pending
    state.budget += state.pending_income
    state.budget -= state.pending_expense
    state.reputation += state.pending_rep

    # Clamp reputation
    state.reputation = max(REP_MIN, min(REP_MAX, state.reputation))

    # Reset pending
    state.pending_income = 0
    state.pending_expense = 0
    state.pending_rep = 0

    # Bankruptcy check
    if state.budget <= 0 or state.reputation <= REP_MIN:
        return "bankruptcy"
    return "next_day"
```

## Engine — Events (`engine/events.py`)

### Daily Events (20% at day start)
| ID | Event | Effect |
|---|---|---|
| health_inspection | Health inspector visits | Equipment quality penalty if durability low |
| vip_guest | VIP guest expected | +50% budget for VIP guests, +expectation |
| equipment_breakdown | Random equipment fails | One equipment takes 30 durability damage |
| good_press | Positive review | x1.5 spawn rate, +5 rep bonus |

### Tick Events (8% per tick)
Kept mostly as-is: inspector, rush_hour, equipment_break, investor, party, food_critic.

## Engine — Tables (`engine/tables.py`)

```python
def create_tables(count: int, capacity: int) -> list[Table]:
    return [Table(table_id=i, capacity=capacity, state="free", busy_timer=0) for i in range(count)]

def find_free_table(tables: list[Table]) -> Table | None:
    for t in tables:
        if t.state == "free":
            return t
    return None

def allocate_table(table: Table, guest: Guest, duration: int):
    table.state = "occupied"
    table.guest = guest
    table.busy_timer = duration

def release_table(table: Table):
    table.state = "free"
    table.guest = None
    table.busy_timer = 0

def find_ready_staff(staff_list: list[Staff]) -> Staff | None:
    for s in staff_list:
        if s.status == "ready" and s.stamina > s.rest_threshold:
            return s
    return None
```

## UI Changes

### DaySetupScreen
- Add table count selector (1-20, up/down arrows or number input)
- Add seating type: small (2 seats), medium (4), large (6)

### ShopScreen
- Add note: "Quality halves when durability drops below 20" per tier

### GameScreen (major changes)
- **Top bar**: day, time (HH:MM), budget, reputation
- **Left panel**: staff list — name, status (Ready=green, Busy=yellow, Resting=blue), stamina bar
- **Center**: table grid — free vs occupied with guest icon, busy timer ring
- **Right panel**: guest queue — priority (VIP star), wait timers, patience bars
- **Bottom**: event log (last 5-8 messages), phase indicator

### DaySummaryScreen
- Guests served, lost guests, avg quality
- Income: service income, expenses (refunds + salaries), net profit
- Reputation: before → after (with clamp)
- Equipment status, durability warnings
- "Next Day" or "Bankruptcy — Game Over" button

### Renderer
- `draw_table_sprite(surface, x, y, state, busy_pct)` — table icon
- `draw_staff_card(surface, x, y, staff)` — compact status card
- `draw_phase_indicator(surface, phase)` — corner text

## Main Loop (`main.py`)

```
SCREEN FLOW:
MainMenu → DaySetup → Shop → Hire → GameScreen → DaySummary → (loop back)

INSIDE GameScreen (per tick):
    phase_1(state)     → events
    phase_2(state)     → events
    phase_3(state)     → events
    phase_4(state)     → events
    phase_5(state)     → events
    phase_6(state)     → events

    if state.day_ended:
        result = end_of_day(state)   # "next_day" or "bankruptcy"

Speed controls: 1x, 2x, 4x toggle. Space to pause.
```

## Files to Create
- `restaurant_simulator/models/table.py`
- `restaurant_simulator/engine/phases.py`
- `restaurant_simulator/engine/economy.py`
- `restaurant_simulator/engine/tables.py`

## Files to Rewrite
- `restaurant_simulator/engine/__init__.py`
- `restaurant_simulator/engine/events.py`
- `restaurant_simulator/engine/spawning.py`
- `restaurant_simulator/main.py`

## Files to Modify
- `restaurant_simulator/config.py`
- `restaurant_simulator/models/__init__.py`
- `restaurant_simulator/models/game_state.py`
- `restaurant_simulator/models/staff.py`
- `restaurant_simulator/models/guest.py`
- `restaurant_simulator/models/equipment.py`
- `restaurant_simulator/ui/screens.py`
- `restaurant_simulator/ui/renderer.py`
- `restaurant_simulator/ui/__init__.py`

## Files to Delete
- `game.py`
- `game_v2_FINAL.py`
- `game_v3.py`
- `gameLoop copy.md` (consumed into spec)

## Files Unchanged
- `restaurant_simulator/__init__.py`
- `restaurant_simulator/__main__.py`
- `restaurant_simulator/audio/` (all files)
- `restaurant_simulator/ui/input_handler.py`
