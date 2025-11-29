from __future__ import annotations

from pathlib import Path
from typing import Callable

import pygame
import mido  # pip install mido


def load_midi_note_times(midi_path: Path) -> list[float]:
    """
    Zwraca listę czasów (w sekundach, narastająco) dla wszystkich NOTE_ON
    z dodatnią velocity. Używamy tego do synchronizacji z muzyką.
    """
    if not midi_path.exists():
        print(f"[WARN] load_midi_note_times: nie znaleziono pliku {midi_path}")
        return []

    mid = mido.MidiFile(midi_path)
    times: list[float] = []
    current_time = 0.0

    for msg in mid:
        current_time += msg.time
        if msg.type == "note_on" and msg.velocity > 0:
            times.append(current_time)

    print(f"[INFO] Załadowano {len(times)} note_on z {midi_path.name}")
    if times[:5]:
        print("[INFO] Pierwsze nuty:", ", ".join(f"{t:.3f}s" for t in times[:5]))
    return times


class Level1AudioManager:
    """
    Odpowiada za:
    - inicjalizację miksera,
    - (opcjonalne) odtwarzanie tła MP3 w pętli,
    - wirtualny czas MIDI: music_time liczone z scaled_dt,
    - wywoływanie callbacka on_beat(note_time, music_time),
    - (opcjonalny) klik dźwiękowy na każdym bicie.
    """

    def __init__(
        self,
        fps: int,
        bit_mid_path: Path,
        mexican_mp3_path: Path,
        enable_background_mp3: bool = False,
    ) -> None:
        self.fps = fps
        self.bit_mid_path = bit_mid_path
        self.mexican_mp3_path = mexican_mp3_path
        self.enable_background_mp3 = enable_background_mp3

        self.mexican_sound: pygame.mixer.Sound | None = None
        self.click_sound: pygame.mixer.Sound | None = None

        self.midi_note_times: list[float] = []
        self.next_note_index: int = 0

        # WIRTUALNY czas muzyki sterowany przez scaled_dt z gry
        self.music_time: float = 0.0
        self.music_started: bool = False

        self._debug_last_music_time_int: int = -1

        self._init_mixer()
        if self.enable_background_mp3:
            self._load_background_mp3()
        self._load_midi_times()
        self._load_click_sound()

    # ======================
    # Inicjalizacja audio
    # ======================

    def _init_mixer(self) -> None:
        if not pygame.mixer.get_init():
            pygame.mixer.init()

    def _load_background_mp3(self) -> None:
        """
        Tło mp3 – gra w stałym tempie, NIE podlega time_scale.
        Używaj tylko, jeśli nie zależy Ci na „bullet time” dla muzyki.
        """
        print(f"[INFO] MEXICAN_MP3_PATH = {self.mexican_mp3_path}")
        if self.mexican_mp3_path.exists():
            try:
                self.mexican_sound = pygame.mixer.Sound(str(self.mexican_mp3_path))
                self.mexican_sound.play(loops=-1)
                print("[INFO] mexicanBit.mp3 odpalony w pętli.")
            except pygame.error as e:
                print(f"[WARN] Nie udało się załadować mexicanBit.mp3: {e}")
        else:
            print(f"[WARN] Nie znaleziono pliku mexicanBit.mp3: {self.mexican_mp3_path}")

    def _load_midi_times(self) -> None:
        print(f"[INFO] BIT_MID_PATH = {self.bit_mid_path}")
        self.midi_note_times = load_midi_note_times(self.bit_mid_path)
        self.music_time = 0.0
        self.next_note_index = 0
        self.music_started = len(self.midi_note_times) > 0

    def _load_click_sound(self) -> None:
        """
        Ładuje krótki klik na beat z pliku click.wav w tym samym katalogu co bit.mid.
        """
        click_path = self.bit_mid_path.parent / "click.wav"
        if not click_path.exists():
            print(f"[INFO] Brak pliku kliknięcia: {click_path} (beat będzie tylko wizualny).")
            return

        try:
            self.click_sound = pygame.mixer.Sound(str(click_path))
            print(f"[INFO] Załadowano click.wav: {click_path}")
        except pygame.error as e:
            print(f"[WARN] Nie udało się załadować click.wav: {e}")
            self.click_sound = None

    # ======================
    # Publiczne API
    # ======================

    def stop(self) -> None:
        """
        Zatrzymuje odtwarzanie mp3 i czyści stan beatów.
        """
        try:
            pygame.mixer.music.stop()
        except Exception:
            pass

        if self.mexican_sound is not None:
            try:
                self.mexican_sound.stop()
            except Exception:
                pass

        self.music_started = False

    def update(self, on_beat: Callable[[float, float], None], scaled_dt: float) -> None:
        """
        Wołane co klatkę z game_level7.
        scaled_dt = dt * time_scale z Game:
        - wirtualny czas muzyki (self.music_time) rośnie wg scaled_dt,
        - wszystkie beaty lecą wolniej/szybciej razem z resztą gry.
        """
        if not self.midi_note_times or not self.music_started:
            return

        if scaled_dt < 0.0:
            scaled_dt = 0.0

        # aktualizacja wirtualnego czasu muzyki
        self.music_time += scaled_dt

        music_time_int = int(self.music_time)
        if music_time_int != self._debug_last_music_time_int:
            self._debug_last_music_time_int = music_time_int
            print(
                f"[DEBUG] music_time ~ {self.music_time:6.3f}s, "
                f"next_note_index={self.next_note_index}"
            )

        # epsilon jako „okno” czasu – bierzemy mniej więcej jedną klatkę
        epsilon = scaled_dt

        # Jeśli w tej klatce „miniemy” jakieś nuty, odpalamy on_beat dla każdej
        while self.next_note_index < len(self.midi_note_times):
            note_time = self.midi_note_times[self.next_note_index]
            if note_time <= self.music_time + epsilon:
                # triggerujemy beat w logice poziomu
                on_beat(note_time, self.music_time)

                # opcjonalny metronom
                if self.click_sound is not None:
                    self.click_sound.play()

                self.next_note_index += 1
            else:
                break
