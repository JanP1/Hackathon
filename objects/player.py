import pygame
import math
from objects.game_object import GameObject


class Player(GameObject):
    def __init__(self, x_pos: int, y_pos: int, screen_w: int, screen_h: int, name: str = "player"):
        super().__init__(x_pos, y_pos, screen_w, screen_h, name)

        # Movement parameters
        self.speed = 5
        self.friction = 0.9
        self.velocity = pygame.math.Vector2(0, 0)

        # Sound wave visuals generated on mouse click
        self.sound_waves = []  # list of dicts: {pos: (x,y), radius: float, max_radius: int}
        self.wave_speed = 7
        self.max_wave_radius = 180
        self.wave_color = (0, 255, 255)
        self.wave_thickness = 5

        # Click handling to avoid spawning too many waves at once
        self._mouse_was_pressed = False
        # Attack cooldown (milliseconds)
        self.attack_cooldown_ms = 2000  # 2 seconds
        self._next_attack_time_ms = 0

        # Dash parameters
        self.is_dashing = False
        self.dash_cooldown_ms = 3000  # 3 seconds cooldown per spec
        self._next_dash_time_ms = 0
        self.dash_duration_ms = 220  # total dash time
        self.dash_speed = 18  # pixels per frame while dashing
        self.dash_dir = pygame.math.Vector2(0, 0)
        self.dash_start_time_ms = 0
        self.dash_scale = 0.8  # slightly smaller sprite during dash

        # Max distance for look indicator (cursor dot) from player center
        self.look_max_distance = 250

        # Ensure rect is positioned correctly relative to provided x,y as center
        # Incoming x_pos, y_pos are treated as center for convenience
        self.rect.centerx = x_pos
        self.rect.centery = y_pos

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

        # Normalize diagonal movement so it's not faster than straight
        if direction.length() > 0:
            direction = direction.normalize()
            self.velocity = direction * self.speed
        else:
            self.velocity *= self.friction

            if abs(self.velocity.length()) < self.speed / 5:
                self.velocity = pygame.math.Vector2(0, 0)

        # Apply movement and clamp to screen
        self.rect.x = int(max(0, min(self.SCREEN_W - self.rect.width, self.rect.x + self.velocity.x)))
        self.rect.y = int(max(0, min(self.SCREEN_H - self.rect.height, self.rect.y + self.velocity.y)))

    def _handle_look_direction(self):
        # Face towards mouse cursor left/right
        mx, my = pygame.mouse.get_pos()
        self.facing_right = mx >= self.rect.centerx

    def _try_start_dash(self):
        # Left Shift triggers dash if off cooldown
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
        # Move along dash direction
        self.rect.x = int(self.rect.x + self.dash_dir.x * self.dash_speed)
        self.rect.y = int(self.rect.y + self.dash_dir.y * self.dash_speed)
        # Clamp to screen bounds
        self.rect.x = max(0, min(self.SCREEN_W - self.rect.width, self.rect.x))
        self.rect.y = max(0, min(self.SCREEN_H - self.rect.height, self.rect.y))

    def _handle_mouse_click(self):
        pressed = pygame.mouse.get_pressed(num_buttons=3)
        if pressed[0]:  # left click
            if not self._mouse_was_pressed:
                now = pygame.time.get_ticks()
                if now >= self._next_attack_time_ms:
                    # Spawn a new sound wave at player's center
                    self.sound_waves.append({
                        "pos": (self.rect.centerx, self.rect.centery),
                        "radius": 0.0,
                        "max_radius": self.max_wave_radius,
                    })
                    # Optionally play a sound if one is set up with key 'guitar'
                    self.play_sound('guitar')
                    # Set next allowed attack time
                    self._next_attack_time_ms = now + self.attack_cooldown_ms
            self._mouse_was_pressed = True
        else:
            self._mouse_was_pressed = False

    def _update_waves(self):
        # Expand and cull finished waves
        for wave in self.sound_waves:
            wave["radius"] += self.wave_speed
        self.sound_waves = [w for w in self.sound_waves if w["radius"] <= w["max_radius"]]

    def update(self):
        # Handle all per-frame logic
        # Dash takes precedence over normal movement
        if not self.is_dashing:
            self._handle_input()
        self._handle_look_direction()
        # Dash input can be attempted every frame
        self._try_start_dash()
        # Update dash movement if active
        self._update_dash()
        self._handle_mouse_click()
        self._update_waves()

    def draw(self, screen):
        # Draw the player (uses facing_right from base class). If dashing, rotate 360deg and scale down slightly.
        if self.is_dashing:
            # Choose sprite based on facing
            base_sprite = self.sprite if self.facing_right else self.sprite_flipped
            # Compute rotation progress 0..360 over dash duration
            now = pygame.time.get_ticks()
            elapsed = now - self.dash_start_time_ms
            t = max(0.0, min(1.0, elapsed / (self.dash_duration_ms if self.dash_duration_ms > 0 else 1)))
            angle = 360 * t if self.facing_right else -360 * t
            spun = pygame.transform.rotozoom(base_sprite, -angle, self.dash_scale)
            spun_rect = spun.get_rect(center=self.rect.center)
            screen.blit(spun, spun_rect)
        else:
            super().draw(screen)

        # Draw sound waves
        for wave in self.sound_waves:
            if wave["radius"] > 0:
                pygame.draw.circle(screen, self.wave_color, wave["pos"], int(wave["radius"]), self.wave_thickness)

        # Draw a small dot clamped near the player along the direction to the mouse
        mx, my = pygame.mouse.get_pos()
        cx, cy = self.rect.centerx, self.rect.centery
        vx = mx - cx
        vy = my - cy
        # Compute distance and clamp to look_max_distance
        dist_sq = vx * vx + vy * vy
        if dist_sq == 0:
            dot_x, dot_y = cx, cy
        else:
            # Only clamp if outside max distance
            max_d = self.look_max_distance
            max_d_sq = max_d * max_d
            if dist_sq > max_d_sq:
                # normalize and scale
                import math
                d = math.sqrt(dist_sq)
                vx *= max_d / d
                vy *= max_d / d
            dot_x = int(cx + vx)
            dot_y = int(cy + vy)
        pygame.draw.circle(screen, (255, 255, 255), (dot_x, dot_y), 8)
