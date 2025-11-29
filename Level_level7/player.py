from __future__ import annotations

import pygame


class Level1Player:
    """
    Odpowiada za:
    - pozycję i ruch kostki,
    - kolizje z krawędziami,
    - flashe kolorów przy uderzeniu i beacie,
    - rysowanie kostki.
    """

    def __init__(
        self,
        screen_width: int,
        screen_height: int,
        size: int,
        speed: float,
    ) -> None:
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.size = size
        self.speed = float(speed)

        self.rect = pygame.Rect(
            screen_width // 2 - size // 2,
            screen_height // 2 - size // 2,
            size,
            size,
        )

        # Kolory
        self.color_normal = (50, 200, 50)
        self.color_hit = (250, 80, 80)
        self.color_beat = (80, 180, 255)
        self.color = self.color_normal

        # Timery „flashów”
        self.hit_flash_time = 0.15
        self.hit_flash_timer = 0.0

        self.beat_flash_time = 0.15
        self.beat_flash_timer = 0.0
        self.beat_jump_pixels = 10

    def update(self, dt: float) -> None:
        """
        - odczyt klawiatury,
        - ruch z normalizacją (skosy tak samo szybkie),
        - kolizje z krawędziami i hit-flash,
        - dekrementacja timerów flashy.
        """
        keys = pygame.key.get_pressed()

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

            dx = norm_dx * self.speed * dt
            dy = norm_dy * self.speed * dt
        else:
            dx = 0.0
            dy = 0.0

        self.rect.x += int(round(dx))
        self.rect.y += int(round(dy))

        # kolizje z krawędziami
        hit = False

        if self.rect.left < 0:
            self.rect.left = 0
            hit = True
        if self.rect.right > self.screen_width:
            self.rect.right = self.screen_width
            hit = True
        if self.rect.top < 0:
            self.rect.top = 0
            hit = True
        if self.rect.bottom > self.screen_height:
            self.rect.bottom = self.screen_height
            hit = True

        if hit:
            self.on_hit()

        # timery flashy
        if self.hit_flash_timer > 0.0:
            self.hit_flash_timer -= dt
            if self.hit_flash_timer <= 0.0:
                self.hit_flash_timer = 0.0
                if self.beat_flash_timer <= 0.0:
                    self.color = self.color_normal

        if self.beat_flash_timer > 0.0:
            self.beat_flash_timer -= dt
            if self.beat_flash_timer <= 0.0:
                self.beat_flash_timer = 0.0
                if self.hit_flash_timer <= 0.0:
                    self.color = self.color_normal

    def on_hit(self) -> None:
        """
        Wywoływane przy uderzeniu w krawędź – czerwony flash.
        """
        self.color = self.color_hit
        self.hit_flash_timer = self.hit_flash_time

    def on_beat(self, note_time: float, music_time: float) -> None:
        """
        Callback dla AudioManagera – wywoływany przy bicie z MIDI.
        """
        print(f"[BEAT] note_time={note_time:.3f}s, music_time={music_time:.3f}s")

        self.color = self.color_beat
        self.beat_flash_timer = self.beat_flash_time

        # mały skok do góry
        self.rect.y -= self.beat_jump_pixels
        if self.rect.top < 0:
            self.rect.top = 0

    def draw(self, surface: pygame.Surface) -> None:
        """
        Rysowanie prostokąta gracza.
        """
        pygame.draw.rect(surface, self.color, self.rect)
