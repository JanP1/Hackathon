# objects/player.py

import math
import pygame

from objects.game_object import GameObject


class Player(GameObject):
    def __init__(self, x_pos: int, y_pos: int, screen_w: int, screen_h: int, name: str = "player"):
        super().__init__(x_pos, y_pos, screen_w, screen_h, name)

        # Movement parameters
        self.speed = 5.0         # bazowa prędkość (px / klatkę przy time_scale=1)
        self.friction = 0.9
        self.velocity = pygame.math.Vector2(0, 0)

        # Bullet-time scale (1.0 = normal)
        self.time_scale: float = 1.0

        # Sound wave (lewy przycisk):
        # - TYLKO logika (pos, radius), bez rysowania pierścienia na CPU
        self.sound_waves = []  # list of dicts: {pos: (x,y), radius: float, max_radius: int}
        self.wave_speed = 7.0
        self.max_wave_radius = 180
        self.wave_color = (0, 255, 255)
        self.wave_thickness = 40  # używane przez shader GL (gl_postprocess)

        # Click handling to avoid spawning too many waves at once
        self._mouse_was_pressed = False
        # Attack cooldown (milliseconds)
        self.attack_cooldown_ms = 2000  # 2 seconds
        self._next_attack_time_ms = 0

        # Dash parameters
        self.is_dashing = False
        self.dash_cooldown_ms = 3000  # 3 seconds cooldown
        self._next_dash_time_ms = 0
        self.dash_duration_ms = 220  # total dash time (real time)
        self.dash_speed = 18.0       # bazowa prędkość dashu (px / klatkę przy time_scale=1)
        self.dash_dir = pygame.math.Vector2(0, 0)
        self.dash_start_time_ms = 0
        self.dash_scale = 0.8  # slightly smaller sprite during dash

        # Max distance for look indicator (cursor dot) from player center
        self.look_max_distance = 250

        # Ensure rect is positioned correctly relative to provided x,y as center
        self.rect.centerx = x_pos
        self.rect.centery = y_pos

    # -------------------------------------------------
    # Time scale (bullet-time)
    # -------------------------------------------------
    def set_time_scale(self, time_scale: float) -> None:
        self.time_scale = max(0.0, float(time_scale))

    # -------------------------------------------------
    # Input / movement
    # -------------------------------------------------
    def _handle_input(self):
        keys = pygame.key.get_pressed()

        direction = pygame.math.Vector2(0, 0)

        if keys[pygame.K_w]:
            direction.y -= 1
        if keys[pygame.K_s]:
            direction.y += 1
        if keys[pygame.K_a]:
            direction.x -= 1
        if keys[pygame.K_d]:
            direction.x += 1

        effective_speed = self.speed * self.time_scale

        if direction.length() > 0:
            direction = direction.normalize()
            self.velocity = direction * effective_speed
        else:
            self.velocity *= self.friction

            if abs(self.velocity.length()) < self.speed / 5.0:
                self.velocity = pygame.math.Vector2(0, 0)

        # Apply movement and clamp to screen
        self.rect.x = int(
            max(0, min(self.SCREEN_W - self.rect.width, self.rect.x + self.velocity.x))
        )
        self.rect.y = int(
            max(0, min(self.SCREEN_H - self.rect.height, self.rect.y + self.velocity.y))
        )

    def _handle_look_direction(self):
        mx, my = pygame.mouse.get_pos()
        self.facing_right = mx >= self.rect.centerx

    # -------------------------------------------------
    # Dash
    # -------------------------------------------------
    def _try_start_dash(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LSHIFT] and not self.is_dashing:
            now = pygame.time.get_ticks()
            if now >= self._next_dash_time_ms:
                cx, cy = self.rect.centerx, self.rect.centery
                mx, my = pygame.mouse.get_pos()
                dx = mx - cx
                dy = my - cy
                vec = pygame.math.Vector2(dx, dy)
                if vec.length_squared() == 0:
                    vec = pygame.math.Vector2(1 if self.facing_right else -1, 0)
                else:
                    vec = vec.normalize()
                self.dash_dir = vec
                self.is_dashing = True
                self.dash_start_time_ms = now
                self._next_dash_time_ms = now + self.dash_cooldown_ms

    def _update_dash(self):
        if not self.is_dashing:
            return

        now = pygame.time.get_ticks()
        elapsed = now - self.dash_start_time_ms
        if elapsed >= self.dash_duration_ms:
            self.is_dashing = False
            return

        effective_dash_speed = self.dash_speed * self.time_scale

        self.rect.x = int(self.rect.x + self.dash_dir.x * effective_dash_speed)
        self.rect.y = int(self.rect.y + self.dash_dir.y * effective_dash_speed)

        self.rect.x = max(0, min(self.SCREEN_W - self.rect.width, self.rect.x))
        self.rect.y = max(0, min(self.SCREEN_H - self.rect.height, self.rect.y))

    # -------------------------------------------------
    # Attack waves (LEWY PRZYCISK)
    # -------------------------------------------------
    def _handle_mouse_click(self):
        pressed = pygame.mouse.get_pressed(num_buttons=3)
        if pressed[0]:
            if not self._mouse_was_pressed:
                now = pygame.time.get_ticks()
                if now >= self._next_attack_time_ms:
                    self.sound_waves.append(
                        {
                            "pos": (self.rect.centerx, self.rect.centery),
                            "radius": 0.0,
                            "max_radius": self.max_wave_radius,
                        }
                    )
                    self.play_sound("guitar")
                    self._next_attack_time_ms = now + self.attack_cooldown_ms
            self._mouse_was_pressed = True
        else:
            self._mouse_was_pressed = False

    def _update_waves(self):
        # promień każdej fali rośnie, bez rysowania na CPU
        for wave in self.sound_waves:
            wave["radius"] += self.wave_speed * self.time_scale

        # usuwamy fale, które przekroczyły max_radius
        self.sound_waves = [w for w in self.sound_waves if w["radius"] <= w["max_radius"]]

    # -------------------------------------------------
    # Public update / draw
    # -------------------------------------------------
    def update(self):
        if not self.is_dashing:
            self._handle_input()

        self._handle_look_direction()
        self._try_start_dash()
        self._update_dash()
        self._handle_mouse_click()
        self._update_waves()

    def draw(self, screen: pygame.Surface):
        # UWAGA:
        # Pierścień fali NIE jest rysowany tutaj – efekt robi shader OpenGL,
        # który korzysta z player.sound_waves + wave_thickness.
        # Tutaj rysujemy tylko samego playera + celownik.

        # Player
        if self.is_dashing:
            base_sprite = self.sprite if self.facing_right else self.sprite_flipped
            now = pygame.time.get_ticks()
            elapsed = now - self.dash_start_time_ms
            t = max(0.0, min(1.0, elapsed / (self.dash_duration_ms if self.dash_duration_ms > 0 else 1)))
            angle = 360 * t if self.facing_right else -360 * t
            spun = pygame.transform.rotozoom(base_sprite, -angle, self.dash_scale)
            spun_rect = spun.get_rect(center=self.rect.center)
            screen.blit(spun, spun_rect)
        else:
            super().draw(screen)

        # celownik (biała kropka)
        mx, my = pygame.mouse.get_pos()
        cx, cy = self.rect.centerx, self.rect.centery
        vx = mx - cx
        vy = my - cy
        dist_sq = vx * vx + vy * vy
        if dist_sq == 0:
            dot_x, dot_y = cx, cy
        else:
            max_d = self.look_max_distance
            max_d_sq = max_d * max_d
            if dist_sq > max_d_sq:
                d = math.sqrt(dist_sq)
                vx *= max_d / d
                vy *= max_d / d
            dot_x = int(cx + vx)
            dot_y = int(cy + vy)
        pygame.draw.circle(screen, (255, 255, 255), (dot_x, dot_y), 8)
