# base_level.py

import math
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, List

import pygame

from objects.audio_manager import Level1AudioManager
from objects.debugHUD import Level1DebugHUD
from objects.effects_manager import EffectsManager
from objects.player import Player
from objects.bpm_counter import BPMCounter
from objects.ranged_enemy import RangedEnemy
from objects.camera import Camera
from objects.beat_hit_popup import BeatHitPopup   # <-- NOWY IMPORT


class BaseLevel(ABC):
    """
    Bazowa klasa poziomu.
    """

    def __init__(
        self,
        screen: pygame.Surface,
        clock: pygame.time.Clock,
        level_name: str,
        player_speed: float,
        bg_color: tuple[int, int, int],
        bpm: int = 120,
        bit_mid_path: Optional[Path] = None,
        mexican_mp3_path: Optional[Path] = None,
        enable_background_mp3: bool = True,
        game_state_manager=None,
    ) -> None:
        # podstawowe referencje
        self.screen = screen
        self.clock = clock
        self.game_state_manager = game_state_manager

        self.level_name = level_name
        self.bg_color = bg_color
        self.base_player_speed_param = float(player_speed)

        self.WIDTH = self.screen.get_width()
        self.HEIGHT = self.screen.get_height()

        # ------------------------------------------------------------------
        # TIME SCALE (bullet-time)
        # ------------------------------------------------------------------
        self.time_scale: float = 1.0
        self.min_time_scale: float = 0.1
        self.max_time_scale: float = 3.0
        self.time_scale_step: float = 0.1

        # ------------------------------------------------------------------
        # AUDIO: Level1AudioManager (mp3 + MIDI)
        # ------------------------------------------------------------------
        self.audio_manager: Optional[Level1AudioManager] = None
        if bit_mid_path is not None and mexican_mp3_path is not None:
            self.audio_manager = Level1AudioManager(
                fps=60,
                bit_mid_path=bit_mid_path,
                mexican_mp3_path=mexican_mp3_path,
                enable_background_mp3=enable_background_mp3,
            )
            self.audio_manager.set_time_scale(self.time_scale)

        # ------------------------------------------------------------------
        # HUD debugowy
        # ------------------------------------------------------------------
        pygame.font.init()
        debug_font = pygame.font.SysFont("consolas", 18)
        self.debug_hud = Level1DebugHUD(self.level_name, debug_font)

        # ------------------------------------------------------------------
        # EffectsManager – waves / bullets do shadera
        # ------------------------------------------------------------------
        self.effects_manager = EffectsManager()

        # ------------------------------------------------------------------
        # Player
        # ------------------------------------------------------------------
        self.player = Player(
            self.WIDTH // 2,
            self.HEIGHT // 2,
            self.WIDTH,
            self.HEIGHT,
            1.0,
            "player",
        )
        if hasattr(self.player, "set_effects_manager"):
            self.player.set_effects_manager(self.effects_manager)
        if hasattr(self.player, "set_time_scale"):
            self.player.set_time_scale(self.time_scale)

        # ------------------------------------------------------------------
        # CAMERA
        # ------------------------------------------------------------------
        self.camera: Optional[Camera] = Camera(
            self.WIDTH,
            self.HEIGHT,
            self.WIDTH,
            self.HEIGHT,
            box_w=int(self.WIDTH * 0.8),
            box_h=int(self.HEIGHT * 0.8),
        )
        self.player.camera = self.camera  # type: ignore

        # ------------------------------------------------------------------
        # BPMCounter
        # ------------------------------------------------------------------
        midi_times = (
            self.audio_manager.midi_note_times
            if self.audio_manager is not None
            else None
        )
        self.bpm_counter = BPMCounter(
            x_pos=self.WIDTH - 200,
            y_pos=self.HEIGHT - 50,
            SCREEN_W=self.WIDTH,
            SCREEN_H=self.HEIGHT,
            bpm=bpm,
            midi_note_times=midi_times,
        )

        self.beat_triggered: bool = False

        # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
        # Wstrzyknięcie on-beat checkera do playera
        # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
        if hasattr(self.player, "set_on_beat_checker") and self.bpm_counter is not None:
            try:
                self.player.set_on_beat_checker(self.bpm_counter.is_on_beat)
            except Exception as e:
                print(f"[BPM] Warning: could not inject on_beat_checker into player: {e}")

        # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
        # Wstrzyknięcie callbacka PERFECT! do playera
        # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
        if hasattr(self.player, "set_perfect_hit_callback"):
            try:
                self.player.set_perfect_hit_callback(self.on_player_perfect_hit)
            except Exception as e:
                print(f"[BPM] Warning: could not inject perfect_hit_callback into player: {e}")

        # ------------------------------------------------------------------
        # Enemies
        # ------------------------------------------------------------------
        self.enemies: List[RangedEnemy] = []

        # ------------------------------------------------------------------
        # Pop-upy PERFECT! itd.
        # ------------------------------------------------------------------
        self.hit_popups: list[BeatHitPopup] = []

        # flaga wyjścia
        self.want_quit: bool = False

    # ======================================================================
    # PUBLICZNE API
    # ======================================================================

    def run_frame(self, dt: float, events: list[pygame.event.Event]) -> None:
        self.handle_events(events)
        self.update(dt)
        self.draw()

    def stop_audio(self) -> None:
        if self.audio_manager is not None:
            self.audio_manager.stop()

    # ======================================================================
    # KAMERA – API dla leveli
    # ======================================================================

    def set_map_size(self, map_width: int, map_height: int) -> None:
        if map_width <= 0 or map_height <= 0:
            return

        if self.camera is None:
            self.camera = Camera(
                map_width,
                map_height,
                self.WIDTH,
                self.HEIGHT,
                box_w=int(self.WIDTH * 0.8),
                box_h=int(self.HEIGHT * 0.8),
            )
        else:
            self.camera.map_width = map_width
            self.camera.map_height = map_height

        if hasattr(self.player, "set_map_size"):
            self.player.set_map_size(map_width, map_height)

        self.player.camera = self.camera  # type: ignore

        if hasattr(self.effects_manager, "set_camera"):
            self.effects_manager.set_camera(self.camera)

    def get_camera(self) -> Optional[Camera]:
        return self.camera

    # ======================================================================
    # EVENTY
    # ======================================================================

    def handle_events(self, events: list[pygame.event.Event]) -> None:
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.on_escape_pressed()
            elif event.type == pygame.MOUSEWHEEL:
                if event.y > 0:
                    self._change_time_scale(+self.time_scale_step)
                elif event.y < 0:
                    self._change_time_scale(-self.time_scale_step)

            self.handle_event_level(event)

    def on_escape_pressed(self) -> None:
        self.want_quit = True
        self.stop_audio()
        if self.game_state_manager is not None:
            pass

    def _change_time_scale(self, delta: float) -> None:
        self.time_scale += delta
        if self.time_scale < self.min_time_scale:
            self.time_scale = self.min_time_scale
        if self.time_scale > self.max_time_scale:
            self.time_scale = self.max_time_scale

        print(f"[TIME] time_scale={self.time_scale:.2f}")

        if self.audio_manager is not None:
            self.audio_manager.set_time_scale(self.time_scale)

        self._apply_time_scale_to_objects()

    def _apply_time_scale_to_objects(self) -> None:
        if hasattr(self.player, "set_time_scale"):
            self.player.set_time_scale(self.time_scale)

        for enemy in self.enemies:
            if hasattr(enemy, "set_time_scale"):
                enemy.set_time_scale(self.time_scale)

    # ======================================================================
    # PERFECT! callback z playera
    # ======================================================================

    def on_player_perfect_hit(self) -> None:
        """
        Wywoływane przez gracza, gdy klik LPM trafi idealnie w beat.
        Tworzymy napis PERFECT! nad metronomem.
        """
        if self.bpm_counter is None:
            return

        # Bierzemy pivot metronomu i rysujemy trochę powyżej
        pivot_x = self.bpm_counter.rect.x
        pivot_y = self.bpm_counter.rect.y

        # Lekko nad metronomem (możesz dostroić offset)
        text_x = pivot_x
        text_y = pivot_y - 260

        popup = BeatHitPopup(
            text="PERFECT!",
            x=text_x,
            y=text_y,
            color=(255, 255, 0),
            lifetime_sec=0.8,
            rise_speed=40.0,
        )
        self.hit_popups.append(popup)

    # ======================================================================
    # UPDATE (wspólny + hooki poziomu)
    # ======================================================================

    def update(self, dt: float) -> None:
        if dt < 0.0:
            dt = 0.0

        scaled_dt = dt * self.time_scale

        self.effects_manager.update()
        self._apply_time_scale_to_objects()

        if self.bpm_counter is not None:
            self.bpm_counter.update(scaled_dt)

        if self.audio_manager is not None:
            self.audio_manager.update(
                lambda _note_time, _music_time: None,
                scaled_dt,
            )

        self.player.update()

        if self.camera is not None:
            self.camera.update(self.player)

        delta_ms = dt * 1000.0
        for enemy in self.enemies:
            if getattr(enemy, "destroying", False):
                continue
            if hasattr(enemy, "update"):
                enemy.update(delta_ms)
            if isinstance(enemy, RangedEnemy):
                enemy.set_target()

        if self.bpm_counter is not None and self.bpm_counter.is_on_beat():
            if not self.beat_triggered:
                self.beat_triggered = True
                self._on_beat_common()
                self.on_beat()
        else:
            self.beat_triggered = False

        # UPDATE popupów PERFECT!
        if self.hit_popups:
            for popup in self.hit_popups:
                popup.update(scaled_dt)
            self.hit_popups = [p for p in self.hit_popups if p.alive]

        self.update_level(scaled_dt, dt)

    def _on_beat_common(self) -> None:
        for enemy in self.enemies:
            if getattr(enemy, "destroying", False):
                continue
            if hasattr(enemy, "on_beat"):
                enemy.on_beat()

    # ======================================================================
    # DRAW
    # ======================================================================

    def draw(self) -> None:
        self.draw_level()

        if self.bpm_counter is not None:
            self.bpm_counter.draw(self.screen)

        # Rysujemy popupy nad metronomem
        for popup in self.hit_popups:
            popup.draw(self.screen)

        fps = self.clock.get_fps() if self.clock is not None else 0.0
        self.debug_hud.draw(
            self.screen,
            base_player_speed=self.base_player_speed_param,
            time_scale=self.time_scale,
            fps=fps,
        )

    # ======================================================================
    # HOOKI DLA POZIOMÓW
    # ======================================================================

    @abstractmethod
    def update_level(self, scaled_dt: float, raw_dt: float) -> None:
        raise NotImplementedError

    @abstractmethod
    def draw_level(self) -> None:
        raise NotImplementedError

    def handle_event_level(self, event: pygame.event.Event) -> None:
        pass

    def on_beat(self) -> None:
        pass

    # ======================================================================
    # POMOCNICZE: dodawanie wroga
    # ======================================================================

    def add_enemy(self, enemy) -> None:
        if hasattr(enemy, "set_time_scale"):
            enemy.set_time_scale(self.time_scale)
        if hasattr(enemy, "set_effects_manager"):
            enemy.set_effects_manager(self.effects_manager)
        if self.camera is not None:
            enemy.camera = self.camera
        self.enemies.append(enemy)
