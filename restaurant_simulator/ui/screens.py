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
        self.renderer.draw_text(f"Day {s.day} | {s.current_time_str()} | T {s.tick}/{s.total_ticks} | ${s.budget:.2f} | Rep {s.reputation:+.0f} | {speed_label}", 5, 5, speed_color, "bold")

        table_section_y = 40
        table_section_h = ((len(s.tables) + 4) // 5) * 60 + 45
        self.renderer.draw_rect(5, table_section_y, 480, table_section_h, "panel", 1)
        self.renderer.draw_text(" TABLES", 5, table_section_y - 18, "cyan", "bold")
        bx, by = 15, table_section_y + 5
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
        if s.kitchen.needs_repair:
            self.renderer.draw_text("LOW!", equip_x + 155, equip_y + 18, "red", "tiny")

        self.renderer.draw_text(f"Hall Q={s.hall.effective_quality:.1f}", equip_x, equip_y + 40, "white", "small")
        self.renderer.draw_progress_bar(equip_x, equip_y + 55, s.hall.durability, s.hall.max_durability, 150, 10)
        if s.hall.needs_repair:
            self.renderer.draw_text("LOW!", equip_x + 155, equip_y + 53, "red", "tiny")

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
        self.renderer.draw_text_centered(f"Served: {s.guests_served} | Lost: {s.lost_guests} | Avg Quality: {avg_q:.1f}", 160, "white", "small")

        salary_total = sum(st.daily_salary for st in s.staff_list)
        self.renderer.draw_text_centered(f"Income: +${s.pending_income:.2f} | Refunds: -${s.pending_expense - salary_total:.2f} | Salaries: -${salary_total:.2f}", 185, "white", "small")
        self.renderer.draw_text_centered(f"Kitchen Q={s.kitchen.effective_quality:.1f} ({s.kitchen.durability_pct:.0f}%) | Hall Q={s.hall.effective_quality:.1f} ({s.hall.durability_pct:.0f}%) | Staff: {len(s.staff_list)}", 220, "dim", "small")

        if s.kitchen.needs_repair or s.hall.needs_repair:
            self.renderer.draw_text_centered("WARNING: Equipment durability critical! Quality halved.", 250, "red", "bold")

        if s.budget <= 0 or s.reputation <= REP_MIN:
            self.renderer.draw_text_centered("BANKRUPT! GAME OVER", 310, "red", "large")
            self.result = "quit"
        else:
            self.renderer.draw_text_centered("ENTER: Next Day  ESC: Quit", 380, "dim", "small")
