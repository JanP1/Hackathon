# objects/beat_hit_popup.py

import pygame
import math


class BeatHitPopup:
    """
    Prosty wyskakujący napis (np. PERFECT!) nad metronomem:
    - znika po krótkim czasie,
    - lekko się unosi,
    - płynnie zanika (alpha).
    """

    _font = None

    def __init__(
        self,
        text: str,
        x: int,
        y: int,
        color: tuple[int, int, int] = (255, 255, 255),
        lifetime_sec: float = 0.8,
        rise_speed: float = 60.0,
    ) -> None:
        if BeatHitPopup._font is None:
            pygame.font.init()
            # dość duży, wyraźny font
            BeatHitPopup._font = pygame.font.SysFont("consolas", 32, bold=True)

        self.text = text
        self.x = float(x)
        self.y = float(y)
        self.color = color

        self.lifetime_sec = float(lifetime_sec)
        self.rise_speed = float(rise_speed)

        self.age_sec = 0.0
        self.alive = True

    def update(self, dt_sec: float) -> None:
        """Aktualizacja wieku i pozycji napisu."""
        if not self.alive:
            return

        if dt_sec < 0.0:
            dt_sec = 0.0

        self.age_sec += dt_sec
        # lekko do góry
        self.y -= self.rise_speed * dt_sec

        if self.age_sec >= self.lifetime_sec:
            self.alive = False

    def draw(self, screen: pygame.Surface) -> None:
        """Rysuje napis z przezroczystością zależną od czasu."""
        if not self.alive:
            return

        font = BeatHitPopup._font
        t = max(0.0, min(1.0, self.age_sec / self.lifetime_sec))

        # Alpha od 255 -> 0
        alpha = int(255 * (1.0 - t))

        # Delikatne powiększenie na początku
        scale = 1.0 + 0.2 * math.sin(t * math.pi)

        base_surf = font.render(self.text, True, self.color)
        w, h = base_surf.get_size()
        scaled_surf = pygame.transform.smoothscale(
            base_surf,
            (int(w * scale), int(h * scale)),
        )

        # kanał alpha
        scaled_surf = scaled_surf.convert_alpha()
        scaled_surf.set_alpha(alpha)

        rect = scaled_surf.get_rect
