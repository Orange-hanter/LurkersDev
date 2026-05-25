# Restaurant Simulator v4 — pygame Architecture Design

## Overview

Refactor the restaurant simulator from a single-file terminal game into a pygame-based application with:
- Continuous real-time game loop (no manual "next" command)
- Adjustable game speed (+/- keys, pause with space)
- Procedural 8-bit chiptune music (numpy + pygame.mixer)
- Full package structure with separated domain, engine, UI, and audio layers

## File Structure

```
restaurant_simulator/
├── __main__.py              # Entry: python -m restaurant_simulator
├── config.py                # Game balance constants (moved from Config class)
├── models/
│   ├── __init__.py
│   ├── equipment.py         # Equipment class
│   ├── staff.py             # Staff class
│   ├── guest.py             # Guest class + GUEST_TYPES
│   └── game_state.py        # GameState class
├── engine/
│   ├── __init__.py
│   ├── tick.py              # process_tick(state) → List[dict]
│   ├── events.py            # RandomEvent + handlers
│   └── spawning.py          # spawn logic
├── ui/
│   ├── __init__.py
│   ├── renderer.py          # Pygame drawing utilities
│   ├── screens.py           # Screen classes (Menu, Game, Shop, Summary)
│   └── input_handler.py     # Key/mouse routing
├── audio/
│   ├── __init__.py
│   ├── music.py             # Playback controller
│   └── tunes.py             # Melody data
└── main.py                  # pygame init + game loop + state machine
```

## Core Game Loop

- pygame runs at 60 FPS via `clock.tick(60)`
- Game ticks fire based on elapsed time × `game_speed` multiplier
- Default: 1 tick per 0.5 seconds → `tick_interval = 0.5`
- Speed range: 0.25x to 4.0x (adjustable with +/-)
- Space toggles pause
- M toggles music mute

## State Machine

```
MainMenu → DaySetup → GamePlaying → DaySummary → (NextDay / GameOver)
```

Each screen has: `handle_input(events)`, `update(dt)`, `render(surface)`.

## UI Design

- Window: 960×640, dark background (#1a1a2e)
- Top bar: `HH:MM | Day N | T x/y | 💰$N | ⭐+N | Speed: 1.0x`
- Center: Scrolling event log (15 lines) + guest queue
- Bottom: Equipment durability bars + staff stamina bars
- Modals: Shop, Hire, Day Summary (centered overlay with dimmed background)

## Music System

- numpy generates audio buffers (square/triangle waves, 44100 Hz)
- pygame.mixer.Sound plays buffers
- 3 melodies: Day theme, Rush hour, Quiet hour
- Controls: M (mute), [ ] (volume down/up), 1/2/3 (track switch)

## Dependencies

- pygame (new)
- numpy (already installed)
