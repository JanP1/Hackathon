import math
import pygame

from objects.smoke import SmokeTrail  # korzystamy z Twojego smoke.py


class PlayerBullet:
    """
    Pocisk gracza:
    - leci w zadanym kierunku z prędkością vx, vy (px/s)
    - generuje dym (SmokeTrail) za sobą
    - ma prostą kolizję jako okrąg (get_rect())
    """

    def __init__(
        self,
        x: float,
        y: float,
        vx: float,
        vy: float,
        radius: int = 14,
        color: tuple[int, int, int] = (255, 255, 255),
    ) -> None:
        self.x = float(x)
        self.y = float(y)
        self.vx = float(vx)
        self.vy = float(vy)
        self.radius = radius
        self.color = color

        # żyje / martwy (po trafieniu lub końcu życia)
        self.alive: bool = True

        # ile sekund może lecieć maksymalnie
        self.max_lifetime: float = 2.5
        self.age: float = 0.0

        # ślad dymu za pociskiem
        self.trail = SmokeTrail(border=0)

    def update(self, dt: float) -> None:
        """
        dt – czas w sekundach (już zeskalowany time_scale z gry).
        """
        # nawet jak pocisk już "nie żyje", chcemy jeszcze wygasić dym
        self.trail.update()

        if not self.alive:
            return

        self.age += dt

        # ruch
        self.x += self.vx * dt
        self.y += self.vy * dt

        # dym – kierunek przeciwny do ruchu (albo ten sam, SmokeTrail i tak normalizuje)
        self.trail.add_particle(self.x, self.y, self.vx, self.vy)

        # limit życia
        if self.age > self.max_lifetime:
            self.alive = False

    def draw(self, surface: pygame.Surface) -> None:
        # najpierw rysujemy dym (distortion)
        self.trail.draw(surface)

        # samą kulkę tylko jeśli jeszcze "żyje"
        if not self.alive:
            return

        pygame.draw.circle(
            surface,
            self.color,
            (int(self.x), int(self.y)),
            self.radius,
        )

    def get_rect(self) -> pygame.Rect:
        """
        Prostokąt kolizji pocisku (okrąg wpisany w rect).
        """
        return pygame.Rect(
            int(self.x - self.radius),
            int(self.y - self.radius),
            self.radius * 2,
            self.radius * 2,
        )
