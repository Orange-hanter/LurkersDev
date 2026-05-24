import pygame


class InputHandler:
    def __init__(self):
        self.keys_pressed = set()

    def handle_events(self) -> list[pygame.event.Event]:
        events = []
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                self.keys_pressed.add(event.key)
            elif event.type == pygame.KEYUP:
                self.keys_pressed.discard(event.key)
            events.append(event)
        return events

    def is_key_pressed(self, key: int) -> bool:
        return key in self.keys_pressed
