import math
import pygame
from objects.game_object import GameObject


class Player(GameObject):
    def __init__(
        self,
        x_pos: int,
        y_pos: int,
        screen_w: int,
        screen_h: int,
        scale: float = 1.0,
        name: str = "player",
    ):
        """
        Player:
        - pełny system HP + pasek życia,
        - dash (LShift) z rotacją i skalowaniem sprite’a,
        - sound waves (LPM) z on-beat bonusami (WIĘKSZY ZASIĘG FALI),
        - look-indicator (białe kółko w kierunku myszy),
        - integracja z BPM przez wstrzykiwaną funkcję is_on_beat(),
        - przygotowana pod bullet-time (time_scale),
        - integracja z EffectsManager (add_wave przy spawn fali),
        - animacja chodzenia z sekwencji PNG (jedna lista klatek, flip w draw),
        - ruch w koordynatach MAPY (map_width/map_height) + kamera (camera.x/y).
        """
        super().__init__(x_pos, y_pos, screen_w, screen_h, scale, name)

        self.is_alive = True

        # ==============================================================#
        # podstawowe stany
        # ==============================================================#
        self.facing_right: bool = True

        # ==============================================================#
        # Mapa i kamera
        # ==============================================================#
        self.map_width = screen_w
        self.map_height = screen_h
        self.camera = None  # type: ignore

        # ==============================================================#
        # Walk animation – JEDNA lista klatek, flip w draw
        # ==============================================================#
        self.anim_frames: list[pygame.Surface] = []

        for i in range(25):
            frame = pygame.image.load(
                f"assets/pictures/walk_animation/mariachi_walk{i:04}.png"
            ).convert_alpha()

            if self.scale != 1.0:
                fw = frame.get_width()
                fh = frame.get_height()
                frame = pygame.transform.scale(
                    frame,
                    (max(1, int(fw * self.scale)), max(1, int(fh * self.scale))),
                )

            self.anim_frames.append(frame)

        self.anim_index: float = 0.0

        if self.anim_frames:
            old_center = self.rect.center
            self.sprite = self.anim_frames[0]
            self.sprite_flipped = pygame.transform.flip(self.sprite, True, False)
            self.rect = self.sprite.get_rect()
            self.rect.center = old_center

        # ==============================================================#
        # Attack animation
        # ==============================================================#
        self.attack_anim_frames: list[pygame.Surface] = []
        try:
            for i in range(13):
                frame = pygame.image.load(
                    f"assets/pictures/guitar_hit_animation/mariachi_guitar_hit{i:04}.png"
                ).convert_alpha()
                if self.scale != 1.0:
                    fw, fh = frame.get_width(), frame.get_height()
                    frame = pygame.transform.scale(
                        frame, (max(1, int(fw * self.scale)), max(1, int(fh * self.scale)))
                    )
                self.attack_anim_frames.append(frame)
        except pygame.error as e:
            print(f"[WARN] Nie udało się załadować animacji ataku: {e}")

        self.is_attacking_anim = False
        self.attack_anim_index: float = 0.0
        self.attack_anim_speed: float = 0.4

        # --- Health system ---
        self.max_health = 100
        self.current_health = self.max_health

        # --- Movement parameters ---
        self.speed = 5
        self.friction = 0.9
        self.velocity = pygame.math.Vector2(0, 0)

        # --- Bullet-time scale ---
        self.time_scale: float = 1.0

        # --- Sound waves (atak) ---
        self.sound_waves: list[dict] = []
        self.wave_speed = 7
        self.max_wave_radius = 180           # normalny zasięg
        self.wave_color = (0, 255, 255)
        self.on_beat_wave_color = (255, 0, 0)
        self.wave_thickness = 5

        # WIĘKSZY ZASIĘG NA BEACIE + GRUBSZA FALA
        self.on_beat_max_wave_radius = 250   # większy range gdy klik na beacie
        self.on_beat_wave_thickness = 12

        self._mouse_was_pressed = False
        self.attack_cooldown_ms = 700
        self._next_attack_time_ms = 0

        self.beat_counter = 0
        self.base_wave_damage = 10
        self.wave_damage_bonus = 0

        self._on_beat_checker = None

        # --- Dash parameters ---
        self.is_dashing = False
        self.dash_cooldown_ms = 1000
        self._next_dash_time_ms = 0
        self.dash_duration_ms = 220
        self.dash_speed = 18
        self.dash_dir = pygame.math.Vector2(0, 0)
        self.dash_start_time_ms = 0
        self.dash_scale = 0.8

        # look indicator
        self.look_max_distance = 250

        # EffectsManager
        self.effects_manager = None

        self.rect.centerx = x_pos
        self.rect.centery = y_pos

    # ======================================================================
    # API mapy i czasu
    # ======================================================================

    def set_time_scale(self, time_scale: float) -> None:
        self.time_scale = float(time_scale)

    def set_effects_manager(self, manager) -> None:
        self.effects_manager = manager

    def set_map_size(self, map_width: int, map_height: int) -> None:
        if map_width > 0:
            self.map_width = int(map_width)
        if map_height > 0:
            self.map_height = int(map_height)

    # ======================================================================
    # Input / movement
    # ======================================================================

    def _handle_input(self) -> None:
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

        if direction.length() > 0:
            direction = direction.normalize()
            self.velocity = direction * self.speed
        else:
            self.velocity *= self.friction
            if abs(self.velocity.length()) < self.speed / 5:
                self.velocity = pygame.math.Vector2(0, 0)

        self.rect.x = int(
            max(0, min(self.map_width - self.rect.width, self.rect.x + self.velocity.x))
        )
        self.rect.y = int(
            max(0, min(self.map_height - self.rect.height, self.rect.y + self.velocity.y))
        )

        if self.anim_frames:
            if self.velocity.length_squared() > 0:
                self.anim_index = (self.anim_index + 0.25) % len(self.anim_frames)
                current = self.anim_frames[int(self.anim_index)]
            else:
                current = self.anim_frames[0]

            self.sprite = current
            self.sprite_flipped = pygame.transform.flip(self.sprite, True, False)

    def _handle_look_direction(self) -> None:
        if self.is_dashing:
            if abs(self.dash_dir.x) > 1e-6:
                self.facing_right = self.dash_dir.x >= 0
            return

        mx, my = pygame.mouse.get_pos()
        if self.camera is not None:
            mx += self.camera.x
            my += self.camera.y

        self.facing_right = mx >= self.rect.centerx

    # ======================================================================
    # Dash
    # ======================================================================

    def _try_start_dash(self) -> None:
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LSHIFT] and not self.is_dashing and self.is_alive:
            now = pygame.time.get_ticks()
            if now >= self._next_dash_time_ms:
                if self.velocity.length_squared() > 0:
                    vec = self.velocity.normalize()
                else:
                    cx, cy = self.rect.centerx, self.rect.centery
                    mx, my = pygame.mouse.get_pos()

                    if self.camera is not None:
                        mx += self.camera.x
                        my += self.camera.y

                    dx = mx - cx
                    dy = my - cy
                    vec = pygame.math.Vector2(dx, dy)
                    if vec.length_squared() == 0:
                        vec = pygame.math.Vector2(1 if self.facing_right else -1, 0)
                    else:
                        vec = vec.normalize()
                self.dash_dir = vec

                if abs(self.dash_dir.x) > 1e-6:
                    self.facing_right = self.dash_dir.x >= 0
                self.is_dashing = True
                self.dash_start_time_ms = now
                self._next_dash_time_ms = now + self.dash_cooldown_ms

    def _update_dash(self) -> None:
        if not self.is_dashing:
            return
        now = pygame.time.get_ticks()
        elapsed = now - self.dash_start_time_ms
        if elapsed >= self.dash_duration_ms:
            self.is_dashing = False
            return

        self.rect.x = int(self.rect.x + self.dash_dir.x * self.dash_speed)
        self.rect.y = int(self.rect.y + self.dash_dir.y * self.dash_speed)

        self.rect.x = max(0, min(self.map_width - self.rect.width, self.rect.x))
        self.rect.y = max(0, min(self.map_height - self.rect.height, self.rect.y))

    # ======================================================================
    # Waves / atak
    # ======================================================================

    def set_on_beat_checker(self, checker_fn) -> None:
        self._on_beat_checker = checker_fn

    def _handle_mouse_click(self) -> None:
        if not self.is_alive:
            self._mouse_was_pressed = False
            return

        pressed = pygame.mouse.get_pressed(num_buttons=3)
        if pressed[0]:
            if not self._mouse_was_pressed:
                now = pygame.time.get_ticks()
                if now >= self._next_attack_time_ms:
                    on_beat_now = False
                    if callable(self._on_beat_checker):
                        try:
                            on_beat_now = bool(self._on_beat_checker())
                        except Exception:
                            on_beat_now = False

                    self.is_attacking_anim = True
                    self.attack_anim_index = 0.0

                    # TU SIĘ DZIEJE WIĘKSZY RANGE NA BEACIE
                    max_radius = (
                        self.on_beat_max_wave_radius if on_beat_now else self.max_wave_radius
                    )
                    thickness = (
                        self.on_beat_wave_thickness if on_beat_now else self.wave_thickness
                    )
                    color = self.wave_color

                    wave = {
                        "pos": (self.rect.centerx, self.rect.centery),
                        "radius": 0.0,
                        "max_radius": max_radius,
                        "color": color,
                        "thickness": thickness,
                        "damage": self.base_wave_damage + self.wave_damage_bonus,
                        "on_beat": on_beat_now,
                    }
                    self.sound_waves.append(wave)

                    if self.effects_manager is not None and hasattr(
                        self.effects_manager, "add_wave"
                    ):
                        try:
                            self.effects_manager.add_wave(wave["pos"])
                        except TypeError:
                            pass

                    if on_beat_now:
                        self.beat_counter += 1
                        self.wave_damage_bonus += 15

                    self.play_sound("guitar")
                    self._next_attack_time_ms = now + self.attack_cooldown_ms
            self._mouse_was_pressed = True
        else:
            self._mouse_was_pressed = False

    def _update_waves(self) -> None:
        for wave in self.sound_waves:
            wave["radius"] += self.wave_speed
        self.sound_waves = [w for w in self.sound_waves if w["radius"] <= w["max_radius"]]

    def on_beat(self) -> None:
        if not self.is_alive:
            return
        return

    def _update_attack_animation(self) -> None:
        if not self.is_attacking_anim:
            return

        self.attack_anim_index += self.attack_anim_speed
        if self.attack_anim_index >= len(self.attack_anim_frames):
            self.is_attacking_anim = False
            self.attack_anim_index = 0.0

    # ======================================================================
    # update / draw
    # ======================================================================

    def update(self) -> None:
        if not self.is_alive:
            return

        if not self.is_dashing and not self.is_attacking_anim:
            self._handle_input()

        self._handle_look_direction()
        self._try_start_dash()
        self._update_dash()
        self._handle_mouse_click()
        self._update_waves()
        self._update_attack_animation()

    def draw(self, screen: pygame.Surface) -> None:
        cam_x, cam_y = 0, 0
        if self.camera is not None:
            cam_x, cam_y = self.camera.x, self.camera.y

        if self.is_attacking_anim and self.attack_anim_frames:
            frame_idx = int(self.attack_anim_index)
            attack_sprite = self.attack_anim_frames[frame_idx]
            if not self.facing_right:
                attack_sprite = pygame.transform.flip(attack_sprite, True, False)
            screen.blit(
                attack_sprite,
                (self.rect.x - cam_x, self.rect.y - cam_y),
            )
        elif self.is_dashing and self.is_alive:
            base_sprite = self.sprite if self.facing_right else self.sprite_flipped
            now = pygame.time.get_ticks()
            elapsed = now - self.dash_start_time_ms
            t = max(
                0.0,
                min(1.0, elapsed / (self.dash_duration_ms if self.dash_duration_ms > 0 else 1)),
            )
            angle = 360 * t if self.facing_right else -360 * t
            spun = pygame.transform.rotozoom(base_sprite, -angle, self.dash_scale)
            spun_rect = spun.get_rect(
                center=(self.rect.centerx - cam_x, self.rect.centery - cam_y)
            )
            screen.blit(spun, spun_rect)
        else:
            current_sprite = self.sprite if self.facing_right else self.sprite_flipped
            screen.blit(
                current_sprite,
                (self.rect.x - cam_x, self.rect.y - cam_y),
            )

        for wave in self.sound_waves:
            if wave["radius"] > 0:
                wx, wy = wave["pos"]
                pygame.draw.circle(
                    screen,
                    wave.get("color", self.wave_color),
                    (int(wx - cam_x), int(wy - cam_y)),
                    int(wave["radius"]),
                    wave.get("thickness", self.wave_thickness),
                )

        mx, my = pygame.mouse.get_pos()
        cam_x, cam_y = 0, 0
        if self.camera is not None:
            cam_x, cam_y = self.camera.x, self.camera.y

        world_mx = mx + cam_x
        world_my = my + cam_y

        cx, cy = self.rect.centerx, self.rect.centery
        vx = world_mx - cx
        vy = world_my - cy
        dist_sq = vx * vx + vy * vy

        if dist_sq == 0:
            dot_x, dot_y = cx - cam_x, cy - cam_y
        else:
            max_d = self.look_max_distance
            max_d_sq = max_d * max_d
            if dist_sq > max_d_sq:
                d = math.sqrt(dist_sq)
                vx *= max_d / d
                vy *= max_d / d
            dot_x = int(cx + vx - cam_x)
            dot_y = int(cy + vy - cam_y)

        pygame.draw.circle(screen, (255, 255, 255), (dot_x, dot_y), 8)

        self._draw_health_bar(screen)

    # ======================================================================
    # Health API
    # ======================================================================

    def _draw_health_bar(self, screen: pygame.Surface) -> None:
        bar_width = self.SCREEN_W / 3
        bar_height = 30
        bar_y_offset = self.SCREEN_H / 14
        x = int(self.SCREEN_W / 2 - bar_width / 2)
        y = int(self.SCREEN_H - bar_y_offset)

        if self.max_health > 0:
            progress = max(0.0, min(1.0, self.current_health / self.max_health))
        else:
            progress = 0.0

        fill_width = int(bar_width * progress)
        if fill_width > 0:
            pygame.draw.rect(screen, (255, 0, 0), (x, y, fill_width, bar_height))

        pygame.draw.rect(
            screen, (255, 255, 255), (x, y, int(bar_width), bar_height), 2
        )

    def take_damage(self, amount: int) -> None:
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

    def heal(self, amount: int) -> None:
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
        return (
            0.0
            if self.max_health <= 0
            else max(0.0, min(1.0, self.current_health / self.max_health))
        )
