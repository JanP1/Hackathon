# Game/Level_level1/game_level1.py

import sys
from pathlib import Path

import pygame
import mido  # pip install mido

# -----------------------------
# Stałe wspólne dla całej gry
# -----------------------------
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# -----------------------------
# Ścieżki
# Struktura:
#   Game/
#     game.py
#     assets/
#       sounds/
#         bit.mid
#         mexicanBit.mp3
#     Level_level1/
#       game_level1.py
# -----------------------------
BASE_DIR = Path(__file__).resolve().parent.parent  # folder Game/
SOUNDS_DIR = BASE_DIR / "assets" / "sounds"
BIT_MID_PATH = SOUNDS_DIR / "bit.mid"
MEXICAN_MP3_PATH = SOUNDS_DIR / "mexicanBit.mp3"


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


class Game:
    """
    Level1:
    - ruch kostki normalizowany (skosy = ta sama prędkość),
    - odtwarzanie bit.mid (steruje beatami),
    - równolegle odpalany mexicanBit.mp3 z tego samego folderu,
    - zmiana koloru kostki w rytm MIDI (note_on),
    - hit w ścianę też zmienia kolor.
    """

    def __init__(self, level_name: str, player_speed: float, bg_color: tuple[int, int, int]):
        pygame.init()
        pygame.display.set_caption(f"Game - {level_name}")

        print(f"[INFO] BIT_MID_PATH = {BIT_MID_PATH}")
        print(f"[INFO] MEXICAN_MP3_PATH = {MEXICAN_MP3_PATH}")

        # Audio: mixer
        pygame.mixer.init()

        # --- MP3 jako tło: Sound + play(-1) ---
        self.mexican_sound: pygame.mixer.Sound | None = None
        if MEXICAN_MP3_PATH.exists():
            try:
                self.mexican_sound = pygame.mixer.Sound(str(MEXICAN_MP3_PATH))
                # -1 = pętla w nieskończoność
                self.mexican_sound.play(loops=-1)
                print("[INFO] mexicanBit.mp3 odpalony w pętli.")
            except pygame.error as e:
                print(f"[WARN] Nie udało się załadować mexicanBit.mp3: {e}")
        else:
            print(f"[WARN] Nie znaleziono pliku mexicanBit.mp3: {MEXICAN_MP3_PATH}")

        # --- MIDI do beatów ---
        self.midi_note_times: list[float] = load_midi_note_times(BIT_MID_PATH)
        self.next_note_index: int = 0  # który note_on będzie następny
        self.beat_flash_time: float = 0.15  # jak długo flash po nucie

        # własny zegar do synchronizacji z muzyką
        self.music_started: bool = False
        self.music_start_ticks: int = 0  # pygame.time.get_ticks() w momencie startu

        if BIT_MID_PATH.exists():
            try:
                pygame.mixer.music.load(str(BIT_MID_PATH))
                pygame.mixer.music.play()  # jeden raz
                self.music_started = True
                self.music_start_ticks = pygame.time.get_ticks()
                print("[INFO] Odtwarzanie bit.mid rozpoczęte.")
            except pygame.error as e:
                print(f"[WARN] Nie udało się załadować bit.mid: {e}")
        else:
            print(f"[WARN] Nie znaleziono pliku muzyki: {BIT_MID_PATH}")

        self.level_name = level_name
        self.player_speed = float(player_speed)
        self.bg_color = bg_color

        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True

        self.player_size = 40
        self.player_rect = pygame.Rect(
            SCREEN_WIDTH // 2 - self.player_size // 2,
            SCREEN_HEIGHT // 2 - self.player_size // 2,
            self.player_size,
            self.player_size,
        )

        # Kolory kostki
        self.player_color_normal = (50, 200, 50)
        self.player_color_hit = (250, 80, 80)      # np. trafienie w ścianę
        self.player_color_beat = (80, 180, 255)    # kolor pod bit
        self.player_color = self.player_color_normal

        # Timery „flashów”
        self.hit_flash_time = 0.15
        self.hit_flash_timer = 0.0

        self.beat_flash_timer = 0.0

        # Dodatkowy parametr: jak bardzo reagujemy na beat (delikatny „puls”)
        self.beat_jump_pixels = 10

        # debug: żeby nie spamować co klatkę
        self._debug_last_music_time_int = -1

        pygame.font.init()
        self.debug_font = pygame.font.SysFont("consolas", 18)

    def run(self) -> None:
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0

            self._handle_events()
            self._update(dt)
            self._draw()

            pygame.display.flip()

        # sprzątanie audio
        try:
            pygame.mixer.music.stop()
        except Exception:
            pass
        if self.mexican_sound is not None:
            try:
                self.mexican_sound.stop()
            except Exception:
                pass

        pygame.quit()
        sys.exit()

    def _handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.running = False

    def _update(self, dt: float) -> None:
        keys = pygame.key.get_pressed()

        # ---- ruch z normalizacją, żeby skosy nie były szybsze ----
        raw_dx = 0.0
        raw_dy = 0.0

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            raw_dx -= 1.0
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            raw_dx += 1.0
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            raw_dy -= 1.0
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            raw_dy += 1.0

        length = (raw_dx * raw_dx + raw_dy * raw_dy) ** 0.5

        if length > 0.0:
            norm_dx = raw_dx / length
            norm_dy = raw_dy / length

            dx = norm_dx * self.player_speed * dt
            dy = norm_dy * self.player_speed * dt
        else:
            dx = 0.0
            dy = 0.0

        # aktualizacja poziomu
        self.player_rect.x += int(round(dx))
        self.player_rect.y += int(round(dy))

        # --- sprawdzanie uderzenia w krawędź ekranu ---
        hit = False

        if self.player_rect.left < 0:
            self.player_rect.left = 0
            hit = True
        if self.player_rect.right > SCREEN_WIDTH:
            self.player_rect.right = SCREEN_WIDTH
            hit = True
        if self.player_rect.top < 0:
            self.player_rect.top = 0
            hit = True
        if self.player_rect.bottom > SCREEN_HEIGHT:
            self.player_rect.bottom = SCREEN_HEIGHT
            hit = True

        if hit:
            self._on_hit()

        # --- obsługa flashy (uderzenie + beat) ---
        if self.hit_flash_timer > 0.0:
            self.hit_flash_timer -= dt
            if self.hit_flash_timer <= 0.0:
                self.hit_flash_timer = 0.0
                if self.beat_flash_timer <= 0.0:
                    self.player_color = self.player_color_normal

        if self.beat_flash_timer > 0.0:
            self.beat_flash_timer -= dt
            if self.beat_flash_timer <= 0.0:
                self.beat_flash_timer = 0.0
                if self.hit_flash_timer <= 0.0:
                    self.player_color = self.player_color_normal

        # --- synchronizacja z MIDI: note_on -> zmiana koloru ---
        self._update_music_sync()

    def _current_music_time(self) -> float:
        """
        Liczy czas muzyki od momentu wywołania pygame.mixer.music.play()
        przez własny zegar, zamiast get_pos().
        """
        if not self.music_started:
            return 0.0

        now_ticks = pygame.time.get_ticks()
        elapsed_ms = now_ticks - self.music_start_ticks
        return max(0.0, elapsed_ms / 1000.0)

    def _update_music_sync(self) -> None:
        """
        Sprawdza, na jakim czasie jest muzyka (wg naszego zegara),
        i czy doszliśmy do kolejnego note_on z listy.
        """
        if not self.midi_note_times or not self.music_started:
            return

        music_time = self._current_music_time()

        # prosty debug raz na sekundę
        music_time_int = int(music_time)
        if music_time_int != self._debug_last_music_time_int:
            self._debug_last_music_time_int = music_time_int
            print(
                f"[DEBUG] music_time ~ {music_time:6.3f}s, "
                f"next_note_index={self.next_note_index}"
            )

        # epsilon ~ 1 klatka
        epsilon = 1.0 / FPS

        while self.next_note_index < len(self.midi_note_times):
            note_time = self.midi_note_times[self.next_note_index]
            if note_time <= music_time + epsilon:
                self._on_beat(note_time, music_time)
                self.next_note_index += 1
            else:
                break

    def _on_hit(self) -> None:
        """
        Reakcja na uderzenie w krawędź:
        - flash koloru hit
        """
        self.player_color = self.player_color_hit
        self.hit_flash_timer = self.hit_flash_time

    def _on_beat(self, note_time: float, music_time: float) -> None:
        """
        Reakcja na nutę z MIDI:
        - flash koloru beat,
        - delikatny "puls" (przesunięcie kostki).
        """
        print(f"[BEAT] note_time={note_time:.3f}s, music_time={music_time:.3f}s")

        self.player_color = self.player_color_beat
        self.beat_flash_timer = self.beat_flash_time

        # "puls" – delikatne przesunięcie w górę
        self.player_rect.y -= self.beat_jump_pixels
        if self.player_rect.top < 0:
            self.player_rect.top = 0

    def _draw(self) -> None:
        self.screen.fill(self.bg_color)

        pygame.draw.rect(self.screen, self.player_color, self.player_rect)

        debug_text = (
            f"Level: {self.level_name} | "
            f"speed: {self.player_speed:.1f} px/s | "
            f"FPS: {self.clock.get_fps():.1f}"
        )
        text_surface = self.debug_font.render(debug_text, True, (255, 255, 255))
        self.screen.blit(text_surface, (10, 10))


# -----------------------------
# Zmienne globalne level1
# -----------------------------
level1_player_speed = 400.0
level1_bg_color = (10, 40, 90)


if __name__ == "__main__":
    """
    Uruchamiasz z katalogu głównego projektu (nad folderem Game):

        python Game/Level_level1/game_level1.py
    """
    game = Game(
        level_name="level1",
        player_speed=level1_player_speed,
        bg_color=level1_bg_color,
    )
    game.run()
