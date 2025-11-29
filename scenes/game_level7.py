# Level_level7/game_level1.py

import sys
import math
import random
from pathlib import Path

import pygame

# -----------------------------
# Ścieżki i importy
# -----------------------------

CURRENT_DIR = Path(__file__).resolve().parent  # .../Hackathon/Level_level7
BASE_DIR = CURRENT_DIR.parent                  # .../Hackathon

if str(CURRENT_DIR) not in sys.path:
    sys.path.append(str(CURRENT_DIR))
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

from base_level import BaseLevel

from objects.effects_manager import EffectsManager  # używany w BaseLevel, import zostawiony
from objects.smoke import SmokeTrail
from objects.bpm_counter import BPMCounter  # używany w BaseLevel
from objects.ranged_enemy import RangedEnemy
from objects.player_bullet import PlayerBullet

from objects.audio_manager import Level1AudioManager  # już używany w BaseLevel
from objects.debugHUD import Level1DebugHUD          # jw.

# -----------------------------
# Stałe poziomu
# -----------------------------
SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080
FPS = 60

SOUNDS_DIR = BASE_DIR / "assets" / "sounds"
BIT_MID_PATH = SOUNDS_DIR / "bit.mid"
MEXICAN_MP3_PATH = SOUNDS_DIR / "mexicanBit.mp3"

PICTURES_DIR = BASE_DIR / "assets" / "pictures"
MAIN_BG_PATH = PICTURES_DIR / "main_background.png"


class Game(BaseLevel):
    """
    Level 7:

    - dziedziczy po BaseLevel wszystkie wspólne systemy:
        * time_scale (scroll),
        * audio (Level1AudioManager + MIDI),
        * BPMCounter,
        * EffectsManager (waves/bullets),
        * Player z time_scale + effects_manager,
        * wspólny on_beat() dla wrogów,
        * Debug HUD.
    - specyficzne dla level7:
        * tło z obrazka,
        * specjalny strzał (prawy przycisk myszy) – piłka z dymem,
        * kurczenie wrogów po trafieniu + chmura dymu,
        * integracja z GLPostProcessor (dane z EffectsManagera).
    """

    def __init__(
        self,
        screen: pygame.Surface,
        clock: pygame.time.Clock,
        level_name: str,
        player_speed: float,
        bg_color: tuple[int, int, int],
    ):
        # inicjalizacja części wspólnej (BaseLevel)
        super().__init__(
            screen=screen,
            clock=clock,
            level_name=level_name,
            player_speed=player_speed,
            bg_color=bg_color,
            bpm=120,
            bit_mid_path=BIT_MID_PATH,
            mexican_mp3_path=MEXICAN_MP3_PATH,
            enable_background_mp3=True,
        )

        # ------------------------
        # TŁO – obraz zamiast jednolitego koloru
        # ------------------------
        self.background_image: pygame.Surface | None = None
        try:
            img = pygame.image.load(str(MAIN_BG_PATH)).convert()
            self.background_image = pygame.transform.scale(
                img, (SCREEN_WIDTH, SCREEN_HEIGHT)
            )
            print(f"[BG] Załadowano tło: {MAIN_BG_PATH}")
        except Exception as e:
            print(f"[BG][WARN] Nie udało się załadować {MAIN_BG_PATH}: {e}")
            self.background_image = None

        # ------------------------
        # SPECYFICZNE DLA LEVEL7
        # ------------------------

        # jeden RangedEnemy na start
        ranged = RangedEnemy(600, 400, SCREEN_WIDTH, SCREEN_HEIGHT)
        ranged.set_attack_cooldown(4)  # co 4 beaty
        self.add_enemy(ranged)         # ustawia mu time_scale + effects_manager

        # pociski gracza (specjal skill – prawy przycisk myszy)
        self.player_bullets: list[PlayerBullet] = []

        # dymy eksplozji na wrogach
        self.smoke_explosions: list[SmokeTrail] = []

    # ======================================================================
    # EVENTY SPECYFICZNE DLA LEVEL7
    # ======================================================================

    def handle_event_level(self, event: pygame.event.Event) -> None:
        """
        Tu reagujemy na eventy specyficzne dla tego poziomu.
        Wspólne rzeczy (ESC, scroll) są w BaseLevel.handle_events().
        """
        if event.type == pygame.MOUSEBUTTONDOWN:
            # prawy przycisk -> strzał kulą z dymem
            if event.button == 3:
                self._shoot_special()

    # ======================================================================
    # SPECJALNY STRZAŁ GRACZA (piłka + smoke)
    # ======================================================================

    def _shoot_special(self) -> None:
        # pozycja gracza
        px, py = self.player.rect.center

        # kierunek = celowanie w pozycję myszy
        mx, my = pygame.mouse.get_pos()
        dx = mx - px
        dy = my - py
        length = math.hypot(dx, dy)
        if length == 0:
            return

        dir_x = dx / length
        dir_y = dy / length

        # prędkość bazowa pocisku (px/s)
        bullet_speed = 900.0

        bullet = PlayerBullet(
            x=px,
            y=py,
            vx=dir_x * bullet_speed,
            vy=dir_y * bullet_speed,
        )
        self.player_bullets.append(bullet)

        # Rejestrujemy pocisk w EffectsManagerze (do shadera)
        self.effects_manager.add_bullet(bullet)

    # ======================================================================
    # UPDATE LOGIKI SPECYFICZNEJ DLA LEVEL7
    # ======================================================================

    def update_level(self, scaled_dt: float, raw_dt: float) -> None:
        """
        scaled_dt – sekundy * time_scale,
        raw_dt    – sekundy bez time_scale.
        BaseLevel zrobił już:
        - effects_manager.update(),
        - _apply_time_scale_to_objects(),
        - bpm_counter.update(),
        - audio_manager.update(),
        - player.update(),
        - enemies.update() + target na gracza,
        - wspólny on_beat() dla enemies.
        Tu dokładamy:
        - ruch pocisków,
        - kolizje z wrogami,
        - kurczenie wrogów po trafieniu,
        - dymy eksplozji.
        """
        # --- Pociski gracza ---
        for bullet in self.player_bullets:
            bullet.update(scaled_dt)

        # kolizje pocisków z wrogami
        self._handle_bullet_enemy_collisions()

        # sprzątanie pocisków – zostawiamy tylko żywe
        self.player_bullets = [b for b in self.player_bullets if b.alive]
        # UWAGA: EffectsManager sam filtruje martwe pociski w get_bullets_data()

        # --- Kurczenie wrogów trafionych specjalnym strzałem ---
        self._update_enemy_shrink(scaled_dt)

        # --- Dymy eksplozji na wrogach ---
        for trail in self.smoke_explosions:
            trail.update()
        self.smoke_explosions = [
            t for t in self.smoke_explosions if len(t.particles) > 0
        ]

    def _handle_bullet_enemy_collisions(self) -> None:
        enemies_hit = set()

        for bullet in self.player_bullets:
            if not bullet.alive:
                continue
            b_rect = bullet.get_rect()

            for enemy in self.enemies:
                if getattr(enemy, "destroying", False):
                    continue
                if not hasattr(enemy, "rect"):
                    continue

                if b_rect.colliderect(enemy.rect):
                    bullet.alive = False
                    enemies_hit.add(enemy)
                    break

        for enemy in enemies_hit:
            self._hit_enemy_with_special(enemy)

    def _hit_enemy_with_special(self, enemy) -> None:
        """
        Trafienie wroga specjalnym pociskiem:
        - odpalamy na nim dym (SmokeTrail)
        - zaczynamy animację kurczenia do zera.
        """
        if getattr(enemy, "destroying", False):
            return

        enemy.destroying = True
        enemy.destroy_scale = 1.0
        enemy.original_rect = enemy.rect.copy()

        ex, ey = enemy.rect.center

        # duża chmura smoke przy trafieniu
        explosion = SmokeTrail(border=1)
        for _ in range(80):
            dx = random.uniform(-1.0, 1.0)
            dy = random.uniform(-1.0, 1.0)
            explosion.add_particle(ex, ey, dx, dy)
        self.smoke_explosions.append(explosion)

    def _update_enemy_shrink(self, scaled_dt: float) -> None:
        """
        Powolne kurczenie wrogów po trafieniu. Gdy rozmiar spadnie do zera – usuwamy.
        """
        to_remove = []

        for enemy in self.enemies:
            if not getattr(enemy, "destroying", False):
                continue

            # inicjalizacja oryginalnego rect, gdyby nie było
            orig = getattr(enemy, "original_rect", enemy.rect)

            # zmniejszamy skalę
            scale_speed = 1.5  # ile "skali" na sekundę
            enemy.destroy_scale -= scale_speed * scaled_dt

            if enemy.destroy_scale <= 0.0:
                to_remove.append(enemy)
                continue

            # przeskalowany rect wokół środka
            cx, cy = orig.center
            new_w = max(1, int(orig.width * enemy.destroy_scale))
            new_h = max(1, int(orig.height * enemy.destroy_scale))

            enemy.rect = pygame.Rect(0, 0, new_w, new_h)
            enemy.rect.center = (cx, cy)

        if to_remove:
            self.enemies = [e for e in self.enemies if e not in to_remove]

    # ======================================================================
    # RYSOWANIE SPECYFICZNE DLA LEVEL7
    # ======================================================================

    def draw_level(self) -> None:
        """
        BaseLevel.draw() dorysuje BPM + HUD.
        Tu rysujemy wszystko co „wizualne” dla poziomu.
        Kolejność jak w oryginalnym level7 (prawie 1:1).
        """
        # tło: najpierw obrazek, jak nie ma to kolor
        if self.background_image is not None:
            self.screen.blit(self.background_image, (0, 0))
        else:
            self.screen.fill(self.bg_color)

        # pociski (w tym ich dym)
        for bullet in self.player_bullets:
            bullet.draw(self.screen)

        # wrogowie (część może być w fazie kurczenia – rect już zmniejszony)
        for enemy in self.enemies:
            enemy.draw(self.screen)

        # dymy eksplozji na wrogach
        for trail in self.smoke_explosions:
            trail.draw(self.screen)

        # gracz
        self.player.draw(self.screen)


# -----------------------------
# Standalone test – z postprocess GL
# -----------------------------

level7_player_speed = 400.0
level7_bg_color = (10, 40, 90)


if __name__ == "__main__":
    pygame.init()
    pygame.display.set_caption("Level 7 - GL postprocess")

    # okno z kontekstem OpenGL
    screen = pygame.display.set_mode(
        (SCREEN_WIDTH, SCREEN_HEIGHT),
        pygame.OPENGL | pygame.DOUBLEBUF,
    )

    clock = pygame.time.Clock()

    # offscreen surface, na którym rysuje cała gra
    game_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT)).convert()

    # postprocess GL
    from gl_postprocess import GLPostProcessor

    gl_post = GLPostProcessor(SCREEN_WIDTH, SCREEN_HEIGHT)

    # UWAGA: do Game (BaseLevel) przekazujemy game_surface jako "screen"
    game = Game(
        screen=game_surface,
        clock=clock,
        level_name="level7",
        player_speed=level7_player_speed,
        bg_color=level7_bg_color,
    )

    running = True
    while running and not game.want_quit:
        dt = clock.tick(FPS) / 1000.0
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                running = False

        # logika + rysowanie NA game_surface (CPU)
        game.run_frame(dt, events)

        # Dane dla shadera bierzemy teraz wyłącznie z EffectsManagera
        bullets_data = game.effects_manager.get_bullets_data()
        waves_data = game.effects_manager.get_waves_data()

        # Przekazujemy też aktualny czas do shadera, aby mógł animować fale
        current_time_ms = pygame.time.get_ticks()

        gl_post.render(game_surface, bullets_data, waves_data, current_time_ms)

        pygame.display.flip()

    game.stop_audio()
    pygame.quit()
    sys.exit()
