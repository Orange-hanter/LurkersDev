"""Main entry point: pygame init, game loop, state machine."""
import pygame
from .config import WINDOW_WIDTH, WINDOW_HEIGHT, FPS, DEFAULT_TICK_INTERVAL, BANKRUPTCY_REP
from .models import GameState
from .ui import Renderer, InputHandler, MainMenu, DaySetupScreen, GameScreen, DaySummaryScreen, ShopScreen, HireScreen
from .audio import MusicPlayer
from .engine.tick import process_tick


class _ScreenSwitch(Exception):
    """Internal exception for switching screens from within the tick loop."""
    def __init__(self, screen):
        self.screen = screen


def _record_snapshot(state: GameState) -> None:
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
    })


def _transition(screen, renderer, state, is_first_day):
    """
    Handle screen transitions based on current screen result.

    Returns (next_screen, new_is_first_day) tuple.
    The is_first_day flag must be returned because Python booleans are immutable.
    """
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
        if screen.result == "next_day" and state.reputation >= BANKRUPTCY_REP:
            state.day += 1
            return DaySetupScreen(renderer, InputHandler(), state, False), False
        return None, is_first_day

    return screen, is_first_day


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
                tick_interval = DEFAULT_TICK_INTERVAL / state.tick_minutes * 5
                music.play_tune("day_theme")
            elif isinstance(current_screen, (MainMenu, DaySummaryScreen)):
                music.stop()

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

            # Handle pending screen switches from GameScreen (shop/hire)
            if isinstance(current_screen, GameScreen) and current_screen.pending_action and current_screen.running:
                action = current_screen.pending_action
                current_screen.pending_action = None
                if action == "shop":
                    current_screen = ShopScreen(renderer, InputHandler(), state)
                elif action == "hire":
                    current_screen = HireScreen(renderer, InputHandler(), state)

            # Handle shop/hire return to game
            if isinstance(current_screen, (ShopScreen, HireScreen)) and not current_screen.running:
                current_screen = GameScreen(renderer, InputHandler(), state)

            # Update music based on rush hour
            if isinstance(current_screen, GameScreen) and music.playing:
                if state.rush_hour_active and music.current_tune != "rush_hour":
                    music.play_tune("rush_hour")
                elif not state.rush_hour_active and music.current_tune != "day_theme":
                    music.play_tune("day_theme")
                if music.muted != current_screen.music_muted:
                    music.set_muted(current_screen.music_muted)

    music.stop()
    pygame.quit()
