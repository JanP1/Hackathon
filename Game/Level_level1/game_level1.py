# Game/Level_level1/game_level1.py

import sys
import pygame

# -----------------------------
# Stałe wspólne dla całej gry
# (skopiowane z game.py)
# -----------------------------
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60


class Game:
    """
    Kopia klasy z Game/game.py – ale pracujemy na niej
    na osobnym branchu dla poziomu 'level1'.

    Możesz tu dopisywać logikę tylko dla tego poziomu,
    zmieniać zachowanie _update, _draw itd.,
    bez ruszania głównego game.py.
    """

    def __init__(self, level_name: str, player_speed: float, bg_color: tuple[int, int, int]):
        pygame.init()
        pygame.display.set_caption(f"Game - {level_name}")

        self.level_name = level_name
        self.player_speed = float(player_speed)
        self.bg_color = bg_color

        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True

        self.player_size = 40
        self.player_rect = pygame.Rect(
            SCREEN_WIDTH // 2 - self.player_size // 2,
            SCREEN_HEIGHT // 2 - self.player_size // 2,
            self.player_size,
            self.player_size,
        )

        pygame.font.init()
        self.debug_font = pygame.font.SysFont("consolas", 18)

    def run(self) -> None:
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0

            self._handle_events()
            self._update(dt)
            self._draw()

            pygame.display.flip()

        pygame.quit()
        sys.exit()

    def _handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            # PRZYKŁAD: dodatkowy skrót tylko w level1
            # np. ESC kończy poziom
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.running = False

    def _update(self, dt: float) -> None:
        keys = pygame.key.get_pressed()

        # Najpierw zbieramy "kierunek" (-1, 0, 1) na osiach
        raw_dx = 0.0
        raw_dy = 0.0

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            raw_dx -= 1.0
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            raw_dx += 1.0
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            raw_dy -= 1.0
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            raw_dy += 1.0

        # Normalizacja wektora ruchu (żeby po skosie nie był szybszy)
        length = (raw_dx * raw_dx + raw_dy * raw_dy) ** 0.5

        if length > 0.0:
            norm_dx = raw_dx / length
            norm_dy = raw_dy / length

            dx = norm_dx * self.player_speed * dt
            dy = norm_dy * self.player_speed * dt
        else:
            dx = 0.0
            dy = 0.0

        # Aktualizacja pozycji – zaokrąglamy do inta przy wpisie do recta
        self.player_rect.x += int(round(dx))
        self.player_rect.y += int(round(dy))

        # Ograniczenie ruchu do ekranu
        if self.player_rect.left < 0:
            self.player_rect.left = 0
        if self.player_rect.right > SCREEN_WIDTH:
            self.player_rect.right = SCREEN_WIDTH
        if self.player_rect.top < 0:
            self.player_rect.top = 0
        if self.player_rect.bottom > SCREEN_HEIGHT:
            self.player_rect.bottom = SCREEN_HEIGHT

    def _draw(self) -> None:
        # tutaj możesz robić rysowanie tylko dla level1
        self.screen.fill(self.bg_color)

        # gracz
        pygame.draw.rect(self.screen, (50, 200, 50), self.player_rect)

        # np. inny overlay, specyficzny dla level1
        debug_text = (
            f"Level: {self.level_name} | "
            f"speed: {self.player_speed:.1f} px/s | "
            f"FPS: {self.clock.get_fps():.1f}"
        )
        text_surface = self.debug_font.render(debug_text, True, (255, 255, 255))
        self.screen.blit(text_surface, (10, 10))


# -----------------------------
# Zmienne globalne powiązane z level1
# -----------------------------
level1_player_speed = 400.0          # szybciej niż w demo
level1_bg_color = (10, 40, 90)       # inne tło, np. "nocny" klimat


if __name__ == "__main__":
    """
    Uruchamiasz z katalogu głównego projektu (nad folderem Game):

        python Game/Level_level1/game_level1.py

    Ten plik używa swojej kopii klasy Game oraz swoich
    zmiennych globalnych level1_*.
    """
    game = Game(
        level_name="level1",
        player_speed=level1_player_speed,
        bg_color=level1_bg_color,
    )
    game.run()
