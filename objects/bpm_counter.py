import pygame
import math
from objects.game_object import GameObject


class BPMCounter(GameObject):
    def __init__(
        self,
        x_pos: int,
        y_pos: int,
        SCREEN_W: int,
        SCREEN_H: int,
        bpm: int = 120,
        midi_note_times: list[float] | None = None,
    ):
        """
        BPM Counter sterowany:
        - albo stałym BPM (fallback),
        - albo realnymi czasami nut z bit.mid (midi_note_times: lista sekund).

        Args:
            x_pos: X position on screen (center)
            y_pos: Y position on screen (bottom pivot point)
            SCREEN_W: Screen width
            SCREEN_H: Screen height
            bpm: Beats per minute (fallback, gdy brak midi)
            midi_note_times: lista czasów NOTE_ON z bit.mid (sekundy, narastająco)
        """
        super().__init__(x_pos, y_pos, SCREEN_W, SCREEN_H, "bpm_counter")

        # --------------------------------
        # TRYB: MIDI czy stały BPM
        # --------------------------------
        self.midi_note_times: list[float] | None = None
        self.use_midi: bool = False

        if midi_note_times is not None and len(midi_note_times) >= 2:
            # posortuj na wszelki wypadek
            self.midi_note_times = sorted(midi_note_times)
            self.use_midi = True
            print(f"[BPM] BPMCounter: używam bit.mid ({len(self.midi_note_times)} nut).")
        else:
            print("[BPM] BPMCounter: brak/za mało nut z bit.mid – używam stałego BPM.")
            self.use_midi = False

        # --------------------------------
        # Wspólny stan
        # --------------------------------
        # "Bieżący" BPM – w trybie MIDI obliczany na podstawie interwału nut
        self.bpm: float = float(bpm)

        # Własny czas gry w sekundach (rośnie o delta_time z update)
        self.music_time_sec: float = 0.0

        # Beat progress 0..1 dla animacji
        self.beat_progress: float = 0.0

        # Fallback: stały BPM (gdy brak MIDI)
        self.fixed_beat_duration_sec: float = 60.0 / float(bpm)

        # --------------------------------
        # MIDI indeksy / interwały
        # --------------------------------
        # index nuty, która jest "następna"
        self._next_note_index: int = 0
        # czas ostatniego beatu
        self._last_beat_time: float = 0.0
        # czas następnego beatu
        self._next_beat_time: float = (
            self.midi_note_times[0] if self.use_midi else self.fixed_beat_duration_sec
        )
        # dla get_beat_number()
        self._beat_counter: int = 0

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

    # ==============================
    # Konfiguracja
    # ==============================

    def set_bpm(self, bpm: int):
        """
        Zmiana BPM – działa tylko w trybie stałego BPM (fallback).
        W trybie MIDI bieżący BPM jest liczony z interwału nut.
        """
        self.bpm = float(bpm)
        self.fixed_beat_duration_sec = 60.0 / float(bpm)
        print(f"[BPM] set_bpm fallback -> {self.bpm:.2f}")

    # ==============================
    # Aktualizacja logiki
    # ==============================

    def _update_from_midi(self, delta_time_sec: float):
        """
        Tryb MIDI:
        - music_time_sec rośnie o delta_time_sec,
        - aktualizujemy indeks nut i interwał,
        - wyliczamy beat_progress 0..1 i BPM.
        """
        if not self.midi_note_times:
            return

        self.music_time_sec += delta_time_sec

        # znajdź odpowiednią parę (last_beat_time, next_beat_time)
        # taką, że last_beat_time <= music_time < next_beat_time
        while (
            self._next_note_index < len(self.midi_note_times)
            and self.music_time_sec > self.midi_note_times[self._next_note_index]
        ):
            self._last_beat_time = self.midi_note_times[self._next_note_index]
            self._next_note_index += 1
            self._beat_counter += 1

            if self._next_note_index < len(self.midi_note_times):
                self._next_beat_time = self.midi_note_times[self._next_note_index]
            else:
                # jeśli skończyły się nuty, zakładamy ostatni interwał taki jak poprzedni
                # albo fallback do fixed_beat_duration_sec
                last_interval = (
                    self._next_beat_time - self._last_beat_time
                    if self._next_beat_time > self._last_beat_time
                    else self.fixed_beat_duration_sec
                )
                self._next_beat_time = self._last_beat_time + last_interval

        interval = self._next_beat_time - self._last_beat_time
        if interval <= 0.0:
            interval = self.fixed_beat_duration_sec

        # 0..1 gdzie jesteśmy między tymi dwoma nutami
        self.beat_progress = (self.music_time_sec - self._last_beat_time) / interval
        self.beat_progress = max(0.0, min(1.0, self.beat_progress))

        # bieżące BPM z interwału
        self.bpm = 60.0 / interval

        # Pulse gdy jesteśmy blisko "startu" kolejnego beatu
        center_tolerance = 0.08  # 1/4 interwału
        if self.beat_progress < center_tolerance:
            progress = self.beat_progress / center_tolerance
            self.pulse_scale = 1.0 + (self.max_pulse_scale - 1.0) * (1.0 - progress)
        else:
            self.pulse_scale = 1.0

    def _update_fixed(self, delta_time_sec: float):
        """
        Tryb stałego BPM (fallback).
        Działa jak Twoja oryginalna wersja, tylko na sekundach.
        """
        self.music_time_sec += delta_time_sec
        beat_duration = self.fixed_beat_duration_sec

        self.beat_progress = (self.music_time_sec % beat_duration) / beat_duration

        center_tolerance = 0.08
        if self.beat_progress < center_tolerance:
            progress = self.beat_progress / center_tolerance
            self.pulse_scale = 1.0 + (self.max_pulse_scale - 1.0) * (1.0 - progress)
        else:
            self.pulse_scale = 1.0

        # Beat count
        self._beat_counter = int(self.music_time_sec / beat_duration)

    def update(self, delta_time: float):
        """
        Update counter:
        - W TRYBIE MIDI: delta_time to sekundy (scaled_dt z gry),
          korzystamy z realnych czasów nut z bit.mid.
        - W TRYBIE STAŁYM: również sekundy, tylko liczymy wg stałego BPM.

        Args:
            delta_time: Time passed since last frame (sekundy!)
        """
        if not self.is_active:
            return

        # zabezpieczenie na minusy
        if delta_time < 0.0:
            delta_time = 0.0

        if self.use_midi:
            self._update_from_midi(delta_time)
        else:
            self._update_fixed(delta_time)

    # ==============================
    # Rysowanie
    # ==============================

    def draw(self, screen):
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
            (pivot_x - rect_width // 2, pivot_y),  # Bottom left
            (pivot_x + rect_width // 2, pivot_y),  # Bottom right
            (pivot_x + rect_width // 2, pivot_y - rect_height),  # Top right
            (pivot_x - rect_width // 2, pivot_y - rect_height),  # Top left
        ]
        pygame.draw.polygon(screen, self.static_color, static_points)

        # Moving rectangle (windshield wiper motion)
        # angle oparty na beat_progress: pełny oscyl w jednym interwale
        angle = math.sin(self.beat_progress * 2 * math.pi) * self.max_angle

        # Calculate the four corners of the rotated rectangle
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

    # ==============================
    # API pomocnicze
    # ==============================

    def is_on_beat(self, tolerance: float = 0.08) -> bool:
        """
        Czy jesteśmy blisko beatu:
        - w trybie MIDI i stałym – oparte o beat_progress 0..1.

        Args:
            tolerance: Jak blisko beatu (0.0..0.5)
        """
        return self.beat_progress < tolerance or self.beat_progress > (1 - tolerance)

    def get_beat_number(self) -> int:
        """
        Aktualny numer beatu od startu.
        - w trybie MIDI liczone z indeksu nut,
        - w trybie stałym – z czasu / interwału.
        """
        return self._beat_counter
