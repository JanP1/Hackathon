import sys
from pathlib import Path

import pygame

# -----------------------------
# Ścieżki i importy
# -----------------------------

CURRENT_DIR = Path(__file__).resolve().parent  # .../Hackathon/Level_level7
BASE_DIR = CURRENT_DIR.parent                  # .../Hackathon

# żeby działały zarówno importy lokalne (audio_manager, player, debugHUD),
# jak i objects.*
if str(CURRENT_DIR) not in sys.path:
    sys.path.append(str(CURRENT_DIR))
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

from audio_manager import Level1AudioManager
from debugHUD import Level1DebugHUD

# obiekty gry z katalogu objects/
from objects.bpm_counter import BPMCounter
from objects.ranged_enemy import RangedEnemy
from objects.player import Player

# -----------------------------
# Stałe poziomu
# -----------------------------
SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080
FPS = 60

SOUNDS_DIR = BASE_DIR / "assets" / "sounds"
BIT_MID_PATH = SOUNDS_DIR / "bit.mid"
MEXICAN_MP3_PATH = SOUNDS_DIR / "mexicanBit.mp3"


class Game:
    """
    Główna klasa poziomu:

    - interfejs kompatybilny ze starym game.py:
        Game(screen, clock, level_name, player_speed, bg_color)
        .run_frame(dt, events)
        .want_quit
        .stop_audio()
    - wewnątrz:
        * audio_manager (mp3 przez VLC, crossfade, time_scale),
        * BPMCounter oparty na bit.mid,
        * Player z objects.player,
        * RangedEnemy z objects.ranged_enemy (atak co N beatów),
        * scroll myszy steruje time_scale (czas gry + muzyka).
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
        # w tym levelu player_speed jest używany tylko do HUD (info)
        self.base_player_speed = float(player_speed)
        self.bg_color = bg_color

        # ------------------------
        # GLOBALNY KONTROLER CZASU
        # ------------------------
        self.time_scale: float = 1.0        # 1.0 = normalna prędkość
        self.min_time_scale: float = 0.1    # minimalne zwolnienie gry
        self.max_time_scale: float = 3.0    # maksymalne przyspieszenie
        self.time_scale_step: float = 0.1   # krok przy scrollu

        # ------------------------
        # AUDIO: mp3 + bit.mid
        # ------------------------
        self.audio_manager = Level1AudioManager(
            fps=FPS,
            bit_mid_path=BIT_MID_PATH,
            mexican_mp3_path=MEXICAN_MP3_PATH,
            enable_background_mp3=True,
        )
        # startowe tempo
        self.audio_manager.set_time_scale(self.time_scale)

        # ------------------------
        # HUD debugowy
        # ------------------------
        pygame.font.init()
        debug_font = pygame.font.SysFont("consolas", 18)
        self.debug_hud = Level1DebugHUD(self.level_name, debug_font)

        # ------------------------
        # OBIEKTY GRY
        # ------------------------

        # Player z katalogu objects (sterowanie WASD itd.)
        self.player = Player(
            SCREEN_WIDTH // 2,
            SCREEN_HEIGHT // 2,
            SCREEN_WIDTH,
            SCREEN_HEIGHT,
            "player",
        )

        # BPMCounter – sterowany realnymi nutami z bit.mid
        self.bpm_counter = BPMCounter(
            x_pos=SCREEN_WIDTH - 200,
            y_pos=SCREEN_HEIGHT - 50,
            SCREEN_W=SCREEN_WIDTH,
            SCREEN_H=SCREEN_HEIGHT,
            bpm=120,  # fallback (gdyby nie było midi), ale my podamy midi_note_times
            midi_note_times=self.audio_manager.midi_note_times,
        )

        # Enemies – np. jeden RangedEnemy atakujący co 4 beaty
        self.enemies: list[RangedEnemy] = []
        ranged = RangedEnemy(600, 400, SCREEN_WIDTH, SCREEN_HEIGHT)
        ranged.set_attack_cooldown(4)  # co 4 beaty
        self.enemies.append(ranged)

        # flaga do wykrywania pojedynczego triggera na beat
        self.beat_triggered: bool = False

        # flaga dla zewnętrznego state managera (ESC / wyjście z levelu)
        self.want_quit: bool = False

    # =========================================================
    # Publiczne API: jedna klatka poziomu
    # =========================================================

    def run_frame(self, dt: float, events: list[pygame.event.Event]) -> None:
        """
        Jedna klatka levelu:
        - obsługa eventów,
        - update logiki (z dt * time_scale),
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

    # =========================================================
    # Eventy / czas gry
    # =========================================================

    def _handle_events(self, events: list[pygame.event.Event]) -> None:
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                # wyjście z poziomu
                self.want_quit = True
                self.stop_audio()

            elif event.type == pygame.MOUSEWHEEL:
                # Scroll = zmiana time_scale
                if event.y > 0:
                    self._change_time_scale(+self.time_scale_step)
                elif event.y < 0:
                    self._change_time_scale(-self.time_scale_step)

    def _change_time_scale(self, delta: float) -> None:
        self.time_scale += delta
        if self.time_scale < self.min_time_scale:
            self.time_scale = self.min_time_scale
        if self.time_scale > self.max_time_scale:
            self.time_scale = self.max_time_scale

        print(f"[TIME] time_scale={self.time_scale:.2f}")
        # MP3 przez VLC – sterowanie tempem + crossfade między prędkościami
        self.audio_manager.set_time_scale(self.time_scale)

    # =========================================================
    # Update logiki
    # =========================================================

    def _update(self, dt: float) -> None:
        # Skalujemy dt – WSZYSTKO (ruch, bpm_counter, beat z MIDI) zależy od time_scale:
        if dt < 0.0:
            dt = 0.0
        scaled_dt = dt * self.time_scale  # sekundy

        # --- BPMCounter oparty na bit.mid ---
        self.bpm_counter.update(scaled_dt)

        # --- Player (z objects) ---
        # Ten Player zwykle w update() sam czyta klawiaturę, więc bez dt
        self.player.update()

        # --- Enemies ---
        # RangedEnemy.update() w Twoim przykładzie dostawał delta_time w ms,
        # więc tu konwersja scaled_dt (s) -> ms:
        delta_ms = scaled_dt * 1000.0

        for enemy in self.enemies:
            enemy.update(delta_ms)

            # target = pozycja playera
            if isinstance(enemy, RangedEnemy):
                enemy.set_target(self.player.rect.centerx, self.player.rect.centery)

        # --- Atak na beat (logika jak w Start.run z Twojego przykładu) ---
        if self.bpm_counter.is_on_beat():
            if not self.beat_triggered:
                self.beat_triggered = True
                # pojedynczy trigger na beat dla wszystkich enemies
                for enemy in self.enemies:
                    enemy.on_beat()
        else:
            self.beat_triggered = False

        # --- Audio manager ---
        # Potrzebuje scaled_dt do:
        #   - przesuwania wirtualnego czasu muzyki (bit.mid),
        #   - wyzwalania on_beat (jeśli byśmy chcieli),
        #   - obsługi crossfade'u mp3.
        #
        # Tutaj nie używamy callbacka on_beat, więc dajemy prostego lambda.
        self.audio_manager.update(lambda _note_time, _music_time: None, scaled_dt)

    # =========================================================
    # Rysowanie
    # =========================================================

    def _draw(self) -> None:
        # tło
        self.screen.fill(self.bg_color)

        # BPM counter
        self.bpm_counter.draw(self.screen)

        # player
        self.player.draw(self.screen)

        # enemies
        for enemy in self.enemies:
            enemy.draw(self.screen)

        # HUD
        fps = self.clock.get_fps() if self.clock is not None else 0.0
        self.debug_hud.draw(
            self.screen,
            base_player_speed=self.base_player_speed,
            time_scale=self.time_scale,
            fps=fps,
        )


# -----------------------------
# Standalone test levelu
# -----------------------------

level1_player_speed = 400.0
level1_bg_color = (10, 40, 90)


if __name__ == "__main__":
    """
    Standalone test poziomu:

        python Level_level7/game_level7.py
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
