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


class BaseLevel(ABC):
    """
    Bazowa klasa poziomu.

    WSPÓLNE SYSTEMY DLA WIELU LEVELI:
    - globalny time_scale (bullet time) sterowany scroll'em myszy,
    - audio:
        * Level1AudioManager (mp3 + bit.mid),
        * powiązanie time_scale z prędkością odtwarzania,
    - BPMCounter oparty o MIDI (midi_note_times z audio_managera),
    - EffectsManager:
        * przechowuje dane dla postprocessu (waves, bullets),
    - Player:
        * wstrzyknięty effects_manager (fale),
        * wstrzyknięty time_scale,
    - lista wrogów + wspólna obsługa on_beat(),
    - debug HUD (nazwa poziomu, FPS, time_scale, speed).

    PRZEBIEG FRAME:
    run_frame(dt, events) ->
        handle_events(events)  # ESC, scroll, zdarzenia poziomu
        update(dt)             # time_scale, audio, BPM, player, enemies, update_level()
        draw()                 # draw_level() + BPM + HUD
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
                fps=60,  # nominalne FPS – i tak korzystasz z dt
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
        # Player – wstrzykujemy effects_manager i time_scale
        # ------------------------------------------------------------------
        self.player = Player(
            self.WIDTH // 2,
            self.HEIGHT // 2,
            self.WIDTH,
            self.HEIGHT,
            "player",
        )
        if hasattr(self.player, "set_effects_manager"):
            self.player.set_effects_manager(self.effects_manager)
        if hasattr(self.player, "set_time_scale"):
            self.player.set_time_scale(self.time_scale)

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

        # ------------------------------------------------------------------
        # Enemies
        # ------------------------------------------------------------------
        self.enemies: List[RangedEnemy] = []

        # flaga dla zarządcy stanów / main loopa
        self.want_quit: bool = False

    # ======================================================================
    # PUBLICZNE API
    # ======================================================================

    def run_frame(self, dt: float, events: list[pygame.event.Event]) -> None:
        """
        Jedno wywołanie na klatkę:
        - dt w sekundach,
        - events z pygame.event.get().
        """
        self.handle_events(events)
        self.update(dt)
        self.draw()

    def stop_audio(self) -> None:
        if self.audio_manager is not None:
            self.audio_manager.stop()

    # ======================================================================
    # EVENTY
    # ======================================================================

    def handle_events(self, events: list[pygame.event.Event]) -> None:
        """
        Obsługa wspólnych eventów (ESC, scroll) + hook dla poziomu.
        """
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.on_escape_pressed()

            elif event.type == pygame.MOUSEWHEEL:
                if event.y > 0:
                    self._change_time_scale(+self.time_scale_step)
                elif event.y < 0:
                    self._change_time_scale(-self.time_scale_step)

            # przekazujemy dalej do poziomu (np. strzał prawym przyciskiem)
            self.handle_event_level(event)

    def on_escape_pressed(self) -> None:
        self.want_quit = True
        self.stop_audio()
        # jeżeli korzystasz z game_state_managera
        if self.game_state_manager is not None:
            # przykładowo:
            # self.game_state_manager.change_state("start")
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
        # Player
        if hasattr(self.player, "set_time_scale"):
            self.player.set_time_scale(self.time_scale)

        # Enemies
        for enemy in self.enemies:
            if hasattr(enemy, "set_time_scale"):
                enemy.set_time_scale(self.time_scale)

    # ======================================================================
    # UPDATE (wspólny + hooki poziomu)
    # ======================================================================

    def update(self, dt: float) -> None:
        """
        dt – sekundy od poprzedniej klatki.
        """
        if dt < 0.0:
            dt = 0.0

        scaled_dt = dt * self.time_scale  # bullet-time

        # EffectsManager – czyści stare dane, aktualizuje waves/bullets
        self.effects_manager.update()

        # upewnij się, że obiekty mają aktualny time_scale
        self._apply_time_scale_to_objects()

        # BPMCounter (oparty o MIDI)
        if self.bpm_counter is not None:
            self.bpm_counter.update(scaled_dt)

        # Audio manager (MIDI + crossfade mp3)
        if self.audio_manager is not None:
            self.audio_manager.update(
                lambda _note_time, _music_time: None,
                scaled_dt,
            )

        # Player – ruch, umiejętności itd.
        self.player.update()

        # Enemies:
        # - update na milisekundach (jak w level7),
        # - dla RangedEnemy ustawiamy target na gracza.
        delta_ms = dt * 1000.0
        for enemy in self.enemies:
            if getattr(enemy, "destroying", False):
                continue
            if hasattr(enemy, "update"):
                enemy.update(delta_ms)
            if isinstance(enemy, RangedEnemy):
                enemy.set_target(
                    self.player.rect.centerx,
                    self.player.rect.centery,
                )

        # Beat logic (wspólny) – jeden trigger na beat
        if self.bpm_counter is not None and self.bpm_counter.is_on_beat():
            if not self.beat_triggered:
                self.beat_triggered = True
                self._on_beat_common()
                self.on_beat()
        else:
            self.beat_triggered = False

        # Logika specyficzna dla poziomu (kulki, dymy, inne rzeczy)
        self.update_level(scaled_dt, dt)

    def _on_beat_common(self) -> None:
        """
        Wspólny mechanizm: każdy wróg, który ma on_beat(), dostaje callback.
        """
        for enemy in self.enemies:
            if getattr(enemy, "destroying", False):
                continue
            if hasattr(enemy, "on_beat"):
                enemy.on_beat()

    # ======================================================================
    # DRAW
    # ======================================================================

    def draw(self) -> None:
        """
        Rysowanie:
        - draw_level() – odpowiedzialność poziomu (tło, player, enemies, efekty),
        - BPMCounter,
        - Debug HUD.
        """
        self.draw_level()

        # BPMCounter
        if self.bpm_counter is not None:
            self.bpm_counter.draw(self.screen)

        # HUD debugowy
        fps = self.clock.get_fps() if self.clock is not None else 0.0
        self.debug_hud.draw(
            self.screen,
            base_player_speed=self.base_player_speed_param,
            time_scale=self.time_scale,
            fps=fps,
        )

    # ======================================================================
    # HOOKI DLA POZIOMÓW (do nadpisania)
    # ======================================================================

    @abstractmethod
    def update_level(self, scaled_dt: float, raw_dt: float) -> None:
        """
        Logika specyficzna dla danego levelu.
        - scaled_dt – sekundy z uwzględnieniem time_scale,
        - raw_dt    – sekundy bez time_scale.
        """
        raise NotImplementedError

    @abstractmethod
    def draw_level(self) -> None:
        """
        Rysowanie specyficzne dla danego levelu:
        tło, player, enemies, pociski, efekty itd.
        (BPM i HUD dorysowywane są w BaseLevel.draw()).
        """
        raise NotImplementedError

    def handle_event_level(self, event: pygame.event.Event) -> None:
        """
        Opcjonalny hook na eventy poziomu.
        Domyślnie nic nie robi.
        """
        pass

    def on_beat(self) -> None:
        """
        Opcjonalny hook wywoływany na beat (po wspólnym _on_beat_common()).
        Domyślnie nic nie robi.
        """
        pass

    # ======================================================================
    # DODATKOWE POMOCNICZE METODY (np. wygodne dodawanie wroga)
    # ======================================================================

    def add_enemy(self, enemy) -> None:
        """
        Pomocnicza metoda do dodawania wrogów tak, żeby mieli już
        poprawnie ustawiony time_scale i effects_manager (jeśli obsługują).
        """
        if hasattr(enemy, "set_time_scale"):
            enemy.set_time_scale(self.time_scale)
        if hasattr(enemy, "set_effects_manager"):
            enemy.set_effects_manager(self.effects_manager)
        self.enemies.append(enemy)
