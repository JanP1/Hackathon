from __future__ import annotations

from pathlib import Path
from typing import Callable

import pygame
import mido          # pip install mido
import vlc           # pip install python-vlc


def load_midi_note_times(midi_path: Path) -> list[float]:
    """
    Zwraca listę czasów (w sekundach, narastająco) dla wszystkich NOTE_ON
    z dodatnią velocity. Używamy tego do synchronizacji z muzyką (bit.mid).
    """
    print(f"[MIDI] midi_path = {midi_path} (exists={midi_path.exists()})")

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

    print(f"[MIDI] Załadowano {len(times)} NOTE_ON z {midi_path.name}")
    if times[:5]:
        print("[MIDI] Pierwsze nuty:", ", ".join(f"{t:.3f}s" for t in times[:5]))
    return times


class Level1AudioManager:
    """
    - Czyta bit.mid i daje on_beat(note_time, music_time) zgodnie z time_scale gry.
    - Odpala MP3 (mexicanBit.mp3) przez VLC i steruje jego prędkością.
    - Zmiana prędkości audio: DRUGI PLAYER + CROSSFADE:
        * old_player gra dalej swoim tempem
        * new_player startuje wyciszony, z tym samym czasem i nowym rate
        * przez ~400 ms ściszamy starego i podgłaśniamy nowego
        * potem starego stop() i wyrzucamy
    """

    def __init__(
        self,
        fps: int,
        bit_mid_path: Path,
        mexican_mp3_path: Path,
        enable_background_mp3: bool = True,
        start_delay_sec: float = 0.0,
    ) -> None:
        self.fps = fps
        self.bit_mid_path = bit_mid_path
        self.mexican_mp3_path = mexican_mp3_path
        self.enable_background_mp3 = enable_background_mp3
        self.start_delay_sec = float(start_delay_sec)
        self.delay_timer: float = 0.0
        self.started: bool = False

        print(f"[INIT] CWD = {Path.cwd()}")
        print(f"[INIT] bit_mid_path = {self.bit_mid_path} (exists={self.bit_mid_path.exists()})")
        print(f"[INIT] mexican_mp3_path = {self.mexican_mp3_path} (exists={self.mexican_mp3_path.exists()})")
        print(f"[INIT] start_delay_sec = {self.start_delay_sec}")

        # --- MIDI / beat ---
        self.midi_note_times: list[float] = load_midi_note_times(self.bit_mid_path)
        self.next_note_index: int = 0
        self.music_time: float = 0.0  # wirtualny czas utworu (sekundy)
        self._debug_last_music_time_int: int = -1

        # --- time scale (logika gry) ---
        self.time_scale: float = 1.0

        # --- AUDIO rate ---
        self.desired_audio_rate: float = 1.0   # docelowa prędkość zgodnie z time_scale
        self.active_rate: float = 1.0          # prędkość aktywnego playera

        self.min_audio_rate: float = 0.1       # minimalna prędkość muzyki
        self.max_audio_rate: float = 2.0       # maksymalna prędkość muzyki

        # --- VLC (MP3) i crossfade ---
        self.vlc_instance: vlc.Instance | None = None
        self.active_player: vlc.MediaPlayer | None = None
        self.next_player: vlc.MediaPlayer | None = None

        self.base_volume: int = 100

        self.crossfade_active: bool = False
        self.crossfade_start_ms: int = 0
        self.crossfade_duration_ms: int = 400  # 0.4 s crossfade

        # pygame.mixer tylko po to, żeby był zainicjalizowany (jeśli używasz gdzie indziej)
        if not pygame.mixer.get_init():
            pygame.mixer.init()

        if self.start_delay_sec <= 0:
            self._init_vlc_player()
            self.started = True
        else:
            # Init VLC instance but don't play yet
            self._init_vlc_instance_only()

    # =========================================================
    # VLC: tworzenie playerów i kontrola prędkości
    # =========================================================

    def _init_vlc_instance_only(self) -> None:
        if not self.enable_background_mp3:
            return
        try:
            self.vlc_instance = vlc.Instance()
        except Exception as e:
            print(f"[VLC][WARN] Nie udało się zainicjalizować VLC instance: {e}")
            self.vlc_instance = None

    def _create_player(
        self,
        rate: float,
        start_time_ms: int,
        volume: int,
    ) -> vlc.MediaPlayer | None:
        """
        Tworzy nowego VLC MediaPlayer dla mexicanBit.mp3:
        - ustawia go na podany rate,
        - ustawia pozycję (start_time_ms),
        - ustawia głośność,
        - uruchamia odtwarzanie.
        """
        if self.vlc_instance is None:
            print("[VLC] _create_player: brak instancji VLC.")
            return None

        if not self.mexican_mp3_path.exists():
            print(f"[VLC] _create_player: brak pliku {self.mexican_mp3_path}")
            return None

        try:
            player = self.vlc_instance.media_player_new()
            media = self.vlc_instance.media_new(str(self.mexican_mp3_path))
            player.set_media(media)

            # ustaw od razu volume na 0 (żeby nie było klików przy starcie)
            player.audio_set_volume(volume)

            player.play()
            # chwila na start, zanim zmienimy rate/czas
            pygame.time.delay(150)

            # ustaw prędkość (clamp na bezpieczny zakres)
            clamped_rate = max(self.min_audio_rate, min(self.max_audio_rate, rate))
            player.set_rate(clamped_rate)

            # ustaw pozycję (ms) – jeśli > 0
            if start_time_ms > 0:
                player.set_time(start_time_ms)

            print(
                f"[VLC] _create_player: rate={clamped_rate:.2f}, "
                f"time={start_time_ms} ms, volume={volume}"
            )

            return player
        except Exception as e:
            print(f"[VLC][WARN] _create_player: {e}")
            return None

    def _init_vlc_player(self) -> None:
        if not self.enable_background_mp3:
            print("[VLC] background mp3 wyłączone (enable_background_mp3=False)")
            return

        if not self.mexican_mp3_path.exists():
            print(f"[VLC][WARN] Nie znaleziono mexicanBit.mp3: {self.mexican_mp3_path}")
            return

        try:
            self.vlc_instance = vlc.Instance()
            print(f"[VLC] instance = {self.vlc_instance}")

            # pierwszy player: 1.0x, od początku, pełna głośność
            self.active_player = self._create_player(
                rate=1.0,
                start_time_ms=0,
                volume=self.base_volume,
            )
            self.active_rate = 1.0
            if self.active_player is not None:
                print("[VLC] active_player zainicjalizowany.")
            else:
                print("[VLC][WARN] active_player nie został utworzony.")

        except Exception as e:
            print(f"[VLC][WARN] Nie udało się zainicjalizować VLC: {e}")
            self.vlc_instance = None
            self.active_player = None

    def _start_crossfade_to_rate(self, new_rate: float) -> None:
        """
        Uruchamia crossfade:
        - old = active_player
        - next = new player z nowym rate, tę samą pozycją czasu, volume=0
        """
        if self.vlc_instance is None:
            print("[VLC] _start_crossfade_to_rate: brak instancji VLC.")
            return

        if self.active_player is None:
            # nie ma aktywnego – po prostu tworzymy jednego na nowym rate
            self.active_player = self._create_player(
                rate=new_rate,
                start_time_ms=0,
                volume=self.base_volume,
            )
            self.active_rate = new_rate
            self.crossfade_active = False
            self.next_player = None
            print("[VLC] _start_crossfade_to_rate: brak old_player, ustawiam tylko new.")
            return

        # aktualny czas utworu, żeby nowy player wskoczył mniej więcej w to samo miejsce
        try:
            current_time_ms = self.active_player.get_time()
        except Exception:
            current_time_ms = 0

        # jeśli jest już jakiś next_player (poprzedni crossfade przerwany) – wyłącz
        if self.next_player is not None:
            try:
                self.next_player.stop()
            except Exception:
                pass
            self.next_player = None

        # nowy player startuje wyciszony
        self.next_player = self._create_player(
            rate=new_rate,
            start_time_ms=max(0, current_time_ms),
            volume=0,
        )
        if self.next_player is None:
            print("[VLC][WARN] _start_crossfade_to_rate: nie udało się utworzyć next_player.")
            return

        self.crossfade_active = True
        self.crossfade_start_ms = pygame.time.get_ticks()
        print(
            f"[VLC] CROSSFADE start: old_rate={self.active_rate:.2f}, "
            f"new_rate={new_rate:.2f}, time={current_time_ms} ms"
        )

    def _update_crossfade(self) -> None:
        """
        Aktualizacja crossfade'u – wywoływana w update().
        """
        if not self.crossfade_active:
            return
        if self.active_player is None or self.next_player is None:
            self.crossfade_active = False
            return

        now = pygame.time.get_ticks()
        elapsed = now - self.crossfade_start_ms
        if elapsed <= 0:
            elapsed = 0

        t = elapsed / float(self.crossfade_duration_ms)
        if t >= 1.0:
            t = 1.0

        # starego ściszamy 100->0, nowego podgłaśniamy 0->100
        old_vol = int((1.0 - t) * self.base_volume)
        new_vol = int(t * self.base_volume)

        try:
            self.active_player.audio_set_volume(old_vol)
            self.next_player.audio_set_volume(new_vol)
        except Exception as e:
            print(f"[VLC][WARN] _update_crossfade volume set: {e}")

        if t >= 1.0:
            # koniec crossfade – zatrzymujemy starego, nowy staje się aktywny
            try:
                self.active_player.stop()
            except Exception:
                pass

            self.active_player = self.next_player
            self.next_player = None
            self.active_rate = self.desired_audio_rate
            self.crossfade_active = False

            print("[VLC] CROSSFADE done – nowy player przejął odtwarzanie.")

    # =========================================================
    # Publiczne sterowanie prędkością
    # =========================================================

    def set_time_scale(self, scale: float) -> None:
        """
        Ustawia globalny time_scale (logika gry) + docelową prędkość audio.
        - gra i beat mogą zejść do 0.1x,
        - audio też schodzi minimalnie do 0.1x.
        - jeśli różnica rate jest znacząca, robimy crossfade.
        """
        # time_scale gry – może iść do 0.1
        self.time_scale = max(0.1, float(scale))
        print(f"[TIME] set_time_scale({self.time_scale:.2f})")

        # mapujemy 1:1 na audio, ale clamp do [0.1, 2.0]
        new_rate = max(self.min_audio_rate, min(self.max_audio_rate, self.time_scale))
        self.desired_audio_rate = new_rate
        print(
            f"[TIME] desired_audio_rate={self.desired_audio_rate:.2f}, "
            f"active_rate={self.active_rate:.2f}"
        )

        # jeśli różnica jest bardzo mała – nie ma sensu crossfade
        if abs(self.desired_audio_rate - self.active_rate) < 0.05:
            print("[VLC] Różnica rate < 0.05 – pomijam crossfade.")
            return

        # odpalamy nowy player i crossfade
        self._start_crossfade_to_rate(self.desired_audio_rate)

    def stop(self) -> None:
        """
        Zatrzymuje mp3 i czyści stan beatów.
        """
        print("[AUDIO] stop()")

        if self.active_player is not None:
            try:
                self.active_player.stop()
            except Exception as e:
                print(f"[VLC][WARN] stop() active_player: {e}")

        if self.next_player is not None:
            try:
                self.next_player.stop()
            except Exception as e:
                print(f"[VLC][WARN] stop() next_player: {e}")

        self.active_player = None
        self.next_player = None
        self.vlc_instance = None

        self.midi_note_times.clear()
        self.next_note_index = 0
        self.music_time = 0.0
        self.crossfade_active = False

    # =========================================================
    # MIDI / beat – wirtualny czas, sterowany dt z gry
    # =========================================================

    def update(self, on_beat: Callable[[float, float], None], scaled_dt: float) -> None:
        """
        Wołane co klatkę z game_level7.
        scaled_dt = dt * time_scale z gry.

        - aktualizuje wirtualny czas utworu (music_time),
        - wyzwala on_beat(...) dla nut, które „minęliśmy” w tej klatce,
        - aktualizuje crossfade audio (jeśli trwa).
        """
        # Obsługa opóźnionego startu
        if not self.started:
            # Używamy scaled_dt czy raw dt? Zazwyczaj delay jest w czasie rzeczywistym.
            # Ale scaled_dt jest przekazywane z zewnątrz.
            # Załóżmy, że delay liczymy w czasie gry (scaled) lub rzeczywistym.
            # Skoro to "muzyka startuje po 3s", to pewnie chodzi o czas rzeczywisty (niezależny od slow-mo).
            # Ale tutaj dostajemy scaled_dt.
            # Przyjmijmy, że delay liczymy w scaled_dt dla uproszczenia, albo musielibyśmy dostawać raw_dt.
            # W BaseLevel.update przekazywane jest scaled_dt.
            # Jeśli gra startuje z time_scale=1.0, to to samo.
            self.delay_timer += scaled_dt
            if self.delay_timer >= self.start_delay_sec:
                self.started = True
                self._init_vlc_player()
            else:
                return

        # --- BEAT Z MIDI ---
        if self.midi_note_times:
            if scaled_dt < 0.0:
                scaled_dt = 0.0

            self.music_time += scaled_dt

            music_time_int = int(self.music_time)
            if music_time_int != self._debug_last_music_time_int:
                self._debug_last_music_time_int = music_time_int
                print(
                    f"[BEAT-DEBUG] music_time ~ {self.music_time:6.3f}s, "
                    f"next_note_index={self.next_note_index}"
                )

            epsilon = scaled_dt if scaled_dt > 0.0 else (1.0 / float(self.fps) if self.fps > 0 else 0.0)

            while self.next_note_index < len(self.midi_note_times):
                note_time = self.midi_note_times[self.next_note_index]
                if note_time <= self.music_time + epsilon:
                    on_beat(note_time, self.music_time)
                    self.next_note_index += 1
                else:
                    break

        # --- AUDIO CROSSFADE ---
        self._update_crossfade()
