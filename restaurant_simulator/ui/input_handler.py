import pygame
from typing import Callable, Dict, List


class InputHandler:
    def __init__(self):
        self.keys_pressed: set[int] = set()
        self.key_callbacks: Dict[int, Callable] = {}

    def register_key(self, key: int, callback: Callable) -> None:
        self.key_callbacks[key] = callback

    def handle_events(self, events: List[pygame.event.Event]) -> List[pygame.event.Event]:
        for event in events:
            if event.type == pygame.KEYDOWN:
                self.keys_pressed.add(event.key)
                if event.key in self.key_callbacks:
                    self.key_callbacks[event.key]()
            elif event.type == pygame.KEYUP:
                self.keys_pressed.discard(event.key)
        return events

    def is_key_pressed(self, key: int) -> bool:
        return key in self.keys_pressed

    def clear(self) -> None:
        self.keys_pressed.clear()
