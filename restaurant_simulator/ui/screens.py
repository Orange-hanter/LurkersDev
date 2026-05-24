import pygame
import random
from typing import List
from ..models import GameState
from ..config import (
    WINDOW_WIDTH, WINDOW_HEIGHT, WORK_START_HOUR, WORK_END_HOUR,
    REPAIR_COST, DAILY_SALARY_PER_SKILL,
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
        self.renderer.draw_text_centered("Restaurant Simulator v4", 200, "cyan", "large")
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
        self.renderer.draw_text_centered("Select Tick Duration", 100, "cyan", "large")
        for i, opt in enumerate(self.options):
            color = "green" if opt == self.selection else "white"
            ticks_per_day = (WORK_END_HOUR - WORK_START_HOUR) * 60 // opt
            label = f"{'> ' if opt == self.selection else '  '}{opt} min/tick  ({ticks_per_day} ticks/day)"
            self.renderer.draw_text_centered(label, 200 + i * 40, color)
        self.renderer.draw_text_centered("UP/DOWN to select, ENTER to confirm", 450, "dim", "small")
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

    def render(self) -> None:
        self.renderer.clear()
        s = self.state

        self.renderer.draw_rect(0, 0, WINDOW_WIDTH, 30, "bar_bg")
        speed_label = "PAUSED" if self.paused else f"{self.game_speed:.1f}x"
        speed_color = "yellow" if self.paused else "green"
        self.renderer.draw_text(f"  {s.current_time_str()} | Day {s.day} | T {s.tick+1}/{s.total_ticks} | ${s.budget:.2f} | Rep {s.reputation:+.0f} | Queue: {len(s.guest_queue)} | Speed: {speed_label}", 0, 5, speed_color, "bold")

        y = 45
        self.renderer.draw_text("Events:", 10, y, "cyan", "bold")
        y += 20
        for msg in self.event_log[-12:]:
            color = "white"
            if "Success" in msg:
                color = "green"
            elif "Failed" in msg or "malfunction" in msg:
                color = "red"
            elif "left" in msg.lower():
                color = "yellow"
            self.renderer.draw_text(f"  {msg}", 10, y, color, "small")
            y += 18

        rx = 600
        self.renderer.draw_text("Equipment:", rx, 45, "cyan", "bold")
        self.renderer.draw_text(f"Kitchen Q={s.kitchen.quality}", rx, 70, "white", "small")
        self.renderer.draw_progress_bar(rx, 85, s.kitchen.durability, s.kitchen.max_durability, 150, 10)
        self.renderer.draw_text(f"Hall    Q={s.hall.quality}", rx, 110, "white", "small")
        self.renderer.draw_progress_bar(rx, 125, s.hall.durability, s.hall.max_durability, 150, 10)

        self.renderer.draw_text(f"Staff ({len(s.staff_list)}):", rx, 160, "cyan", "bold")
        for i, staff in enumerate(s.staff_list):
            status = "Free" if staff.is_free else "Busy"
            self.renderer.draw_text(f"#{i+1} Sk={staff.skill} {status}", rx, 180 + i * 35, "white", "small")
            self.renderer.draw_progress_bar(rx, 195 + i * 35, staff.stamina, staff.max_stamina, 150, 8)

        self.renderer.draw_text(f"Queue ({len(s.guest_queue)}):", 10, WINDOW_HEIGHT - 100, "cyan", "bold")
        for i, guest in enumerate(s.guest_queue[:5]):
            self.renderer.draw_text(f"  {guest.icon} {guest.label} Budget=${guest.budget:.0f} Exp={guest.expectation:.1f}", 10, WINDOW_HEIGHT - 80 + i * 18, "white", "small")
        if len(s.guest_queue) > 5:
            self.renderer.draw_text(f"  ... +{len(s.guest_queue) - 5} more", 10, WINDOW_HEIGHT - 80 + 5 * 18, "dim", "small")

        self.renderer.draw_text("Space:Pause  +/-:Speed  M:Music  S:Shop  H:Hire  Q:End Day  ESC:Quit", 10, WINDOW_HEIGHT - 18, "dim", "small")


EQUIPMENT_TIERS = {
    0: ("Basic", 50, 1, 80),
    1: ("Standard", 100, 3, 120),
    2: ("Premium", 180, 5, 150),
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
        self.input.register_key(pygame.K_k, self._switch_kitchen)
        self.input.register_key(pygame.K_l, self._switch_hall)
        self.slot = "kitchen"

    def _prev(self) -> None:
        self.cursor = max(0, self.cursor - 1)

    def _next(self) -> None:
        self.cursor = min(len(self.tier_keys) - 1, self.cursor + 1)

    def _switch_kitchen(self) -> None:
        self.slot = "kitchen"

    def _switch_hall(self) -> None:
        self.slot = "hall"

    def _buy(self) -> None:
        name, price, quality, max_dur = EQUIPMENT_TIERS[self.cursor]
        if self.state.budget >= price:
            self.state.budget -= price
            equip = self.state.kitchen if self.slot == "kitchen" else self.state.hall
            equip.replace(quality, price, max_dur)
            self.result = "bought"
            self.exit()

    def _repair(self) -> None:
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
        self.renderer.draw_text_centered("Equipment Shop", 100, "cyan", "large")
        self.renderer.draw_text_centered(f"Budget: ${self.state.budget:.2f}", 140, "green", "bold")
        self.renderer.draw_text_centered("K: Switch Kitchen  L: Switch Hall  R: Repair  ESC: Close", 180, "dim", "small")
        equip = getattr(self.state, self.slot)
        self.renderer.draw_text_centered(f"Current: {self.slot.title()} Q={equip.quality} Dur={equip.durability_pct:.0f}%", 210, "white", "small")
        for i, (name, price, quality, max_dur) in EQUIPMENT_TIERS.items():
            color = "green" if i == self.cursor else "white"
            prefix = "> " if i == self.cursor else "  "
            self.renderer.draw_text_centered(f"{prefix}{name}: ${price} | Q={quality} | MaxDur={max_dur}", 260 + i * 40, color)
        self.renderer.draw_text_centered("UP/DOWN to select, ENTER to buy, R to repair", 420, "dim", "small")


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

    def _skip(self) -> None:
        self._reroll()

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
        recovery = 5 + int(self.state.kitchen.effective_quality * 0.5)
        per_tick = self.candidate_salary / self.state.total_ticks if self.state.total_ticks > 0 else 0
        self.renderer.draw_text_centered(f"Skill: {self.candidate_skill}", 220, "white", "large")
        self.renderer.draw_text_centered(f"Salary: ${self.candidate_salary}/day (${per_tick:.2f}/tick)", 260, "yellow", "bold")
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
        self.renderer.draw_text_centered(f"Day {s.day} Summary", 50, "cyan", "large")
        start = s.day_history[-1]["end_budget"] if s.day_history else 500
        profit = s.budget - start
        self.renderer.draw_text_centered(f"Budget: ${start:.2f} -> ${s.budget:.2f}", 100, "green" if profit >= 0 else "red", "bold")
        self.renderer.draw_text_centered(f"Profit: {'+' if profit >= 0 else ''}${profit:.2f}", 130, "green" if profit >= 0 else "red")
        self.renderer.draw_text_centered(f"Reputation: {s.reputation:+.0f}", 160, "yellow")
        success_rate = (s.served_success / s.served_total * 100) if s.served_total > 0 else 0
        self.renderer.draw_text_centered(f"Served: {s.served_total} (Success: {s.served_success}, Failed: {s.served_fail}, Left: {s.left_guests})", 200, "white", "small")
        self.renderer.draw_text_centered(f"Success rate: {success_rate:.0f}%", 220, "white", "small")
        self.renderer.draw_text_centered(f"Staff: {len(s.staff_list)} | Kitchen Q={s.kitchen.quality} ({s.kitchen.durability_pct:.0f}%) | Hall Q={s.hall.quality} ({s.hall.durability_pct:.0f}%)", 260, "dim", "small")
        if s.reputation < -20:
            self.renderer.draw_text_centered("BANKRUPT!", 310, "red", "large")
        self.renderer.draw_text_centered("ENTER: Next Day  ESC: Quit", 380, "dim", "small")
