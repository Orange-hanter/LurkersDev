"""
Procedural chiptune melody definitions.
Each tune is a dict with:
  - notes: list of (frequency_hz, duration_beats) tuples. None = rest.
  - bpm: beats per minute
  - waveform: "square" or "triangle"
  - loop: bool (whether to repeat)
"""

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
