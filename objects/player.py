import pygame
from objects.game_object import GameObject


class Player(GameObject):
    def __init__(self, x_pos: int, y_pos: int, screen_w: int, screen_h: int, name: str = "player"):
        super().__init__(x_pos, y_pos, screen_w, screen_h, name)

        # Movement parameters
        self.speed = 5

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

        # Max distance for look indicator (cursor dot) from player center
        self.look_max_distance = 250

        # Ensure rect is positioned correctly relative to provided x,y as center
        # Incoming x_pos, y_pos are treated as center for convenience
        self.rect.centerx = x_pos
        self.rect.centery = y_pos

    def _handle_input(self):
        keys = pygame.key.get_pressed()

        move = pygame.math.Vector2(0, 0)

        if keys[pygame.K_w]:
            move.y -= 1
        if keys[pygame.K_s]:
            move.y += 1
        if keys[pygame.K_a]:
            move.x -= 1
        if keys[pygame.K_d]:
            move.x += 1

        # Normalize diagonal movement so it's not faster than straight
        if move.length() != 0:
            move = move.normalize() * self.speed

        # Apply movement and clamp to screen
        self.rect.x = int(max(0, min(self.SCREEN_W - self.rect.width, self.rect.x + move.x)))
        self.rect.y = int(max(0, min(self.SCREEN_H - self.rect.height, self.rect.y + move.y)))

    def _handle_look_direction(self):
        # Face towards mouse cursor left/right
        mx, my = pygame.mouse.get_pos()
        self.facing_right = mx >= self.rect.centerx

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
        self._handle_input()
        self._handle_look_direction()
        self._handle_mouse_click()
        self._update_waves()

    def draw(self, screen):
        # Draw the player (uses facing_right from base class)
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
