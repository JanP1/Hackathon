# Game/game.py

import sys
import pygame

# -----------------------------
# Stałe wspólne dla całej gry
# -----------------------------
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60


class Game:
    """
    Prosta klasa gry inspirowana systemem scen:
    - okno o stałym rozmiarze
    - prosty kwadrat jako gracz
    - poruszanie WSAD / strzałki
    - logika zamknięta w metodach:
      _handle_events, _update, _draw, run
    """

    def __init__(self, level_name: str, player_speed: float, bg_color: tuple[int, int, int]):
        """
        :param level_name: nazwa poziomu (np. 'level1', 'tutorial')
        :param player_speed: prędkość gracza w pikselach na sekundę
        :param bg_color: kolor tła (R, G, B)
        """
        pygame.init()
        pygame.display.set_caption(f"Game - {level_name}")

        self.level_name = level_name
        self.player_speed = float(player_speed)
        self.bg_color = bg_color

        # ekran i zegar
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True

        # gracz – prosty kwadrat
        self.player_size = 40
        self.player_rect = pygame.Rect(
            SCREEN_WIDTH // 2 - self.player_size // 2,
            SCREEN_HEIGHT // 2 - self.player_size // 2,
            self.player_size,
            self.player_size,
        )

        # prosty font do debug info
        pygame.font.init()
        self.debug_font = pygame.font.SysFont("consolas", 18)

    # -----------------------------
    # Główna pętla gry
    # -----------------------------
    def run(self) -> None:
        """Główna pętla gry."""
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0  # sekundy na klatkę

            self._handle_events()
            self._update(dt)
            self._draw()

            pygame.display.flip()

        pygame.quit()
        sys.exit()

    # -----------------------------
    # Obsługa zdarzeń
    # -----------------------------
    def _handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

    # -----------------------------
    # Aktualizacja stanu gry
    # -----------------------------
    def _update(self, dt: float) -> None:
        """
        :param dt: czas w sekundach od poprzedniej klatki
        """
        keys = pygame.key.get_pressed()

        dx = 0.0
        dy = 0.0

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx -= self.player_speed * dt
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx += self.player_speed * dt
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            dy -= self.player_speed * dt
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            dy += self.player_speed * dt

        # aktualizacja pozycji gracza
        self.player_rect.x += int(dx)
        self.player_rect.y += int(dy)

        # trzymanie gracza w oknie
        if self.player_rect.left < 0:
            self.player_rect.left = 0
        if self.player_rect.right > SCREEN_WIDTH:
            self.player_rect.right = SCREEN_WIDTH
        if self.player_rect.top < 0:
            self.player_rect.top = 0
        if self.player_rect.bottom > SCREEN_HEIGHT:
            self.player_rect.bottom = SCREEN_HEIGHT

    # -----------------------------
    # Rysowanie
    # -----------------------------
    def _draw(self) -> None:
        # tło poziomu
        self.screen.fill(self.bg_color)

        # gracz
        pygame.draw.rect(self.screen, (200, 50, 50), self.player_rect)

        # prosty overlay z nazwą poziomu i parametrami
        debug_text = f"Level: {self.level_name} | speed: {self.player_speed:.1f} px/s | FPS: {self.clock.get_fps():.1f}"
        text_surface = self.debug_font.render(debug_text, True, (255, 255, 255))
        self.screen.blit(text_surface, (10, 10))


# -----------------------------
# Przykładowa konfiguracja "demo"
# -----------------------------
# Zmienna jest związana z poziomem "demo",
# dlatego trzyma się konwencji:
#   [nazwa_poziomu]_[nazwa_zmiennej]
demo_player_speed = 300.0
demo_bg_color = (30, 30, 30)


if __name__ == "__main__":
    # Uruchomienie "głównego" game.py z domyślną konfiguracją demo
    game = Game(
        level_name="demo",
        player_speed=demo_player_speed,
        bg_color=demo_bg_color,
    )
    game.run()
