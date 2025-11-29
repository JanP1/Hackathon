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

from audio_manager import Level1AudioManager
from debugHUD import Level1DebugHUD

from objects.smoke import SmokeTrail
from objects.bpm_counter import BPMCounter
from objects.ranged_enemy import RangedEnemy
from objects.player import Player
from objects.player_bullet import PlayerBullet

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
    Level 7:

    - sterowanie czasem gry time_scale scroll'em myszy (bullet-time),
    - muzyka mp3 (VLC + crossfade) + bit.mid (MIDI) spowalnia się razem z grą,
    - BPMCounter korzysta z realnego bit.mid,
    - Player z objects.player:
        * porusza się wg własnego update()
        * ma specjalny strzał prawym przyciskiem myszy:
          kulka (piłka) z dymem (SmokeTrail) leci w kierunku celowania (mysz)
    - RangedEnemy:
        * reaguje na beat (co N uderzeń),
        * po trafieniu specjalnym pociskiem:
            - generujemy chmurę dymu na przeciwniku
            - przeciwnik się „kurczy” aż do zera i znika ze sceny
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
        self.base_player_speed_param = float(player_speed)
        self.bg_color = bg_color

        # ------------------------
        # GLOBALNY KONTROLER CZASU
        # ------------------------
        self.time_scale: float = 1.0
        self.min_time_scale: float = 0.1
        self.max_time_scale: float = 3.0
        self.time_scale_step: float = 0.1

        # ------------------------
        # AUDIO: mp3 + bit.mid
        # ------------------------
        self.audio_manager = Level1AudioManager(
            fps=FPS,
            bit_mid_path=BIT_MID_PATH,
            mexican_mp3_path=MEXICAN_MP3_PATH,
            enable_background_mp3=True,
        )
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

        # Player
        self.player = Player(
            SCREEN_WIDTH // 2,
            SCREEN_HEIGHT // 2,
            SCREEN_WIDTH,
            SCREEN_HEIGHT,
            "player",
        )
        self.player_base_speed = getattr(self.player, "speed", None)

        # BPMCounter oparty na bit.mid
        self.bpm_counter = BPMCounter(
            x_pos=SCREEN_WIDTH - 200,
            y_pos=SCREEN_HEIGHT - 50,
            SCREEN_W=SCREEN_WIDTH,
            SCREEN_H=SCREEN_HEIGHT,
            bpm=120,
            midi_note_times=self.audio_manager.midi_note_times,
        )

        # Enemies – na start jeden RangedEnemy
        self.enemies: list[RangedEnemy] = []
        ranged = RangedEnemy(600, 400, SCREEN_WIDTH, SCREEN_HEIGHT)
        ranged.set_attack_cooldown(4)  # co 4 beaty
        self.enemies.append(ranged)

        # bazowe prędkości enemies (jeśli mają atrybut speed)
        self.enemy_base_speeds: dict[object, float] = {}
        for enemy in self.enemies:
            if hasattr(enemy, "speed"):
                self.enemy_base_speeds[enemy] = enemy.speed

        # pociski gracza (specjal skill – prawy przycisk myszy)
        self.player_bullets: list[PlayerBullet] = []

        # dymy eksplozji na wrogach
        self.smoke_explosions: list[SmokeTrail] = []

        # pomocnicza flaga do pojedynczego triggera beatu
        self.beat_triggered: bool = False

        # flaga dla zewnętrznego game_state_managera
        self.want_quit: bool = False

    # =========================================================
    # Publiczne API poziomu
    # =========================================================

    def run_frame(self, dt: float, events: list[pygame.event.Event]) -> None:
        self._handle_events(events)
        self._update(dt)
        self._draw()

    def stop_audio(self) -> None:
        self.audio_manager.stop()

    # =========================================================
    # Eventy / czas gry
    # =========================================================

    def _handle_events(self, events: list[pygame.event.Event]) -> None:
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.want_quit = True
                self.stop_audio()

            elif event.type == pygame.MOUSEWHEEL:
                if event.y > 0:
                    self._change_time_scale(+self.time_scale_step)
                elif event.y < 0:
                    self._change_time_scale(-self.time_scale_step)

            elif event.type == pygame.MOUSEBUTTONDOWN:
                # prawy przycisk -> strzał kulą z dymem
                if event.button == 3:
                    self._shoot_special()

    def _change_time_scale(self, delta: float) -> None:
        self.time_scale += delta
        if self.time_scale < self.min_time_scale:
            self.time_scale = self.min_time_scale
        if self.time_scale > self.max_time_scale:
            self.time_scale = self.max_time_scale

        print(f"[TIME] time_scale={self.time_scale:.2f}")
        self.audio_manager.set_time_scale(self.time_scale)
        self._apply_time_scale_to_speeds()

    def _apply_time_scale_to_speeds(self) -> None:
        # Player – jeśli ma speed
        if self.player_base_speed is not None:
            try:
                self.player.speed = self.player_base_speed * self.time_scale
            except Exception:
                pass

        # Enemies – jeśli mają speed
        for enemy, base_speed in self.enemy_base_speeds.items():
            try:
                enemy.speed = base_speed * self.time_scale
            except Exception:
                pass

    # =========================================================
    # Specjalny strzał gracza (piłka + smoke)
    # =========================================================

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

    # =========================================================
    # Update logiki
    # =========================================================

    def _update(self, dt: float) -> None:
        if dt < 0.0:
            dt = 0.0

        # bullet-time
        scaled_dt = dt * self.time_scale  # sekundy
        self._apply_time_scale_to_speeds()

        # --- BPMCounter (bit.mid) ---
        self.bpm_counter.update(scaled_dt)

        # --- Player (porusza się wg własnego update + speed zeskalowany) ---
        self.player.update()

        # --- Pociski gracza ---
        for bullet in self.player_bullets:
            bullet.update(scaled_dt)

        # kolizje pocisków z wrogami
        self._handle_bullet_enemy_collisions()

        # sprzątanie pocisków (zostawiamy te, które jeszcze mają dym)
        self.player_bullets = [
            b for b in self.player_bullets if b.alive or len(b.trail.particles) > 0
        ]

        # --- Enemies (ruch tylko jeśli nie są w fazie "umierania") ---
        delta_ms = scaled_dt * 1000.0
        for enemy in self.enemies:
            if getattr(enemy, "destroying", False):
                continue  # już "umiera", nie ruszamy AI
            enemy.update(delta_ms)

            if isinstance(enemy, RangedEnemy):
                enemy.set_target(self.player.rect.centerx, self.player.rect.centery)

        # --- Kurczenie wrogów trafionych specjalnym strzałem ---
        self._update_enemy_shrink(scaled_dt)

        # --- Beat logic (atak na beat) ---
        if self.bpm_counter.is_on_beat():
            if not self.beat_triggered:
                self.beat_triggered = True
                for enemy in self.enemies:
                    if getattr(enemy, "destroying", False):
                        continue
                    enemy.on_beat()
        else:
            self.beat_triggered = False

        # --- Audio manager (MIDI + crossfade mp3) ---
        self.audio_manager.update(lambda _note_time, _music_time: None, scaled_dt)

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

    # =========================================================
    # Rysowanie
    # =========================================================

    def _draw(self) -> None:
        self.screen.fill(self.bg_color)

        # BPM
        self.bpm_counter.draw(self.screen)

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

        # HUD
        fps = self.clock.get_fps() if self.clock is not None else 0.0
        self.debug_hud.draw(
            self.screen,
            base_player_speed=self.base_player_speed_param,
            time_scale=self.time_scale,
            fps=fps,
        )


# -----------------------------
# Standalone test
# -----------------------------

level1_player_speed = 400.0
level1_bg_color = (10, 40, 90)


if __name__ == "__main__":
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
