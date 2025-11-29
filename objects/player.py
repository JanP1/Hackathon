import pygame
import math
from objects.game_object import GameObject
from objects.smoke import SmokeTrail  # NOWE: dym do umiejętności na lewy przycisk


class Player(GameObject):
    def __init__(self, x_pos: int, y_pos: int, screen_w: int, screen_h: int, name: str = "player"):
        super().__init__(x_pos, y_pos, screen_w, screen_h, name)

        # Movement parameters
        self.speed = 5.0         # bazowa prędkość (px / klatkę przy time_scale=1)
        self.friction = 0.9
        self.velocity = pygame.math.Vector2(0, 0)

        # Bullet-time scale (1.0 = normal)
        self.time_scale: float = 1.0

        # Sound wave + distortion particles (lewy przycisk)
        # Każda fala ma promień; na obwodzie promienia spawnujemy dym (SmokeTrail)
        self.sound_waves = []  # list of dicts: {pos: (x,y), radius: float, max_radius: int}
        self.wave_speed = 7.0
        self.max_wave_radius = 180
        self.wave_color = (0, 255, 255)
        self.wave_thickness = 5

        # Dym dla fal (okrąg zniekształceń)
        self.wave_smoke = SmokeTrail(border=1)

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
        """
        Ustawia skalę czasu dla playera.

        Wpływa na:
        - normalny ruch (WASD),
        - dash (prędkość poruszania się podczas dashu),
        - prędkość rozchodzenia się fali (wave).
        """
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

        # efektywna prędkość z bullet-time
        effective_speed = self.speed * self.time_scale

        # Normalize diagonal movement so it's not faster than straight
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
        # Face towards mouse cursor left/right
        mx, my = pygame.mouse.get_pos()
        self.facing_right = mx >= self.rect.centerx

    # -------------------------------------------------
    # Dash
    # -------------------------------------------------
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

        # efektywna prędkość dashu z bullet-time
        effective_dash_speed = self.dash_speed * self.time_scale

        # Move along dash direction
        self.rect.x = int(self.rect.x + self.dash_dir.x * effective_dash_speed)
        self.rect.y = int(self.rect.y + self.dash_dir.y * effective_dash_speed)
        # Clamp to screen bounds
        self.rect.x = max(0, min(self.SCREEN_W - self.rect.width, self.rect.x))
        self.rect.y = max(0, min(self.SCREEN_H - self.rect.height, self.rect.y))

    # -------------------------------------------------
    # Attack waves (LEWY PRZYCISK: fala + zniekształcające partikles)
    # -------------------------------------------------
    def _handle_mouse_click(self):
        pressed = pygame.mouse.get_pressed(num_buttons=3)
        if pressed[0]:  # left click
            if not self._mouse_was_pressed:
                now = pygame.time.get_ticks()
                if now >= self._next_attack_time_ms:
                    # Spawn a new sound wave at player's center
                    self.sound_waves.append(
                        {
                            "pos": (self.rect.centerx, self.rect.centery),
                            "radius": 0.0,
                            "max_radius": self.max_wave_radius,
                        }
                    )
                    # Optionally play a sound if one is set up with key 'guitar'
                    self.play_sound("guitar")
                    # Set next allowed attack time
                    self._next_attack_time_ms = now + self.attack_cooldown_ms
            self._mouse_was_pressed = True
        else:
            self._mouse_was_pressed = False

    def _update_waves(self):
        """
        - Promień fali rośnie.
        - Na obwodzie okręgu (we wszystkich kierunkach) spawnujemy dym (SmokeTrail),
          tak żeby zniekształcenie było dokładnie na pierścieniu.
        """
        # rozchodzenie się fal
        for wave in self.sound_waves:
            wave["radius"] += self.wave_speed * self.time_scale

            r = wave["radius"]
            cx, cy = wave["pos"]

            # liczba punktów na pierścieniu (ilość kierunków)
            points_on_ring = 24

            for i in range(points_on_ring):
                angle = (2.0 * math.pi / points_on_ring) * i
                # pozycja na okręgu
                px = cx + math.cos(angle) * r
                py = cy + math.sin(angle) * r

                # niewielka prędkość na zewnątrz, żeby dym lekko "odpływał"
                vx = math.cos(angle) * 2.0
                vy = math.sin(angle) * 2.0

                # dodajemy zniekształcający particle dymu
                self.wave_smoke.add_particle(px, py, vx, vy)

        # usuwamy fale, które przekroczyły max_radius
        self.sound_waves = [w for w in self.sound_waves if w["radius"] <= w["max_radius"]]

    # -------------------------------------------------
    # Public update / draw
    # -------------------------------------------------
    def update(self):
        # Dash takes precedence over normal movement
        if not self.is_dashing:
            self._handle_input()
        self._handle_look_direction()
        # Dash input can be attempted every frame
        self._try_start_dash()
        # Update dash movement if active
        self._update_dash()
        # Lewy przycisk – fala z dymem
        self._handle_mouse_click()
        self._update_waves()
        # aktualizacja dymu fal
        self.wave_smoke.update()

    def draw(self, screen):
        # Najpierw rysujemy dym (zniekształcenie tła / obiektów)
        self.wave_smoke.draw(screen)

        # Draw the player (uses facing_right from base class).
        # If dashing, rotate 360deg and scale down slightly.
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

        # (opcjonalne) wizualne okręgi fali – jeśli chcesz zostawić „rysowany” wave
        # for wave in self.sound_waves:
        #     if wave["radius"] > 0:
        #         pygame.draw.circle(
        #             screen,
        #             self.wave_color,
        #             wave["pos"],
        #             int(wave["radius"]),
        #             self.wave_thickness,
        #         )

        # Dot kierunku celowania
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
