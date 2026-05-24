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
        else:
            samples = np.sign(np.sin(2 * np.pi * freq * t))
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
