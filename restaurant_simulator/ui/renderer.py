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
        self.font_tiny = pygame.font.SysFont("monospace", 12)
        self.colors = {
            "green": (50, 205, 50),
            "red": (255, 69, 69),
            "yellow": (255, 215, 0),
            "cyan": (0, 255, 255),
            "magenta": (255, 105, 180),
            "white": (255, 255, 255),
            "dim": (150, 150, 150),
            "bar_bg": (60, 60, 60),
            "panel": (40, 40, 60),
            "blue": (70, 130, 255),
        }

    def clear(self) -> None:
        self.surface.fill(BG_COLOR)

    def draw_text(self, text: str, x: int, y: int, color: str = "white", font: str = "normal") -> None:
        f = self.font_bold if font == "bold" else self.font_large if font == "large" else self.font_small if font == "small" else self.font_tiny if font == "tiny" else self.font
        surf = f.render(str(text), True, self.colors.get(color, self.colors["white"]))
        self.surface.blit(surf, (x, y))

    def draw_text_centered(self, text: str, y: int, color: str = "white", font: str = "normal") -> int:
        f = self.font_bold if font == "bold" else self.font_large if font == "large" else self.font_small if font == "small" else self.font
        surf = f.render(str(text), True, self.colors.get(color, self.colors["white"]))
        x = (self.width - surf.get_width()) // 2
        self.surface.blit(surf, (x, y))
        return surf.get_width()

    def text_width(self, text: str, font: str = "normal") -> int:
        f = self.font_bold if font == "bold" else self.font_large if font == "large" else self.font_small if font == "small" else self.font
        return f.render(str(text), True, self.colors["white"]).get_width()

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

    def draw_table_sprite(self, x: int, y: int, state: str, busy_pct: float, guest_label: str = "") -> None:
        if state == "free":
            color = self.colors["dim"]
            label = "Free"
        else:
            color = self.colors["green"]
            label = guest_label
        pygame.draw.rect(self.surface, self.colors["panel"], (x, y, 80, 50), 0, 4)
        pygame.draw.rect(self.surface, color, (x, y, 80, 50), 2, 4)
        self.draw_text(label, x + 5, y + 5, "white", "tiny")
        if state == "occupied":
            prog_width = int(76 * busy_pct)
            prog_color = self.colors["green"] if busy_pct > 0.5 else self.colors["yellow"] if busy_pct > 0.25 else self.colors["red"]
            pygame.draw.rect(self.surface, prog_color, (x + 2, y + 38, prog_width, 4))

    def draw_staff_card(self, x: int, y: int, staff, width: int = 180) -> None:
        pygame.draw.rect(self.surface, self.colors["panel"], (x, y, width, 50), 0, 4)
        status_colors = {"ready": "green", "busy": "yellow", "resting": "blue"}
        sc = status_colors.get(staff.status, "red")
        pygame.draw.rect(self.surface, self.colors[sc], (x, y, 4, 50), 0, 4, 0, 0, 4, 0)
        self.draw_text(f"Sk={staff.skill} {staff.status.upper()}", x + 10, y + 3, "white", "tiny")
        self.draw_progress_bar(x + 10, y + 22, staff.stamina, staff.max_stamina, width - 20, 8)
        self.draw_text(f"${staff.daily_salary}/d", x + 10, y + 35, "dim", "tiny")

    def draw_phase_indicator(self, phase: int) -> None:
        names = {1: "Timers", 2: "Spawn", 3: "Assign", 4: "Serve", 5: "Rest", 6: "End"}
        self.draw_text(f"Phase: {names.get(phase, '?')}", self.width - 120, self.height - 18, "dim", "tiny")
