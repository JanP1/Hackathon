import pygame
import math
from pathlib import Path
from typing import Optional, List

from objects.game_object import GameObject


class BPMCounter(GameObject):
    def __init__(
        self,
        x_pos: int,
        y_pos: int,
        SCREEN_W: int,
        SCREEN_H: int,
        scale: float = 1,
        bpm: int = 120,
        midi_path: Optional[str] = None,
        mexican_mp3_path: Optional[str] = None,
    ):
        """
        BPM Counter z ruchomym prostokątem.

        Tryby:
        - manualny: stałe BPM liczone z delta_time,
        - MIDI: rytm z pliku .mid (note_on),
        - dodatkowo: odpalany mp3 z assets/sounds/mexican.mp3 (jeśli jest).
        """
        super().__init__(x_pos, y_pos, SCREEN_W, SCREEN_H, scale, "bpm_counter")

        # --- konfiguracja BPM / MIDI ---
        self.bpm: float = float(bpm)
        self.beat_duration_ms: float = 60000.0 / self.bpm  # ms na beat

        # czas logiki licznika
        self.current_time_ms: float = 0.0
        self.beat_progress: float = 0.0  # 0..1 w obrębie beatu

        # Tryb MIDI
        self.use_midi: bool = False
        self.midi_times_ms: List[float] = []
        self.midi_index: int = 0
        self.average_interval_ms: float = self.beat_duration_ms

        # Audio (MIDI)
        self.music_started: bool = False
        self.music_start_ticks: int = 0

        # Audio (MP3)
        self.mexican_sound: Optional[pygame.mixer.Sound] = None

        # Ścieżki (tylko dla debug/logów)
        self._midi_path_str: Optional[str] = midi_path
        self._mexican_mp3_path_str: Optional[str] = mexican_mp3_path

        # Inicjalizacja audio
        if midi_path is not None:
            self._try_init_midi(midi_path)

        if mexican_mp3_path is not None:
            self._try_init_mexican_mp3(mexican_mp3_path)

        # Jeśli nie ma MIDI albo się nie udało – zostajemy w trybie manualnym
        if not self.use_midi:
            print("[BPMCounter] MIDI disabled, using manual BPM mode.")

        # Rectangle settings
        self.rect_width = 50
        self.rect_height = 200

        self.rect_moving_width = 20
        self.rect_moving_height = 200

        # Max angle for windshield wiper motion (in radians)
        self.max_angle = math.pi / 3  # 60 degrees total swing

        # Colors
        self.static_color = (100, 100, 255)  # Blue
        self.moving_color = (255, 100, 100)  # Red

        # Pulse effect
        self.pulse_scale = 1.0
        self.max_pulse_scale = 1.3

        self.is_active = True

    # -------------------------------------------------------------------------
    # Inicjalizacja / MIDI / MP3
    # -------------------------------------------------------------------------

    def _ensure_mixer(self) -> None:
        if not pygame.mixer.get_init():
            pygame.mixer.init()

    def _try_init_midi(self, midi_path_str: str) -> None:
        """
        Próbuje załadować plik MIDI i włączyć tryb synchronizacji z nutami.
        Odpala ten plik też jako muzykę przez pygame.mixer.music.
        """
        path = Path(midi_path_str)
        if not path.exists():
            print(f"[BPMCounter] MIDI file not found: {path}")
            return

        try:
            import mido  # type: ignore
        except ImportError:
            print("[BPMCounter] mido not installed, cannot use MIDI mode.")
            return

        mid = mido.MidiFile(str(path))
        times_sec: List[float] = []
        current_time = 0.0

        for msg in mid:
            current_time += msg.time
            if msg.type == "note_on" and getattr(msg, "velocity", 0) > 0:
                times_sec.append(current_time)

        if not times_sec:
            print(f"[BPMCounter] No note_on events in MIDI: {path.name}")
            return

        self.midi_times_ms = [t * 1000.0 for t in times_sec]

        # Średni interwał między beatami -> BPM z pliku MIDI
        if len(self.midi_times_ms) > 1:
            intervals = [
                self.midi_times_ms[i + 1] - self.midi_times_ms[i]
                for i in range(len(self.midi_times_ms) - 1)
                if self.midi_times_ms[i + 1] > self.midi_times_ms[i]
            ]
            if intervals:
                self.average_interval_ms = sum(intervals) / len(intervals)
                if self.average_interval_ms <= 0:
                    self.average_interval_ms = self.beat_duration_ms
                self.beat_duration_ms = self.average_interval_ms
                self.bpm = 60000.0 / self.beat_duration_ms

        self.use_midi = True
        self.midi_index = 0
        self.current_time_ms = 0.0

        print(f"[BPMCounter] MIDI loaded: {path.name}")
        print(f"[BPMCounter] Found {len(self.midi_times_ms)} note_on events.")
        print(f"[BPMCounter] Estimated BPM from MIDI: {self.bpm:.2f}")

        # Odpalenie MIDI jako audio (jeśli się da)
        try:
            self._ensure_mixer()
            pygame.mixer.music.load(str(path))
            pygame.mixer.music.play()
            self.music_started = True
            self.music_start_ticks = pygame.time.get_ticks()
            print("[BPMCounter] Started playing MIDI via pygame.mixer.music.")
        except Exception as e:
            print(f"[BPMCounter] Could not play MIDI audio: {e}")
            # nadal możemy używać samych czasów note_on

    def _try_init_mexican_mp3(self, mp3_path_str: str) -> None:
        """
        Odpala w pętli mp3 (mexican.mp3) jako tło.
        """
        path = Path(mp3_path_str)
        if not path.exists():
            print(f"[BPMCounter] mexican.mp3 not found: {path}")
            return

        try:
            self._ensure_mixer()
            self.mexican_sound = pygame.mixer.Sound(str(path))
            self.mexican_sound.play(loops=-1)
            print(f"[BPMCounter] mexican.mp3 started looping: {path.name}")
        except Exception as e:
            print(f"[BPMCounter] Could not play mexican.mp3: {e}")
            self.mexican_sound = None

    # -------------------------------------------------------------------------
    # Publiczne API
    # -------------------------------------------------------------------------

    def set_bpm(self, bpm: int) -> None:
        """Zmieniamy BPM (w trybie manualnym)."""
        self.bpm = float(bpm)
        self.beat_duration_ms = 60000.0 / self.bpm

    def update(self, delta_time: float) -> None:
        """
        Update the counter.

        Args:
            delta_time: Time passed since last frame in milliseconds
        """
        if not self.is_active:
            return

        if self.use_midi and self.midi_times_ms:
            # Tryb MIDI – czas z zegara pygame, zsynchronizowany z odtwarzaniem.
            self.current_time_ms = self._current_music_time_ms()
            self._update_midi_mode()
        else:
            # Tryb manualny – stara logika na stałym BPM.
            self.current_time_ms += delta_time
            self._update_manual_mode()

        # Pulse kiedy beat_progress blisko 0
        center_tolerance = 0.25
        if self.beat_progress < center_tolerance:
            progress = self.beat_progress / center_tolerance
            self.pulse_scale = 1.0 + (self.max_pulse_scale - 1.0) * (1.0 - progress)
        else:
            self.pulse_scale = 1.0

    def draw(self, screen) -> None:
        """Draw the rectangles."""
        if not self.is_active:
            return

        # Apply pulse scale
        rect_width = int(self.rect_width * self.pulse_scale)
        rect_height = int(self.rect_height * self.pulse_scale)

        moving_width = int(self.rect_moving_width * self.pulse_scale)
        moving_height = int(self.rect_moving_height * self.pulse_scale)

        # Pivot point (bottom center)
        pivot_x = self.rect.x
        pivot_y = self.rect.y

        # Static rectangle (vertical, pivoting from bottom)
        static_points = [
            (pivot_x - rect_width // 2, pivot_y),                # Bottom left
            (pivot_x + rect_width // 2, pivot_y),                # Bottom right
            (pivot_x + rect_width // 2, pivot_y - rect_height),  # Top right
            (pivot_x - rect_width // 2, pivot_y - rect_height),  # Top left
        ]
        pygame.draw.polygon(screen, self.static_color, static_points)

        # Moving rectangle (windshield wiper motion)
        angle = math.sin(self.beat_progress * 2 * math.pi) * self.max_angle

        # Bottom corners stay at pivot
        bottom_left = (pivot_x - moving_width // 2, pivot_y)
        bottom_right = (pivot_x + moving_width // 2, pivot_y)

        cos_a = math.cos(angle)
        sin_a = math.sin(angle)

        # Left top corner
        local_x = -moving_width // 2
        local_y = -moving_height
        top_left_x = pivot_x + (local_x * cos_a - local_y * sin_a)
        top_left_y = pivot_y + (local_x * sin_a + local_y * cos_a)

        # Right top corner
        local_x = moving_width // 2
        local_y = -moving_height
        top_right_x = pivot_x + (local_x * cos_a - local_y * sin_a)
        top_right_y = pivot_y + (local_x * sin_a + local_y * cos_a)

        moving_points = [
            bottom_left,
            bottom_right,
            (top_right_x, top_right_y),
            (top_left_x, top_left_y),
        ]
        pygame.draw.polygon(screen, self.moving_color, moving_points)

    def is_on_beat(self, tolerance: float = 0.15) -> bool:
        """
        Czy jesteśmy blisko beatu?

        tolerance – jak blisko 0 lub 1 beat_progress (0.0–0.5).
        """
        return self.beat_progress < tolerance or self.beat_progress > (1 - tolerance)

    def get_beat_number(self) -> int:
        """
        Get the current beat number.

        Manual: approx current_time / beat_duration.
        MIDI: liczba beatów które minęły (na podstawie midi_index).
        """
        if self.use_midi and self.midi_times_ms:
            return self.midi_index
        if self.beat_duration_ms <= 0:
            return 0
        return int(self.current_time_ms / self.beat_duration_ms)

    # -------------------------------------------------------------------------
    # Tryb manualny / MIDI
    # -------------------------------------------------------------------------

    def _update_manual_mode(self) -> None:
        """Stara logika oparta o stałe BPM."""
        if self.beat_duration_ms <= 0:
            self.beat_progress = 0.0
            return

        self.beat_progress = (
            self.current_time_ms % self.beat_duration_ms
        ) / self.beat_duration_ms

    def _update_midi_mode(self) -> None:
        """
        Ustawia beat_progress na podstawie listy czasów nut z pliku MIDI.
        """
        if not self.midi_times_ms:
            self._update_manual_mode()
            return

        # midi_index = indeks następnego beatu,
        # wszystkie < midi_index już minęły.
        while (
            self.midi_index < len(self.midi_times_ms)
            and self.current_time_ms >= self.midi_times_ms[self.midi_index]
        ):
            self.midi_index += 1

        if self.midi_index == 0:
            prev_time = 0.0
            next_time = self.midi_times_ms[0]
        elif self.midi_index >= len(self.midi_times_ms):
            prev_time = self.midi_times_ms[-1]
            next_time = prev_time + self.average_interval_ms
        else:
            prev_time = self.midi_times_ms[self.midi_index - 1]
            next_time = self.midi_times_ms[self.midi_index]

        interval = max(1.0, next_time - prev_time)
        self.beat_progress = (self.current_time_ms - prev_time) / interval

        # clamp 0..1
        if self.beat_progress < 0.0:
            self.beat_progress = 0.0
        elif self.beat_progress > 1.0:
            self.beat_progress = 1.0

    def _current_music_time_ms(self) -> float:
        """
        Czas (ms) od startu odtwarzania MIDI przez pygame.mixer.music.
        Jeśli muzyka nie została odpalona, korzysta z current_time_ms.
        """
        if not self.music_started:
            return self.current_time_ms

        now_ticks = pygame.time.get_ticks()
        elapsed = now_ticks - self.music_start_ticks
        if elapsed < 0:
            elapsed = 0
        return float(elapsed)
