import sys
from pathlib import Path

import pygame

# Umożliwia import "classes.*" zarówno przy uruchamianiu jako skrypt,
# jak i przy imporcie z game.py
CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.append(str(CURRENT_DIR))

from audio_manager import Level1AudioManager
from player import Level1Player
from debugHUD import Level1DebugHUD

# -----------------------------
# Stałe wspólne dla poziomu
# -----------------------------
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# Struktura:
#   Game/
#     assets/
#       sounds/
#         bit.mid
#         mexicanBit.mp3
#         click.wav   <- opcjonalny krótki „klik” na beat
#     Level_level7/
#       game_level7.py
BASE_DIR = Path(__file__).resolve().parent.parent  # folder Game/
SOUNDS_DIR = BASE_DIR / "assets" / "sounds"
BIT_MID_PATH = SOUNDS_DIR / "bit.mid"
MEXICAN_MP3_PATH = SOUNDS_DIR / "mexicanBit.mp3"


class Game:
    """
    Główna klasa poziomu:
    - scala Playera, AudioManager i HUD,
    - nie tworzy własnego okna (korzysta z przekazanego screen),
    - nie ma własnej pętli while – używasz run_frame(dt, events).
    """

    def __init__(
        self,
        screen: pygame.Surface,
        clock: pygame.time.Clock,
        level_name: str,
        player_speed: float,
        bg_color: tuple[int, int, int],
    ):
        self.screen = screen
        self.clock = clock

        self.level_name = level_name
        self.player_speed = float(player_speed)
        self.bg_color = bg_color

        # ------------------------
        # GLOBALNY KONTROLER CZASU
        # ------------------------
        self.time_scale: float = 1.0       # 1.0 = normalna prędkość gry
        self.min_time_scale: float = 0.1   # minimalne zwolnienie
        self.max_time_scale: float = 3.0   # maksymalne przyspieszenie
        self.time_scale_step: float = 0.1  # krok przy scrollu

        # --- obiekty poziomu ---
        self.player = Level1Player(
            screen_width=SCREEN_WIDTH,
            screen_height=SCREEN_HEIGHT,
            size=40,
            speed=self.player_speed,
        )

        pygame.font.init()
        debug_font = pygame.font.SysFont("consolas", 18)
        self.debug_hud = Level1DebugHUD(self.level_name, debug_font)

        # UWAGA: enable_background_mp3=False → tryb „treningowy” bez mp3,
        # tylko beat/metronom, który w 100% podlega time_scale.
        self.audio_manager = Level1AudioManager(
            fps=FPS,
            bit_mid_path=BIT_MID_PATH,
            mexican_mp3_path=MEXICAN_MP3_PATH,
            enable_background_mp3=False,
        )

        # flaga dla zewnętrznego state managera
        self.want_quit: bool = False

    def run_frame(self, dt: float, events: list[pygame.event.Event]) -> None:
        """
        Jedna klatka levelu:
        - obsługa eventów,
        - update logiki,
        - rysowanie na screen.
        """
        self._handle_events(events)
        self._update(dt)
        self._draw()

    def stop_audio(self) -> None:
        """
        Zatrzymanie audio. Wołane przy wychodzeniu z levelu.
        """
        self.audio_manager.stop()

    # ======================
    # Metody wewnętrzne
    # ======================

    def _handle_events(self, events: list[pygame.event.Event]) -> None:
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                # ESC -> prosimy state manager o wyjście z poziomu
                self.want_quit = True
                self.stop_audio()

            # Sterowanie PRĘDKOŚCIĄ CZASU gry scroll’em
            elif event.type == pygame.MOUSEWHEEL:
                if event.y > 0:
                    # scroll w górę → przyspieszenie
                    self._change_time_scale(+self.time_scale_step)
                elif event.y < 0:
                    # scroll w dół → zwolnienie
                    self._change_time_scale(-self.time_scale_step)

    def _change_time_scale(self, delta: float) -> None:
        self.time_scale += delta
        if self.time_scale < self.min_time_scale:
            self.time_scale = self.min_time_scale
        if self.time_scale > self.max_time_scale:
            self.time_scale = self.max_time_scale

        print(f"[TIME] time_scale={self.time_scale:.2f}")

    def _update(self, dt: float) -> None:
        # skalujemy dt – WSZYSTKO, co używa dt, zwalnia/przyspiesza
        scaled_dt = max(0.0, dt * self.time_scale)

        # ruch i kolizje gracza
        self.player.update(scaled_dt)

        # synchronizacja z muzyką/beatem – używamy TEGO SAMEGO scaled_dt
        self.audio_manager.update(self.player.on_beat, scaled_dt)

    def _draw(self) -> None:
        # tło tylko na obszarze 800x600
        self.screen.fill(
            self.bg_color,
            rect=pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT),
        )

        # gracz
        self.player.draw(self.screen)

        # HUD
        fps = self.clock.get_fps() if self.clock is not None else 0.0
        self.debug_hud.draw(
            self.screen,
            base_player_speed=self.player_speed,
            time_scale=self.time_scale,
            fps=fps,
        )


# -----------------------------
# Konfiguracja poziomu
# -----------------------------
level1_player_speed = 400.0
level1_bg_color = (10, 40, 90)


if __name__ == "__main__":
    """
    Standalone test levelu:
    Uruchamiasz z katalogu głównego projektu (nad folderem Game):

        python Game/Level_level7/game_level7.py
    """
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    clock = pygame.time.Clock()

    game = Game(
        screen=screen,
        clock=clock,
        level_name="level7",
        player_speed=level1_player_speed,
        bg_color=level1_bg_color,
    )

    running = True
    while running and not game.want_quit:
        dt = clock.tick(FPS) / 1000.0
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                running = False

        game.run_frame(dt, events)
        pygame.display.flip()

    game.stop_audio()
    pygame.quit()
    sys.exit()
