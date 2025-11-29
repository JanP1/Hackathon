import pygame
import math
from objects.game_object import GameObject


class Player(GameObject):
    def __init__(self, x_pos: int, y_pos: int, screen_w: int, screen_h: int,
                map_width = 4096,
                map_height = 4096,
                 name: str = "player"):
        super().__init__(x_pos, y_pos, screen_w, screen_h, name)

        self.is_alive = True


        # -------------------------- Experimental


# Add at the end of Player.__init__, after camera & sprite_flipped
# Load animation frames for right and left facing
        self.anim_frames_right = []
        self.anim_frames_left = []
        for i in range(25):
            img = pygame.image.load(
                f"assets/pictures/walk_animation/mariachi_walk{i:04}.png"
            ).convert_alpha()
            self.anim_frames_right.append(img)
            self.anim_frames_left.append(pygame.transform.flip(img, True, False))
        self.anim_index = 0

        
# At the end of Player.__init__
        self.facing_right = True
        # self.sprite_flipped = pygame.transform.flip(self.sprite, True, False)
        self.camera = None  # Will be injected if using a camera
        # ---------------------------------------

        # Health system
        self.max_health = 100
        self.current_health = self.max_health

        
        # Map size
        self.map_width = map_width
        self.map_height = map_height

        # Movement parameters
        self.speed = 15
        self.friction = 0.6
        self.velocity = pygame.math.Vector2(0, 0)

        # Sound wave visuals generated on mouse click
        self.sound_waves = []  # list of dicts: {pos: (x,y), radius: float, max_radius: int}
        self.wave_speed = 7
        self.max_wave_radius = 180
        self.wave_color = (0, 255, 255)
        # Kolor fali, gdy kliknięcie nastąpi "on beat" (wymóg: czerwona)
        self.on_beat_wave_color = (255, 0, 0)
        self.wave_thickness = 5
        # Parametry wizualne fali dla kliknięcia on-beat (dłuższa i grubsza)
        self.on_beat_max_wave_radius = 250
        self.on_beat_wave_thickness = 12

        # Click handling to avoid spawning too many waves at once
        self._mouse_was_pressed = False
        # Attack cooldown (milliseconds)
        self.attack_cooldown_ms = 700
        self._next_attack_time_ms = 0

        # Beat / damage system (mirrors Enemy logic where applicable)
        self.beat_counter = 0
        # Base damage of a sound wave and a cumulative bonus increased on beat-clicks
        self.base_wave_damage = 10
        self.wave_damage_bonus = 0

        # Flaga była używana do pokolorowania następnej fali; nieużywana przy natychmiastowym sprawdzaniu
        self._on_beat_click_pending = False

        # Funkcja sprawdzająca czy w tej klatce jest beat (wstrzykiwana z zewnątrz)
        self._on_beat_checker = None

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

        
        # ------------------------------------------ Experimental
        # Animacja
        if self.velocity.length_squared() > 0:
            self.anim_index = (self.anim_index + 0.25) % len(self.anim_frames_right)
            self.sprite = self.anim_frames_right[int(self.anim_index)] if self.facing_right else self.anim_frames_left[int(self.anim_index)]
        else:
            self.sprite = self.anim_frames_right[0] if self.facing_right else self.anim_frames_left[0]

        # ------------------------------------------------------

        # Apply movement and clamp to screen
        self.rect.x = int(max(0, min(self.map_width - self.rect.width, self.rect.x + self.velocity.x)))
        self.rect.y = int(max(0, min(self.map_height - self.rect.height, self.rect.y + self.velocity.y)))

    def _handle_look_direction(self):
        # If dashing, always face dash direction
        if self.is_dashing:
            if abs(self.dash_dir.x) > 1e-6:
                self.facing_right = self.dash_dir.x >= 0
            return

        # Otherwise, face toward the mouse in world coordinates
        mx, my = pygame.mouse.get_pos()
        if self.camera is not None:
            mx += self.camera.x
            my += self.camera.y
        self.facing_right = mx >= self.rect.centerx

    def _try_start_dash(self):
        # Left Shift triggers dash if off cooldown
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LSHIFT] and not self.is_dashing:
            now = pygame.time.get_ticks()
            if now >= self._next_dash_time_ms:
                # Prefer direction of current movement; if stationary, use cursor direction
                if self.velocity.length_squared() > 0:
                    vec = self.velocity.normalize()
                else:
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
                # Obróć gracza w stronę dashu natychmiast po rozpoczęciu
                if abs(self.dash_dir.x) > 1e-6:
                    self.facing_right = self.dash_dir.x >= 0
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
                    # Sprawdź w chwili kliknięcia, czy jest beat
                    on_beat_now = False
                    if callable(self._on_beat_checker):
                        try:
                            on_beat_now = bool(self._on_beat_checker())
                        except Exception:
                            on_beat_now = False

                    # Ustal parametry fali: jeśli on-beat, fala jest dłuższa i ma większe obramowanie
                    max_radius = self.on_beat_max_wave_radius if on_beat_now else self.max_wave_radius
                    thickness = self.on_beat_wave_thickness if on_beat_now else self.wave_thickness
                    color = self.wave_color  # bez zmiany koloru
                    # Spawn a new sound wave at player's center
                    self.sound_waves.append({
                        "pos": (self.rect.centerx, self.rect.centery),
                        "radius": 0.0,
                        "max_radius": max_radius,
                        "color": color,
                        "thickness": thickness,
                        # Store damage so other systems can read it
                        "damage": self.base_wave_damage + self.wave_damage_bonus,
                    })
                    # Jeśli kliknięto dokładnie w beat, zwiększ licznik i bonus obrażeń od razu
                    if on_beat_now:
                        self.beat_counter += 1
                        self.wave_damage_bonus += 15
                    # Optionally play a sound if one is set up with key 'guitar'
                    self.play_sound('guitar')
                    # Set next allowed attack time
                    self._next_attack_time_ms = now + self.attack_cooldown_ms
            self._mouse_was_pressed = True
        else:
            self._mouse_was_pressed = False

    def on_beat(self):
        """Wywoływane z main_copy.py w momencie uderzenia beatu.
        W nowej logice sprawdzamy beat w momencie kliknięcia, więc tutaj nie modyfikujemy obrażeń.
        """
        if not self.is_alive:
            return
        # Zachowujemy metodę dla kompatybilności, ale bez efektu ubocznego
        return

    def set_on_beat_checker(self, checker_fn):
        """Wstrzykuje funkcję zwracającą True/False czy aktualnie jest beat.
        Np. przekazać BPMCounter.is_on_beat.
        """
        self._on_beat_checker = checker_fn

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
        # Determine camera offset
        cam_x, cam_y = (0, 0)
        if self.camera is not None:
            cam_x, cam_y = self.camera.x, self.camera.y

        # Draw the player (with dash rotation if active)
        if self.is_dashing:
            base_sprite = self.sprite  # already correctly flipped
            now = pygame.time.get_ticks()
            elapsed = now - self.dash_start_time_ms
            t = max(0.0, min(1.0, elapsed / (self.dash_duration_ms if self.dash_duration_ms > 0 else 1)))
            angle = 360 * t if self.facing_right else -360 * t
            spun = pygame.transform.rotozoom(base_sprite, -angle, self.dash_scale)
            spun_rect = spun.get_rect(center=(self.rect.centerx - cam_x, self.rect.centery - cam_y))
            screen.blit(spun, spun_rect)
        else:
            screen.blit(self.sprite, (self.rect.x - cam_x - 30, self.rect.y - cam_y - 50))

        # Draw sound waves
        for wave in self.sound_waves:
            if wave["radius"] > 0:
                pygame.draw.circle(
                    screen,
                    wave.get("color", self.wave_color),
                    (wave["pos"][0] - cam_x, wave["pos"][1] - cam_y),
                    int(wave["radius"]),
                    wave.get("thickness", self.wave_thickness)
                )

        # Draw the dot pointing to mouse
        mx, my = pygame.mouse.get_pos()
        cx, cy = self.rect.centerx, self.rect.centery
        vx, vy = mx + cam_x - cx, my + cam_y - cy
        dist_sq = vx * vx + vy * vy
        if dist_sq > self.look_max_distance ** 2:
            scale = self.look_max_distance / (dist_sq ** 0.5)
            vx *= scale
            vy *= scale
        dot_x = int(cx + vx - cam_x)
        dot_y = int(cy + vy - cam_y)
        pygame.draw.circle(screen, (255, 255, 255), (dot_x, dot_y), 8)

        # Draw health bar
        self._draw_attack_cooldown_bar(screen)

    def _draw_attack_cooldown_bar(self, screen):
        """Rysuje pasek życia gracza (zamiast paska cooldownu)."""
        # Wymiary i pozycja paska (centrowany przy dolnej krawędzi)
        bar_width = self.SCREEN_W / 3
        bar_height = 30
        bar_y_offset = self.SCREEN_H / 14
        x = int(self.SCREEN_W / 2 - bar_width / 2)
        y = int(self.SCREEN_H - bar_y_offset)

        # Tło paska (czerwone tło zdrowia)
        pygame.draw.rect(screen, (120, 20, 20), (x, y, int(bar_width), bar_height))

        # Procent zdrowia
        if self.max_health > 0:
            progress = max(0.0, min(1.0, self.current_health / self.max_health))
        else:
            progress = 0.0

        # Wypełnienie paska (zielone zdrowie)
        fill_width = int(bar_width * progress)
        if fill_width > 0:
            pygame.draw.rect(screen, (0, 200, 0), (x, y, fill_width, bar_height))

        # Obramowanie paska
        pygame.draw.rect(screen, (255, 255, 255), (x, y, int(bar_width), bar_height), 2)

    # ==== Health API ====
    def take_damage(self, amount: int):
        """Zadaje obrażenia graczowi i obsługuje śmierć."""
        if not self.is_alive:
            return
        try:
            dmg = int(amount)
        except Exception:
            dmg = 0
        if dmg <= 0:
            return
        self.current_health -= dmg
        if self.current_health <= 0:
            self.current_health = 0
            self.is_alive = False

    def heal(self, amount: int):
        if not self.is_alive:
            return
        try:
            val = int(amount)
        except Exception:
            val = 0
        if val <= 0:
            return
        self.current_health = min(self.max_health, self.current_health + val)

    def get_health_percentage(self) -> float:
        return 0.0 if self.max_health <= 0 else max(0.0, min(1.0, self.current_health / self.max_health))
