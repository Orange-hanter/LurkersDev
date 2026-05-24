import pygame
from ..config import BG_COLOR


class Renderer:
    def __init__(self, surface: pygame.Surface):
        self.surface = surface
        self.width, self.height = surface.get_size()
        self.font = pygame.font.SysFont("monospace", 16)
        self.font_bold = pygame.font.SysFont("monospace", 16, bold=True)
        self.font_large = pygame.font.SysFont("monospace", 24, bold=True)
        self.font_small = pygame.font.SysFont("monospace", 14)
        self.colors = {
            "green": (50, 205, 50),
            "red": (255, 69, 69),
            "yellow": (255, 215, 0),
            "cyan": (0, 255, 255),
            "magenta": (255, 105, 180),
            "white": (255, 255, 255),
            "dim": (150, 150, 150),
            "bar_bg": (60, 60, 60),
        }

    def clear(self) -> None:
        self.surface.fill(BG_COLOR)

    def draw_text(self, text: str, x: int, y: int, color: str = "white", font: str = "normal") -> None:
        f = self.font_bold if font == "bold" else self.font_large if font == "large" else self.font_small if font == "small" else self.font
        surf = f.render(str(text), True, self.colors.get(color, self.colors["white"]))
        self.surface.blit(surf, (x, y))

    def draw_text_centered(self, text: str, y: int, color: str = "white", font: str = "normal") -> int:
        f = self.font_bold if font == "bold" else self.font_large if font == "large" else self.font_small if font == "small" else self.font
        surf = f.render(str(text), True, self.colors.get(color, self.colors["white"]))
        x = (self.width - surf.get_width()) // 2
        self.surface.blit(surf, (x, y))
        return surf.get_width()

    def draw_progress_bar(self, x: int, y: int, current: float, maximum: float, width: int = 100, height: int = 12) -> None:
        ratio = max(0, min(1, current / maximum)) if maximum > 0 else 0
        filled = int(width * ratio)
        pygame.draw.rect(self.surface, self.colors["bar_bg"], (x, y, width, height))
        if ratio > 0.6:
            color = self.colors["green"]
        elif ratio > 0.3:
            color = self.colors["yellow"]
        else:
            color = self.colors["red"]
        if filled > 0:
            pygame.draw.rect(self.surface, color, (x, y, filled, height))

    def draw_rect(self, x: int, y: int, w: int, h: int, color: str, outline: int = 0) -> None:
        pygame.draw.rect(self.surface, self.colors.get(color, self.colors["white"]), (x, y, w, h), outline)

    def draw_dimmed_overlay(self, alpha: int = 128) -> None:
        overlay = pygame.Surface((self.width, self.height))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(alpha)
        self.surface.blit(overlay, (0, 0))
