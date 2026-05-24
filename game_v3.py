"""
Restaurant Simulator v3 — A text-based restaurant management game.

Architecture Overview
=====================
The codebase is organized into five logical layers within a single file:

  1. CONFIGURATION    — Game constants, balance tuning, ANSI color codes
  2. DOMAIN MODELS    — Equipment, Staff, Guest, GameState (pure data + behaviour)
  3. GAME ENGINE      — Tick processing, spawning, random events (simulation logic)
  4. UI / MENUS       — Terminal rendering, input prompts, status displays
  5. MAIN LOOP        — Day lifecycle, command dispatch, save/load carry-over

Design Principles
=================
• Domain models are side-effect free where possible
• Game engine functions accept GameState and return event strings
• UI functions only handle rendering and input — no game logic
• Constants are centralized for easy rebalancing
"""

import random
import math
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Callable, Tuple


# ==============================================================================
# 1. CONFIGURATION
# ==============================================================================

class Config:
    """Centralized game balance constants. Tweak here to rebalance the game."""

    # --- Economy ---
    # Base daily salary per skill point. A skill-1 worker costs $30/day; skill-10 costs $300/day.
    DAILY_SALARY_PER_SKILL = 30

    # Starting budget for a new restaurant on Day 1.
    STARTING_BUDGET = 500

    # Cost to repair equipment (+50 durability per repair).
    REPAIR_COST = 20
    REPAIR_AMOUNT = 50

    # --- Win/Lose Conditions ---
    # If reputation drops below this threshold, the restaurant goes bankrupt.
    BANKRUPTCY_REP = -20

    # If budget drops below this threshold, the player enters "danger debt".
    # Two consecutive days in debt triggers game over.
    DEBT_LIMIT = -200
    DEBT_DAYS_LIMIT = 2

    # --- Time ---
    # Operating hours (in 24h format). A day runs from START to END.
    WORK_START_HOUR = 9
    WORK_END_HOUR = 21

    # --- Events ---
    # Probability (per tick) that a random event occurs.
    RANDOM_EVENT_CHANCE = 0.08

    # --- Guest Spawning ---
    # Base probability that a guest spawns each tick (before reputation modifier).
    SPAWN_BASE_RATE = 0.3

    # Reputation multiplier factor: each +1 rep increases spawn rate by 1%.
    SPAWN_REP_FACTOR = 0.01

    # Clamp minimum spawn multiplier to prevent total drought at low rep.
    SPAWN_MULT_MIN = 0.1

    # Random variance applied to spawn chance (±20%).
    SPAWN_VARIANCE_LOW = 0.8
    SPAWN_VARIANCE_HIGH = 1.2

    # --- Guest Parameters ---
    # Guest budget follows a normal distribution: N(mean * type_mult, stddev).
    GUEST_BUDGET_MEAN = 40.0
    GUEST_BUDGET_STDDEV = 15.0
    GUEST_BUDGET_MIN = 5.0

    # Patience is uniformly distributed in real minutes, then converted to ticks.
    GUEST_PATIENCE_MIN_MINUTES = 5
    GUEST_PATIENCE_MAX_MINUTES = 15

    # Base expectation for a regular guest at neutral reputation.
    GUEST_BASE_EXPECTATION = 3.0

    # Each +1 reputation increases guest expectation by this amount.
    GUEST_EXPECTATION_REP_FACTOR = 0.05

    # --- Service Calculation ---
    # Quality formula: staff contributes 70%, equipment contributes 30%.
    QUALITY_STAFF_WEIGHT = 0.7
    QUALITY_EQUIP_WEIGHT = 0.3

    # Base stamina drain per service (additional drain scales with guest type).
    SERVICE_BASE_STAMINA_DRAIN = 8
    SERVICE_STAMINA_PER_EXP_MULT = 2

    # Income multiplier on successful service (guest.budget × this factor).
    SUCCESS_INCOME_MULT = 1.2

    # Base reputation changes for success/failure (multiplied by guest type rep_mult).
    SUCCESS_REP_BASE = 3
    FAILURE_REP_BASE = 10
    GUEST_LEFT_REP_BASE = 5

    # --- Stamina Recovery ---
    # Base stamina recovered per tick when staff is idle.
    STAMINA_RECOVERY_BASE = 5

    # Kitchen quality bonus: each point of effective quality adds this to recovery.
    STAMINA_RECOVERY_KITCHEN_BONUS = 0.5

    # --- Equipment ---
    # Durability lost per service rendered.
    EQUIP_DEGRADE_PER_SERVICE = 1


# ==============================================================================
# ANSI Color Helpers
# ==============================================================================

class C:
    """ANSI escape codes for terminal coloring. Usage: f"{C['red']}text{C['reset']}"."""
    reset = "\033[0m"
    bold = "\033[1m"
    red = "\033[91m"
    green = "\033[92m"
    yellow = "\033[93m"
    blue = "\033[94m"
    magenta = "\033[95m"
    cyan = "\033[96m"
    white = "\033[97m"
    dim = "\033[2m"
    bg_dark = "\033[48;5;235m"


def cp(text: str, color: str) -> str:
    """Wrap text in ANSI color codes."""
    return f"{color}{text}{C.reset}"


def progress_bar(current: float, maximum: float, width: int = 10) -> str:
    """Render a visual progress bar with color-coded fill level."""
    ratio = max(0, min(1, current / maximum)) if maximum > 0 else 0
    filled = int(width * ratio)
    empty = width - filled

    if ratio > 0.6:
        color = C.green
    elif ratio > 0.3:
        color = C.yellow
    else:
        color = C.red

    return f"{color}{'█' * filled}{'░' * empty}{C.reset} {current:.0f}/{maximum:.0f}"


def fmt_money(amount: float) -> str:
    """Format a dollar amount with green/red coloring based on sign."""
    color = C.green if amount >= 0 else C.red
    return f"{color}${amount:.2f}{C.reset}"


def fmt_rep(rep: float) -> str:
    """Format reputation with sign and color based on value."""
    if rep > 10:
        color = C.green
    elif rep > 0:
        color = C.yellow
    else:
        color = C.red
    return f"{color}{rep:+.0f}{C.reset}"


# ==============================================================================
# 2. DOMAIN MODELS
# ==============================================================================

class Equipment:
    """
    Represents a piece of restaurant equipment (kitchen or hall).

    Each equipment has a fixed quality rating (set at purchase/upgrade) and a
    degrading durability bar. The *effective* quality — used in service
    calculations — is quality scaled by the current durability percentage.

    Example: quality=5, durability=60% → effective_quality = 3.0
    """

    def __init__(self, name: str, quality: int, price: int, max_durability: int = 100):
        self.name = name
        self.quality = quality
        self.price = price
        self.max_durability = max_durability
        self.durability = max_durability

    # -- Computed properties --

    @property
    def effective_quality(self) -> float:
        """Quality adjusted by current wear. Returns 0 if durability is exhausted."""
        if self.durability <= 0:
            return 0.0
        return self.quality * (self.durability / self.max_durability)

    @property
    def durability_pct(self) -> float:
        """Current durability as a percentage of maximum, capped at 100%."""
        return min(100.0, (self.durability / self.max_durability) * 100) if self.max_durability > 0 else 100.0

    # -- Mutators --

    def degrade(self, amount: int = 1) -> None:
        """Reduce durability by the given amount (never below 0)."""
        self.durability = max(0, self.durability - amount)

    def repair(self, amount: int = Config.REPAIR_AMOUNT) -> None:
        """Restore durability by the given amount (never above max)."""
        self.durability = min(self.max_durability, self.durability + amount)

    def replace(self, new_quality: int, new_price: int, new_max_durability: int) -> None:
        """Replace with a new tier: resets durability to fresh max."""
        self.quality = new_quality
        self.price = new_price
        self.max_durability = new_max_durability
        self.durability = new_max_durability


class Staff:
    """
    Represents a restaurant employee.

    Key attributes:
    • skill (1-10): Affects service quality (70% weight).
    • daily_salary: Total pay for a full day, distributed evenly across ticks.
    • stamina: Drains during service, recovers during idle ticks.
                 Recovery is faster with better kitchen equipment.

    Staff are considered "free" when their busy_timer reaches 0 AND stamina > 0.
    """

    def __init__(self, skill: int, daily_salary: int):
        self.skill = skill
        self.daily_salary = daily_salary
        self.max_stamina = 100
        self.stamina = self.max_stamina
        self.busy_timer = 0

    # -- State queries --

    @property
    def is_free(self) -> bool:
        """True if staff can accept a new guest assignment."""
        return self.busy_timer == 0 and self.stamina > 0

    # -- Actions --

    def start_service(self, stamina_drain: int = Config.SERVICE_BASE_STAMINA_DRAIN) -> None:
        """
        Begin serving a guest. Sets busy_timer to 1 (one tick) and drains stamina.

        Raises RuntimeError if staff is not available.
        """
        if not self.is_free:
            raise RuntimeError("Staff is not available")
        self.busy_timer = 1
        self.stamina = max(0, self.stamina - stamina_drain)

    def tick_update(self, kitchen_effective_quality: float = 0.0) -> None:
        """
        Advance staff state by one tick.

        • If busy: decrement busy_timer.
        • If idle and damaged stamina: recover stamina. Recovery rate is
          Config.STAMINA_RECOVERY_BASE + kitchen_quality × 0.5.
        """
        if self.busy_timer > 0:
            self.busy_timer -= 1
        elif self.stamina < self.max_stamina:
            recovery = Config.STAMINA_RECOVERY_BASE + int(
                kitchen_effective_quality * Config.STAMINA_RECOVERY_KITCHEN_BONUS
            )
            self.stamina = min(self.max_stamina, self.stamina + recovery)


class Guest:
    """
    Represents a customer waiting to be served.

    Guest types (Regular, Business, VIP, Critic) determine:
    • budget_mult   — multiplier on the base budget distribution
    • exp_mult      — multiplier on the base expectation threshold
    • rep_mult      — multiplier on reputation gains/losses
    • icon/label    — visual indicator for the terminal UI
    """

    def __init__(self, guest_type: str, budget: float, patience_ticks: int, expectation: float):
        self.guest_type = guest_type
        self.budget = budget
        self.patience_ticks = patience_ticks
        self.expectation = expectation
        self.wait_timer = 0

    @property
    def type_info(self) -> dict:
        """Lookup table entry for this guest's type."""
        return GUEST_TYPES[self.guest_type]

    @property
    def icon(self) -> str:
        """Emoji icon for display."""
        return self.type_info["icon"]

    @property
    def label(self) -> str:
        """Human-readable type label."""
        return self.type_info["label"]

    @property
    def rep_multiplier(self) -> float:
        """How much reputation change this guest type causes."""
        return self.type_info["rep_mult"]

    @property
    def expectation_multiplier(self) -> float:
        """How demanding this guest type is."""
        return self.type_info["exp_mult"]


# --- Guest type definitions ---
# Weights sum to 100 for probability distribution.
GUEST_TYPES: Dict[str, dict] = {
    "regular":  {"weight": 70, "budget_mult": 1.0, "exp_mult": 1.0, "rep_mult": 1.0, "icon": "🔵", "label": "Regular"},
    "business": {"weight": 20, "budget_mult": 1.5, "exp_mult": 1.2, "rep_mult": 1.5, "icon": "🟡", "label": "Business"},
    "VIP":      {"weight": 8,  "budget_mult": 2.5, "exp_mult": 1.5, "rep_mult": 2.0, "icon": "🟣", "label": "VIP"},
    "critic":   {"weight": 2,  "budget_mult": 3.0, "exp_mult": 2.0, "rep_mult": 5.0, "icon": "🔴", "label": "CRITIC"},
}


class GameState:
    """
    Central game state container. Holds all mutable simulation data.

    The tick-based simulation loop works as follows:
    1. Increment tick counter.
    2. Check end-of-day and bankruptcy conditions.
    3. Update all staff (busy timers, stamina recovery).
    4. Roll for random events (8% chance).
    5. Attempt to spawn a new guest (probability scales with reputation).
    6. Assign free staff to waiting guests (FIFO).
    7. Process service outcomes (success/failure → budget + reputation).
    8. Age waiting guests; remove those who exceeded patience.
    9. Deduct staff salaries (daily_salary / total_ticks per tick).

    Multi-day persistence: day_history stores snapshots at day boundaries.
    On a new day, the previous day's end state is restored (with partial
    reputation decay and full stamina recovery).
    """

    def __init__(self):
        # Economy
        self.budget = Config.STARTING_BUDGET
        self.reputation = 0.0

        # Infrastructure
        self.kitchen = Equipment("Kitchen", 0, 0)
        self.hall = Equipment("Hall", 0, 0)

        # Entities
        self.staff_list: List[Staff] = []
        self.guest_queue: List[Guest] = []

        # Time tracking
        self.tick = 0
        self.tick_minutes = 5
        self.total_ticks = 144
        self.start_minute = Config.WORK_START_HOUR * 60

        # Statistics
        self.served_total = 0
        self.served_success = 0
        self.served_fail = 0
        self.left_guests = 0

        # Multi-day persistence
        self.day = 1
        self.day_history: List[Dict] = []
        self.debt_days = 0

        # Active effects
        self.rush_hour_active = False
        self.rush_hour_remaining = 0

    # -- Computed properties --

    @property
    def avg_equipment_quality(self) -> float:
        """Average effective quality of kitchen and hall combined."""
        return (self.kitchen.effective_quality + self.hall.effective_quality) / 2.0

    @property
    def avg_durability_pct(self) -> float:
        """Combined durability percentage across both equipment pieces."""
        total_max = self.kitchen.max_durability + self.hall.max_durability
        if total_max == 0:
            return 100.0
        return ((self.kitchen.durability + self.hall.durability) / total_max) * 100

    # -- Time helpers --

    def current_time_str(self) -> str:
        """Format the current in-game clock as HH:MM."""
        minutes = self.start_minute + self.tick * self.tick_minutes
        h = (minutes // 60) % 24
        m = minutes % 60
        return f"{h:02d}:{m:02d}"

    def time_remaining(self) -> int:
        """Number of ticks left until the work day ends."""
        return max(0, self.total_ticks - self.tick)

    def day_profit(self) -> float:
        """Profit earned during the current day (vs. day start budget)."""
        if not self.day_history:
            return self.budget - Config.STARTING_BUDGET
        return self.budget - self.day_history[-1]["end_budget"]

    # -- Staff management --

    def hire_staff(self, skill: int, daily_salary: int) -> None:
        """Add a new staff member to the roster."""
        self.staff_list.append(Staff(skill, daily_salary))

    def fire_staff(self, index: int) -> None:
        """Remove a staff member by roster index (0-based)."""
        if 0 <= index < len(self.staff_list):
            self.staff_list.pop(index)


# ==============================================================================
# 3. GAME ENGINE — Random Events
# ==============================================================================

class RandomEvent:
    """
    Defines a random event that can occur during a tick.

    Each event has:
    • id: Unique identifier for debugging/logging.
    • weight: Relative probability (higher = more likely when an event triggers).
    • handler: Callable that mutates GameState and returns a description string.
    """

    def __init__(self, event_id: str, weight: int, handler: Callable[[GameState], str]):
        self.id = event_id
        self.weight = weight
        self.handler = handler


def _event_inspector(state: GameState) -> str:
    """Health inspection: rewards good equipment maintenance, penalizes neglect."""
    avg_dur = state.avg_durability_pct
    if avg_dur < 30:
        penalty = 15
        state.reputation -= penalty
        return f"🔍 {cp('Health Inspector!', C.red)} Equipment in bad shape ({avg_dur:.0f}%). {cp(f'Reputation -{penalty}', C.red)}"
    elif avg_dur < 60:
        penalty = 5
        state.reputation -= penalty
        return f"🔍 {cp('Health Inspector', C.yellow)} Equipment needs attention ({avg_dur:.0f}%). {cp(f'Reputation -{penalty}', C.yellow)}"
    else:
        bonus = 5
        state.reputation += bonus
        return f"🔍 {cp('Health Inspector', C.green)} Equipment in great shape! {cp(f'Reputation +{bonus}', C.green)}"


def _event_rush_hour(state: GameState) -> str:
    """Doubles guest spawn rate for the next 5 ticks."""
    state.rush_hour_active = True
    state.rush_hour_remaining = 5
    return f"⚡ {cp('RUSH HOUR!', C.yellow)} Spawn rate doubled for next 5 ticks!"


def _event_equipment_break(state: GameState) -> str:
    """Random equipment loses 20 durability. Skipped if equipment has no quality."""
    equip = random.choice([state.kitchen, state.hall])
    if equip.quality == 0:
        return "💥 Equipment malfunction, but nothing to break!"
    equip.degrade(20)
    return f"💥 {cp('Equipment malfunction!', C.red)} {equip.name} durability -20 (now {equip.durability_pct:.0f}%)"


def _event_investor(state: GameState) -> str:
    """Generous investor gives cash and a small reputation boost."""
    amount = 50 + state.reputation * 2
    state.budget += amount
    state.reputation += 0.5
    return f"💰 {cp('Investor visit!', C.green)} Gained {fmt_money(amount)} and reputation +0.5"


def _event_party(state: GameState) -> str:
    """A large party of 3 guests arrives simultaneously."""
    count = 3
    for _ in range(count):
        _spawn_guest(state)
    return f"🎉 {cp('Large party!', C.magenta)} {count} guests arrived at once!"


def _event_food_critic(state: GameState) -> str:
    """A food critic joins the queue — high budget, very high expectations, massive rep impact."""
    critic = Guest("critic", 0, 0, 0)
    state.guest_queue.append(critic)
    return f"📝 {cp('Food Critic arrived!', C.red)} High risk, high reward! (Added to queue)"


# Registry of all possible random events. Weights are relative probabilities.
RANDOM_EVENTS: List[RandomEvent] = [
    RandomEvent("inspector", 25, _event_inspector),
    RandomEvent("rush_hour", 20, _event_rush_hour),
    RandomEvent("equipment_break", 15, _event_equipment_break),
    RandomEvent("investor", 15, _event_investor),
    RandomEvent("party", 15, _event_party),
    RandomEvent("food_critic", 10, _event_food_critic),
]


def _pick_random_event() -> Optional[RandomEvent]:
    """Select a random event based on weighted probabilities. Returns None if no event."""
    total_weight = sum(e.weight for e in RANDOM_EVENTS)
    roll = random.uniform(0, total_weight)
    cumulative = 0
    for event in RANDOM_EVENTS:
        cumulative += event.weight
        if roll <= cumulative:
            return event
    return None


# ==============================================================================
# 3. GAME ENGINE — Core Simulation
# ==============================================================================

def _pick_guest_type() -> str:
    """
    Select a guest type based on weighted probability distribution.

    Distribution: Regular 70%, Business 20%, VIP 8%, Critic 2%.
    """
    total_weight = sum(info["weight"] for info in GUEST_TYPES.values())
    roll = random.uniform(0, total_weight)
    cumulative = 0
    for gtype, info in GUEST_TYPES.items():
        cumulative += info["weight"]
        if roll <= cumulative:
            return gtype
    return "regular"


def _spawn_guest(state: GameState) -> None:
    """
    Create a new guest with randomized parameters and add them to the queue.

    Parameters are scaled by the guest type:
    • Budget: Normal distribution (mean=GUEST_BUDGET_MEAN × type_mult, stddev=15)
    • Patience: Uniform 5-15 real minutes, converted to ticks
    • Expectation: Base expectation scaled by type multiplier and reputation
    """
    guest_type = _pick_guest_type()
    type_info = GUEST_TYPES[guest_type]

    budget = max(
        Config.GUEST_BUDGET_MIN,
        random.gauss(Config.GUEST_BUDGET_MEAN * type_info["budget_mult"], Config.GUEST_BUDGET_STDDEV),
    )

    base_patience_minutes = random.randint(
        Config.GUEST_PATIENCE_MIN_MINUTES, Config.GUEST_PATIENCE_MAX_MINUTES
    )
    patience_ticks = max(1, base_patience_minutes // state.tick_minutes)

    base_expectation = Config.GUEST_BASE_EXPECTATION * type_info["exp_mult"]
    expectation = base_expectation + state.reputation * Config.GUEST_EXPECTATION_REP_FACTOR

    guest = Guest(guest_type, budget, patience_ticks, expectation)
    state.guest_queue.append(guest)


def _should_spawn_guest(state: GameState) -> bool:
    """
    Determine whether a new guest should spawn this tick.

    Spawn probability = base_rate × reputation_multiplier × random_variance.
    During rush hour, base_rate is doubled.
    """
    base_rate = Config.SPAWN_BASE_RATE

    if state.rush_hour_active:
        base_rate *= 2
        state.rush_hour_remaining -= 1
        if state.rush_hour_remaining <= 0:
            state.rush_hour_active = False

    reputation_mult = 1 + state.reputation * Config.SPAWN_REP_FACTOR
    reputation_mult = max(Config.SPAWN_MULT_MIN, reputation_mult)

    variance = random.uniform(Config.SPAWN_VARIANCE_LOW, Config.SPAWN_VARIANCE_HIGH)
    spawn_chance = base_rate * reputation_mult * variance

    return random.random() < spawn_chance


def process_tick(state: GameState) -> List[str]:
    """
    Execute one full simulation tick and return a list of human-readable event messages.

    Tick order:
    1. Increment tick counter, check day-end and bankruptcy conditions.
    2. Update all staff (busy timers, stamina recovery).
    3. Roll for random events (Config.RANDOM_EVENT_CHANCE probability).
    4. Attempt guest spawning.
    5. Assign free staff to queued guests (FIFO).
    6. Evaluate service outcomes (quality vs expectation).
    7. Age waiting guests; remove those who exceeded patience.
    8. Deduct salaries (pro-rated per tick).
    """
    events: List[str] = []

    # --- Step 1: Tick counter and termination checks ---
    state.tick += 1
    events.append(cp(f"--- Tick {state.tick} ({state.current_time_str()}) ---", C.dim))

    if state.tick > state.total_ticks:
        events.append(cp("🏁 Work day ended!", C.bold + C.cyan))
        return events

    if state.reputation < Config.BANKRUPTCY_REP:
        events.append(cp("💥 Reputation fell below zero! Bankruptcy.", C.bold + C.red))
        return events

    # --- Step 2: Staff updates (stamina recovery, busy timers) ---
    for staff in state.staff_list:
        staff.tick_update(kitchen_effective_quality=state.kitchen.effective_quality)

    # --- Step 3: Random events ---
    if random.random() < Config.RANDOM_EVENT_CHANCE:
        event = _pick_random_event()
        if event:
            result = event.handler(state)
            events.append(f"  {result}")

    # --- Step 4: Guest spawning ---
    if _should_spawn_guest(state):
        _spawn_guest(state)
        events.append(f"  {cp('🎲 New guest arrived!', C.cyan)}")

    # --- Step 5 & 6: Assign staff and process service ---
    free_staff = [s for s in state.staff_list if s.is_free]

    while free_staff and state.guest_queue:
        staff = free_staff.pop(0)
        guest = state.guest_queue.pop(0)

        # Calculate service quality: staff skill (70%) + equipment (30%)
        quality = (
            staff.skill * Config.QUALITY_STAFF_WEIGHT
            + state.avg_equipment_quality * Config.QUALITY_EQUIP_WEIGHT
        )

        # Stamina drain scales with how demanding the guest type is
        stamina_drain = Config.SERVICE_BASE_STAMINA_DRAIN + int(
            guest.expectation_multiplier * Config.SERVICE_STAMINA_PER_EXP_MULT
        )
        staff.start_service(stamina_drain=stamina_drain)

        # Degrade equipment durability with each service
        state.kitchen.degrade(Config.EQUIP_DEGRADE_PER_SERVICE)
        state.hall.degrade(Config.EQUIP_DEGRADE_PER_SERVICE)

        state.served_total += 1
        rep_mult = guest.rep_multiplier

        if quality >= guest.expectation:
            # --- Success: earn income, gain reputation ---
            income = guest.budget * Config.SUCCESS_INCOME_MULT
            state.budget += income
            rep_gain = Config.SUCCESS_REP_BASE * rep_mult
            state.reputation += rep_gain
            state.served_success += 1
            events.append(
                f"  {guest.icon} {cp('Success!', C.green)} {guest.label} served. "
                f"{fmt_money(income)} rep {cp(f'+{rep_gain}', C.green)}"
            )
        else:
            # --- Failure: lose guest budget as penalty, lose reputation ---
            loss = guest.budget
            state.budget -= loss
            rep_loss = Config.FAILURE_REP_BASE * rep_mult
            state.reputation -= rep_loss
            state.served_fail += 1
            events.append(
                f"  {guest.icon} {cp('Failed!', C.red)} {guest.label} unhappy. "
                f"{cp(f'-${loss:.2f}', C.red)} rep {cp(f'-{rep_loss}', C.red)}"
            )

    # --- Step 7: Process waiting guests who exceeded patience ---
    for guest in list(state.guest_queue):
        guest.wait_timer += 1
        if guest.wait_timer >= guest.patience_ticks:
            state.guest_queue.remove(guest)
            rep_loss = Config.GUEST_LEFT_REP_BASE * guest.rep_multiplier
            state.reputation -= rep_loss
            state.left_guests += 1
            events.append(
                f"  {guest.icon} {cp('Guest left!', C.yellow)} {guest.label} waited too long. "
                f"rep {cp(f'-{rep_loss}', C.yellow)}"
            )

    # --- Step 8: Deduct pro-rated staff salaries ---
    total_salary = sum(s.daily_salary / state.total_ticks for s in state.staff_list)
    state.budget -= total_salary
    if state.staff_list:
        events.append(cp(f"  💼 Salaries: -${total_salary:.2f}", C.dim))

    # --- Status summary line ---
    events.append(f"  {fmt_money(state.budget)} | {fmt_rep(state.reputation)} | Queue: {len(state.guest_queue)}")
    return events


def run_ticks(state: GameState, n: int) -> List[str]:
    """
    Fast-forward N ticks without printing intermediate output.
    Returns only the final tick's event list.
    Useful for skipping boring periods or testing.
    """
    final_events: List[str] = []
    for _ in range(n):
        if state.tick >= state.total_ticks or state.reputation < Config.BANKRUPTCY_REP:
            break
        final_events = process_tick(state)
    return final_events


# ==============================================================================
# 4. UI / MENUS
# ==============================================================================

# --- Equipment tiers definition ---
# Format: tier_key -> (display_name, price, quality, max_durability)
EQUIPMENT_TIERS = {
    '1': ('🟢 Basic', 50, 1, 80),
    '2': ('🟡 Standard', 100, 3, 120),
    '3': ('🔴 Premium', 180, 5, 150),
}


def _display_equipment_tiers() -> None:
    """Print available equipment tiers to the terminal."""
    for key, (name, price, quality, max_dur) in EQUIPMENT_TIERS.items():
        print(f"  {key}. {name}: {fmt_money(price)} | Quality: +{quality} | Max Durability: {max_dur}")


def choose_equipment(state: GameState) -> Tuple[Tuple[int, int, int], Tuple[int, int, int]]:
    """
    Initial equipment selection for a new restaurant (Day 1 only).

    Prompts the player to choose a tier for kitchen and hall separately.
    Returns ((kitchen_quality, kitchen_price, kitchen_dur), (hall_quality, hall_price, hall_dur)).
    """
    print(f"\n{cp('🛒 Equipment Shop', C.bold + C.cyan)}")
    print(f"Budget: {fmt_money(state.budget)}")
    _display_equipment_tiers()

    def pick_tier(slot_name: str) -> Tuple[str, int, int, int]:
        """Prompt until the player selects a valid tier."""
        while True:
            choice = input(f"Equipment for {slot_name} (1-3): ").strip()
            if choice in EQUIPMENT_TIERS:
                return (choice,) + EQUIPMENT_TIERS[choice]
            print(cp("Invalid choice.", C.red))

    _, k_price, k_q, k_dur = pick_tier("kitchen")
    _, h_price, h_q, h_dur = pick_tier("hall")
    return (k_q, k_price, k_dur), (h_q, h_price, h_dur)


def hire_menu(state: GameState) -> None:
    """
    Staff hiring menu. Presents random candidates one at a time.

    Each candidate has a random skill (1-10) and a salary of
    skill × Config.DAILY_SALARY_PER_SKILL per day.
    The player can hire, skip, or stop browsing.
    """
    print(f"\n{cp('👥 Hire Staff', C.bold + C.cyan)}")
    print(f"Budget: {fmt_money(state.budget)} | Salary: ${Config.DAILY_SALARY_PER_SKILL}/day per skill level")

    while True:
        skill = random.randint(1, 10)
        daily_salary = skill * Config.DAILY_SALARY_PER_SKILL
        per_tick = daily_salary / state.total_ticks

        recovery_rate = Config.STAMINA_RECOVERY_BASE + int(
            state.kitchen.effective_quality * Config.STAMINA_RECOVERY_KITCHEN_BONUS
        )
        print(f"\nCandidate: Skill={skill}, Salary={fmt_money(daily_salary)}/day ({fmt_money(per_tick)}/tick)")
        print(f"  Stamina recovery: +{recovery_rate}/tick when idle")

        ans = input("Hire? (y/n/stop): ").strip().lower()

        if ans == 'y':
            state.hire_staff(skill, daily_salary)
            print(cp(f"  Hired! Staff count: {len(state.staff_list)}", C.green))
        elif ans == 'stop':
            break
        else:
            if input("See another candidate? (y/n): ").strip().lower() != 'y':
                break


def equipment_shop(state: GameState) -> None:
    """
    In-game equipment management: upgrade or repair kitchen/hall.

    Options:
    1. Upgrade Kitchen — buy a new tier (replaces old equipment)
    2. Upgrade Hall — buy a new tier
    3. Repair Kitchen — restore 50 durability for Config.REPAIR_COST
    4. Repair Hall — restore 50 durability
    """
    print(f"\n{cp('🛒 Equipment Shop', C.bold + C.cyan)}")
    print(f"Budget: {fmt_money(state.budget)}")
    print(f"Current: Kitchen Q={state.kitchen.quality} Dur={state.kitchen.durability_pct:.0f}% | "
          f"Hall Q={state.hall.quality} Dur={state.hall.durability_pct:.0f}%")
    print("\n1. Upgrade Kitchen")
    print("2. Upgrade Hall")
    print("3. Repair Kitchen (restores 50 dur)")
    print("4. Repair Hall (restores 50 dur)")

    choice = input("Your choice (1-4/cancel): ").strip()

    # --- Upgrade path ---
    if choice in ('1', '2'):
        slot_name = "kitchen" if choice == '1' else "hall"
        equip = state.kitchen if choice == '1' else state.hall

        print("\nAvailable tiers:")
        _display_equipment_tiers()

        tier = input("Select tier (1-3): ").strip()
        if tier not in EQUIPMENT_TIERS:
            return

        name, price, quality, max_dur = EQUIPMENT_TIERS[tier]
        if state.budget < price:
            print(cp("Not enough funds!", C.red))
            return

        equip.replace(quality, price, max_dur)
        state.budget -= price
        print(cp(f"  {slot_name} upgraded to '{name}' Q={quality} Dur={max_dur}.", C.green))

    # --- Repair path ---
    elif choice in ('3', '4'):
        slot_name = "kitchen" if choice == '3' else "hall"
        equip = state.kitchen if choice == '3' else state.hall

        if equip.durability >= equip.max_durability:
            print(cp("  Already at full durability!", C.yellow))
            return

        if state.budget < Config.REPAIR_COST:
            print(cp("Not enough funds!", C.red))
            return

        state.budget -= Config.REPAIR_COST
        equip.repair()
        print(cp(f"  {slot_name} repaired (+{Config.REPAIR_AMOUNT} durability). Cost: {fmt_money(Config.REPAIR_COST)}", C.green))


def show_status(state: GameState) -> None:
    """
    Display comprehensive current state of the restaurant.

    Shows: equipment quality/durability bars, staff stamina/status,
    queued guests with wait progress, active effects, statistics,
    and historical day-by-day profit summary.
    """
    # Header
    print(f"\n{cp('┃' + '=' * 58 + '┃', C.dim)}")
    print(f"{cp(f'┃  {state.current_time_str()}  ┃  Day {state.day}  ┃  T {state.tick + 1}/{state.total_ticks}  ┃', C.bold)} "
          f"{fmt_money(state.budget)}  {fmt_rep(state.reputation)}")
    print(f"{cp('┃' + '=' * 58 + '┃', C.dim)}")

    # Equipment
    print(f"\n{cp('🔧 Equipment:', C.bold)}")
    print(f"  Kitchen: Q={state.kitchen.quality} Dur={progress_bar(state.kitchen.durability, state.kitchen.max_durability)}")
    print(f"  Hall:    Q={state.hall.quality} Dur={progress_bar(state.hall.durability, state.hall.max_durability)}")
    print(f"  Average Quality: {state.avg_equipment_quality:.1f}")

    # Staff
    print(f"\n{cp(f'👥 Staff ({len(state.staff_list)}):', C.bold)}")
    for i, s in enumerate(state.staff_list):
        status = cp("✅ Free", C.green) if s.is_free else cp("⛔ Busy/Tired", C.yellow)
        print(f"  {i + 1}. Skill={s.skill} Salary={fmt_money(s.daily_salary)}/day "
              f"Stamina={progress_bar(s.stamina, s.max_stamina)} {status}")

    # Guest queue
    print(f"\n{cp(f'🧍 Guests in queue ({len(state.guest_queue)}):', C.bold)}")
    if not state.guest_queue:
        print(f"  {cp('(empty)', C.dim)}")
    for g in state.guest_queue:
        print(f"  {g.icon} {g.label} Budget=${g.budget:.1f} Exp={g.expectation:.1f} "
              f"Wait={progress_bar(g.wait_timer, g.patience_ticks)}")

    # Active effects
    if state.rush_hour_active:
        print(f"\n  {cp(f'⚡ RUSH HOUR active! ({state.rush_hour_remaining} ticks left)', C.bold + C.yellow)}")

    # Statistics
    print(f"\n{cp('📊 Statistics:', C.bold)}")
    print(f"  Served: {state.served_total} (Success: {state.served_success}, Failed: {state.served_fail})")
    print(f"  Left without service: {state.left_guests}")

    # Day history
    if state.day_history:
        print(f"\n{cp('📈 Day History:', C.bold)}")
        for i, dh in enumerate(state.day_history, 1):
            profit = dh["end_budget"] - dh["start_budget"]
            sign = "+" if profit >= 0 else ""
            color = C.green if profit >= 0 else C.red
            print(f"  Day {i}: {fmt_money(dh['end_budget'])} "
                  f"(Profit: {cp(f'{sign}${profit:.2f}', color)})")


def show_day_summary(state: GameState) -> None:
    """
    Display end-of-day summary report.

    Includes: final time, budget change, daily profit, reputation,
    guest statistics (served/success/fail/left), success rate,
    staff count, equipment state, and multi-day cumulative profit.
    """
    print(f"\n{cp('=' * 60, C.bold + C.cyan)}")
    print(f"{cp(f'         📊 DAY {state.day} SUMMARY', C.bold + C.cyan)}")
    print(f"{cp('=' * 60, C.bold + C.cyan)}")
    print(f"⏰ Closing time: {state.current_time_str()}")

    # Calculate daily profit
    start_budget = state.day_history[-1]["end_budget"] if state.day_history else Config.STARTING_BUDGET
    profit = state.budget - start_budget
    sign = "+" if profit >= 0 else ""
    profit_color = C.green if profit >= 0 else C.red

    print(f"💰 Start budget: {fmt_money(start_budget)}")
    print(f"💰 End budget:   {fmt_money(state.budget)}")
    print(f"📈 Daily profit: {cp(f'{sign}${profit:.2f}', profit_color)}")
    print(f"⭐ Reputation:  {state.reputation}")

    # Guest statistics
    print(f"\n👥 Guests served: {state.served_total}")
    print(f"   ✅ Success: {state.served_success}")
    print(f"   ❌ Failed:  {state.served_fail}")
    print(f"   🚶 Left:    {state.left_guests}")

    success_rate = (state.served_success / state.served_total * 100) if state.served_total > 0 else 0
    print(f"   Success rate: {success_rate:.0f}%")

    # Staff and equipment state
    print(f"\n👨‍🍳 Staff remaining: {len(state.staff_list)}")
    print(f"🔧 Equipment: Kitchen Q={state.kitchen.quality} ({state.kitchen.durability_pct:.0f}%) | "
          f"Hall Q={state.hall.quality} ({state.hall.durability_pct:.0f}%)")

    # Game-over conditions
    if state.reputation < Config.BANKRUPTCY_REP:
        print(f"\n{cp('💥 RESTAURANT BANKRUPT!', C.bold + C.red)}")
    elif state.budget < Config.DEBT_LIMIT:
        print(f"\n{cp('💸 Deep in debt! Next day must improve!', C.bold + C.red)}")

    # Multi-day summary
    if state.day_history:
        print(f"\n{cp('📈 All Days Summary:', C.bold)}")
        total_profit = state.budget - Config.STARTING_BUDGET
        sign_total = "+" if total_profit >= 0 else ""
        total_color = C.green if total_profit >= 0 else C.red
        print(f"  Total profit across {state.day} days: {cp(f'{sign_total}${total_profit:.2f}', total_color)}")
        for i, dh in enumerate(state.day_history, 1):
            p = dh["end_budget"] - dh["start_budget"]
            s = "+" if p >= 0 else ""
            print(f"  Day {i}: {s}${p:.2f}")
        p_now = state.budget - (state.day_history[-1]["end_budget"] if state.day_history else Config.STARTING_BUDGET)
        s_now = "+" if p_now >= 0 else ""
        print(f"  Day {state.day}: {s_now}${p_now:.2f}")

    print(f"{cp('=' * 60, C.bold + C.cyan)}")


# ==============================================================================
# 5. MAIN LOOP
# ==============================================================================

def _restore_from_history(state: GameState, prev: Dict) -> None:
    """
    Restore game state from a previous day's snapshot.

    Carry-over rules:
    • Budget: preserved exactly
    • Reputation: 80% of previous end value (partial decay)
    • Equipment: preserved with current durability
    • Staff: preserved, stamina fully restored, busy timers reset
    """
    state.budget = prev["end_budget"]
    state.reputation = max(0, prev["end_reputation"] * 0.8)
    state.kitchen = prev["kitchen"]
    state.hall = prev["hall"]
    state.staff_list = prev["staff_list"]

    for s in state.staff_list:
        s.stamina = s.max_stamina
        s.busy_timer = 0

    state.day_history = prev["day_history"]


def _select_tick_duration(state: GameState) -> None:
    """Prompt the player to choose the tick-to-minute ratio."""
    print(f"\n⏱️ Select tick duration (in-game minutes):")
    options = {'1': 1, '5': 5, '10': 10, '15': 15, '30': 30}

    while True:
        sel = input("1 / 5 / 10 / 15 / 30 (default 5): ").strip()
        if sel == '':
            sel = '5'
        if sel in options:
            state.tick_minutes = options[sel]
            break
        print(cp("Please enter a valid number.", C.red))

    total_work_minutes = (Config.WORK_END_HOUR - Config.WORK_START_HOUR) * 60
    state.total_ticks = total_work_minutes // state.tick_minutes
    print(f"  Work day: {state.total_ticks} ticks ({Config.WORK_START_HOUR:02d}:00 to {Config.WORK_END_HOUR:02d}:00)")


def _setup_new_day(state: GameState) -> bool:
    """
    Execute the between-days setup phase: tick duration, equipment, hiring.

    Returns False if the player cannot start the day (no staff, insufficient funds).
    """
    _select_tick_duration(state)

    # Equipment purchase (Day 1 only) or upgrade option (subsequent days)
    if not state.day_history:
        print(f"\nStarting budget: {fmt_money(state.budget)}")
        (k_q, k_price, k_dur), (h_q, h_price, h_dur) = choose_equipment(state)
        total_cost = k_price + h_price
        if state.budget < total_cost:
            print(cp("Not enough money for basic equipment! Game over.", C.red))
            return False
        state.budget -= total_cost
        state.kitchen = Equipment("Kitchen", k_q, k_price, k_dur)
        state.hall = Equipment("Hall", h_q, h_price, h_dur)
        print(f"  Equipment purchased. Budget: {fmt_money(state.budget)}")
    else:
        print(f"\n{cp('Existing equipment carried over.', C.dim)}")
        print(f"  Kitchen Q={state.kitchen.quality} Dur={state.kitchen.durability_pct:.0f}%")
        print(f"  Hall Q={state.hall.quality} Dur={state.hall.durability_pct:.0f}%")
        print(f"\nWant to upgrade equipment before starting the day?")
        if input("Upgrade? (y/n): ").strip().lower() == 'y':
            equipment_shop(state)

    # Staff hiring
    if not state.staff_list:
        hire_menu(state)
        if not state.staff_list:
            print(cp("You need at least one staff member to operate!", C.red))
            return False
    else:
        print(f"\n{len(state.staff_list)} staff carried over. Hire more?")
        if input("Hire additional staff? (y/n): ").strip().lower() == 'y':
            hire_menu(state)

    if not state.staff_list:
        print(cp("You need at least one staff member!", C.red))
        return False

    return True


def _record_day_snapshot(state: GameState) -> None:
    """Save current state to day_history for multi-day persistence."""
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


def _process_command(state: GameState) -> str:
    """
    Display the status bar, read player input, and execute the chosen command.

    Returns:
    • 'continue' — normal operation, keep processing ticks
    • 'break' — exit the tick loop (quit, bankruptcy, etc.)
    """
    # Status bar
    print(f"\n{cp('┃', C.dim)} {state.current_time_str()} {cp('┃', C.dim)} "
          f"Day {state.day} T {state.tick + 1}/{state.total_ticks} {cp('┃', C.dim)} "
          f"{fmt_money(state.budget)} {fmt_rep(state.reputation)} {cp('┃', C.dim)} "
          f"Staff:{len(state.staff_list)} Queue:{len(state.guest_queue)}")

    cmd = input("Action: next / run N / hire / fire / shop / status / quit: ").strip().lower()

    if cmd == 'next':
        events = process_tick(state)
        for e in events:
            print(e)
        if state.reputation < Config.BANKRUPTCY_REP:
            print(cp("Bankrupt!", C.red))
            return 'break'
        return 'continue'

    elif cmd.startswith('run'):
        parts = cmd.split()
        if len(parts) == 2 and parts[1].isdigit():
            n = int(parts[1])
            n = min(n, state.time_remaining())
            if n > 0:
                print(cp(f"⏩ Fast-forwarding {n} ticks...", C.dim))
                events = run_ticks(state, n)
                for e in events:
                    print(e)
            if state.reputation < Config.BANKRUPTCY_REP:
                print(cp("Bankrupt during fast-forward!", C.red))
                return 'break'
        else:
            print("Usage: run <number>")
        return 'continue'

    elif cmd == 'hire':
        hire_menu(state)
        return 'continue'

    elif cmd == 'fire':
        if not state.staff_list:
            print(cp("No staff to fire.", C.yellow))
            return 'continue'
        for i, s in enumerate(state.staff_list):
            status = cp("free", C.green) if s.is_free else cp("busy/tired", C.yellow)
            print(f"  {i + 1}. Skill={s.skill} Stamina={s.stamina}/{s.max_stamina} "
                  f"Salary={fmt_money(s.daily_salary)}/day {status}")
        try:
            idx = int(input("Number to fire (0 = cancel): ")) - 1
            if idx >= 0:
                state.fire_staff(idx)
                print(cp("  Staff member fired.", C.yellow))
        except ValueError:
            pass
        return 'continue'

    elif cmd == 'shop':
        equipment_shop(state)
        return 'continue'

    elif cmd == 'status':
        show_status(state)
        return 'continue'

    elif cmd == 'quit':
        print(cp("Ending day early.", C.yellow))
        return 'break'

    else:
        print(cp("Unknown command.", C.red))
        return 'continue'


def _run_day(state: GameState) -> None:
    """Execute the main tick loop for a single day."""
    # Update the snapshot's start_budget to reflect any between-day purchases
    if state.day_history:
        state.day_history[-1]["start_budget"] = state.budget
        state.day_history[-1]["start_reputation"] = state.reputation

    while True:
        # Check day-end condition
        if state.tick >= state.total_ticks or state.reputation < Config.BANKRUPTCY_REP:
            break

        # Check debt condition (two consecutive days triggers game over)
        if state.budget < Config.DEBT_LIMIT:
            state.debt_days += 1
            if state.debt_days >= Config.DEBT_DAYS_LIMIT:
                print(cp("💸 Two days in deep debt. Game over!", C.red))
                break
            print(cp(f"💸 WARNING: Deep debt! (Day {state.debt_days}/{Config.DEBT_DAYS_LIMIT})", C.yellow))
        else:
            state.debt_days = 0

        # Process player command
        action = _process_command(state)
        if action == 'break':
            break

    # Update day snapshot with final values
    if state.day_history:
        state.day_history[-1]["end_budget"] = state.budget
        state.day_history[-1]["end_reputation"] = state.reputation


def main() -> None:
    """
    Game entry point. Manages the multi-day lifecycle:

    1. Welcome screen
    2. For each day:
       a. Restore state from previous day (if applicable)
       b. Between-day setup (tick duration, equipment, hiring)
       c. Run the day's tick loop
       d. Show day summary
       e. Check game-over conditions
       f. Ask to continue to next day
    """
    print(f"\n{cp('🌟 Welcome to Restaurant Simulator v3! 🌟', C.bold + C.cyan)}")
    print(f"{cp('Manage your restaurant across multiple days!', C.dim)}")

    day_loop = True
    while day_loop:
        state = GameState()

        # --- Day start banner ---
        if not state.day_history:
            print(f"\n{cp('Day 1 — New Restaurant!', C.bold + C.green)}")
        else:
            print(f"\n{cp(f'Day {state.day} — Carrying over from previous day', C.bold + C.green)}")
            prev = state.day_history[-1]
            _restore_from_history(state, prev)
            print(f"  Budget: {fmt_money(state.budget)} | Reputation: {state.reputation:.0f}")
            print(f"  Equipment: Kitchen Q={state.kitchen.quality} | Hall Q={state.hall.quality}")
            print(f"  Staff: {len(state.staff_list)} (fully rested)")

        # --- Between-day setup ---
        if not _setup_new_day(state):
            return

        # --- Record initial snapshot ---
        _record_day_snapshot(state)

        # --- Run the day ---
        _run_day(state)

        # --- Day summary ---
        show_day_summary(state)

        # --- Game-over check ---
        if state.reputation < Config.BANKRUPTCY_REP or state.budget < Config.DEBT_LIMIT:
            print(cp("\nGame Over! Thanks for playing!", C.bold + C.red))
            return

        # --- Continue to next day? ---
        print(f"\n{cp('Continue to next day?', C.bold)}")
        cont = input("Continue? (y/n): ").strip().lower()
        if cont != 'y':
            print(cp("Thanks for playing!", C.bold + C.cyan))
            return

        state.day += 1


if __name__ == "__main__":
    main()
