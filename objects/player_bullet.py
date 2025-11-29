# objects/player_bullet.py

import pygame


class PlayerBullet:
    """
    Pocisk gracza:
    - leci w zadanym kierunku z prędkością vx, vy (px/s)
    - kolizja jako okrąg (get_rect)
    - zniekształcenie obrazu robi shader/efekt trójkąta (może brać
      trail_length / trail_half_width z tego obiektu).
    """

    def __init__(
        self,
        x: float,
        y: float,
        vx: float,
        vy: float,
        radius: int = 14,
        color: tuple[int, int, int] = (255, 255, 255),
        trail_length: float | None = None,
        trail_half_width: float | None = None,
    ) -> None:
        self.x = float(x)
        self.y = float(y)
        self.vx = float(vx)
        self.vy = float(vy)
        self.radius = int(radius)
        self.color = color

        # żyje / martwy (po trafieniu lub końcu życia)
        self.alive: bool = True

        # ile sekund może lecieć maksymalnie
        self.max_lifetime: float = 2.5
        self.age: float = 0.0

        # =====================================================
        # PARAMETRY TRÓJKĄTA ZA POCISKIEM (DLA GRACZA – SZEROKO)
        # =====================================================
        # Domyślnie: trochę dłuższy i szerszy niż u wroga
        if trail_length is None:
            # np. ~14 * 14 = 196 px
            self.trail_length = float(self.radius) * 14.0
        else:
            self.trail_length = float(trail_length)

        if trail_half_width is None:
            # np. ~14 * 2.2 = 30.8 px
            self.trail_half_width = float(self.radius) * 2.2
        else:
            self.trail_half_width = float(trail_half_width)

    def update(self, dt: float) -> None:
        """
        dt – czas w sekundach (już zeskalowany time_scale z gry).
        """
        if not self.alive:
            return

        self.age += dt

        # ruch
        self.x += self.vx * dt
        self.y += self.vy * dt

        # limit życia
        if self.age > self.max_lifetime:
            self.alive = False

    def draw(self, surface: pygame.Surface) -> None:
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
