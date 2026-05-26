import pygame
import random
from .config import WINDOW_WIDTH, WINDOW_HEIGHT, FPS, DEFAULT_TICK_INTERVAL, DAILY_EVENT_CHANCE, TOTAL_TICKS_PER_DAY, RANDOM_EVENT_CHANCE
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
            return daily_event.handler(state)
    return ""


def main() -> None:
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
                        current_screen.log_event(f"{g.icon} Success! {g.label} Q={e['quality']:.1f} +${e['income']:.2f}")
                    elif e["type"] == "failure":
                        g = e["guest"]
                        current_screen.log_event(f"{g.icon} Failed! {g.label} Q={e['quality']:.1f} -${e['loss']:.2f}")
                    elif e["type"] == "left":
                        g = e["guest"]
                        current_screen.log_event(f"{g.icon} {g.label} left (waited {g.wait_timer}/{g.patience_ticks})")
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

            if isinstance(current_screen, GameScreen) and not current_screen.paused and elapsed == 0:
                if random.random() < RANDOM_EVENT_CHANCE:
                    tick_event = pick_random_event(TICK_EVENTS)
                    if tick_event:
                        result = tick_event.handler(state)
                        current_screen.log_event(result)

    music.stop()
    pygame.quit()