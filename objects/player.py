import math
import pygame
from objects.game_object import GameObject


class Player(GameObject):
    # statyczny font do napisu PERFECT!
    _perfect_font: pygame.font.Font | None = None

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
        - HP + pasek życia,
        - dash (LShift),
        - sound waves (LPM) z on-beat bonusami (większy zasięg),
        - prosty napis PERFECT! przy trafieniu w beat,
        - look-indicator,
        - integracja z BPM i EffectsManager,
        - ruch po mapie + kamera.
        """
        super().__init__(x_pos, y_pos, screen_w, screen_h, scale, name)

        self.is_alive = True
        self.facing_right: bool = True

        # ==================================================================
        # Mapa i kamera
        # ==================================================================
        self.map_width = screen_w
        self.map_height = screen_h
        self.camera = None  # type: ignore

        # ==================================================================
        # Animacja chodzenia
        # ==================================================================
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
            
            # Adjust rect for collision (smaller hitbox)
            # 10px from left, 10px from right, 10px from top. Bottom stays same.
            self.hitbox_offset_x = 50
            self.hitbox_offset_y = 50
            
            self.rect.width -= (self.hitbox_offset_x * 2)
            self.rect.height -= self.hitbox_offset_y
            
            # Center the new rect on the old center (or initial position)
            # Note: x_pos, y_pos are applied at the end of __init__
            # But here we are inside __init__, so we just prepare the size.
            
        # ==================================================================
        # Attack animation
        # ==================================================================
        self.attack_anim_frames: list[pygame.Surface] = []
        try:
            for i in range(13):
                frame = pygame.image.load(
                    f"assets/pictures/guitar_hit_animation/mariachi_guitar_hit{i:04}.png"
                ).convert_alpha()
                if self.scale != 1.0:
                    fw, fh = frame.get_width(), frame.get_height()
                    frame = pygame.transform.scale(
                        frame,
                        (max(1, int(fw * self.scale)), max(1, int(fh * self.scale))),
                    )
                self.attack_anim_frames.append(frame)
        except pygame.error as e:
            print(f"[WARN] Nie udało się załadować animacji ataku: {e}")

        self.is_attacking_anim = False
        self.attack_anim_index: float = 0.0
        self.attack_anim_speed: float = 0.4

        # --- Health system ---
        self.max_health = 200
        self.current_health = self.max_health

        # --- Damage Feedback ---
        self.damage_tint_timer = 0.0
        self.shake_timer = 0.0
        self.knockback_velocity = pygame.math.Vector2(0, 0)
        self.knockback_friction = 0.9

        # --- Movement parameters ---
        self.speed = 5
        self.friction = 0.9
        self.velocity = pygame.math.Vector2(0, 0)

        # --- Bullet-time scale ---
        self.time_scale: float = 1.0

        # --- Sound waves ---
        self.sound_waves: list[dict] = []
        # Prędkość fali w shaderze to 0.5 px/ms = 500 px/s
        self.wave_speed = 500.0
        # Zasięg fali w shaderze to 1000ms * 0.5px/ms = 500px
        self.max_wave_radius = 500.0
        self.wave_color = (0, 255, 255)
        self.on_beat_wave_color = (255, 0, 0)
        self.wave_thickness = 5

        # większy zasięg / grubość na beacie
        # Skoro shader ma stały czas życia fali (1000ms), to wizualnie każda fala leci do 500px.
        # Ustawiamy więc logiczny zasięg też na 500, żeby pasował do grafiki.
        self.on_beat_max_wave_radius = 500.0
        self.on_beat_wave_thickness = 12

        self._mouse_was_pressed = False
        self.attack_cooldown_ms = 700
        self._next_attack_time_ms = 0

        self.beat_counter = 0
        self.base_wave_damage = 10
        self.wave_damage_bonus = 0

        # on-beat checker z BPMCounter
        self._on_beat_checker = None

        # --- PERFECT! napis ---
        self.perfect_text_timer_ms: int = 0
        self._last_update_ticks: int = pygame.time.get_ticks()
        if Player._perfect_font is None:
            pygame.font.init()
            Player._perfect_font = pygame.font.SysFont("consolas", 32, bold=True)

        # --- Dash parameters ---
        self.is_dashing = False
        self.dash_cooldown_ms = 1000
        self._next_dash_time_ms = 0
        self.dash_duration_ms = 220
        self.dash_speed = 18
        self.dash_dir = pygame.math.Vector2(0, 0)
        self.dash_start_time_ms = 0
        self.dash_scale = 0.8

        self.look_max_distance = 250
        self.effects_manager = None

        # --- Sounds ---
        self.sound_left = None
        self.sound_fail = None
        self.sound_hurt = None
        try:
            self.sound_left = pygame.mixer.Sound("assets/sounds/left.mp3")
            self.sound_left.set_volume(0.5)
        except Exception as e:
            print(f"[WARN] Player sound left.mp3 error: {e}")

        try:
            self.sound_fail = pygame.mixer.Sound("assets/sounds/fail.mp3")
            self.sound_fail.set_volume(0.5)
        except Exception as e:
            print(f"[WARN] Player sound fail.mp3 error: {e}")
            
        try:
            self.sound_hurt = pygame.mixer.Sound("assets/sounds/zabolalo.mp3")
            self.sound_hurt.set_volume(0.6)
        except Exception as e:
            print(f"[WARN] Player sound zabolalo.mp3 error: {e}")

        self.rect.centerx = x_pos
        self.rect.centery = y_pos

        # --- Economy & Ability ---
        self.coins = 0
        self.wave_charge = 0
        self.max_wave_charge = 5
        
        # --- Slow Time Ability ---
        self.slow_time_charge = 0
        self.max_slow_time_charge = 10
        self.is_slow_time_active = False
        
        self.coin_anim_timer = 0
        self.coin_font = pygame.font.SysFont("consolas", 48, bold=True)
        self.small_font = pygame.font.SysFont("consolas", 20, bold=True)

    # ======================================================================
    # API mapy, czasu, efektów
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
    # BPM API
    # ======================================================================

    def set_on_beat_checker(self, checker_fn) -> None:
        """Podpięcie funkcji BPMCounter.is_on_beat."""
        self._on_beat_checker = checker_fn

    # ======================================================================
    # Input / movement
    # ======================================================================

    def _handle_input(self) -> None:
        # Apply knockback
        if self.knockback_velocity.length_squared() > 0.1:
            self.rect.x += int(self.knockback_velocity.x)
            self.rect.y += int(self.knockback_velocity.y)
            self.knockback_velocity *= self.knockback_friction
            if self.knockback_velocity.length_squared() < 0.1:
                self.knockback_velocity = pygame.math.Vector2(0, 0)
            
            # Clamp to map
            self.rect.x = int(max(0, min(self.map_width - self.rect.width, self.rect.x)))
            self.rect.y = int(max(0, min(self.map_height - self.rect.height, self.rect.y)))
            return # Disable normal movement during strong knockback? Or just add? Let's disable for a bit or just add.
            # Actually, let's just add it to position and allow player to fight against it slightly or just drift.
            # If we return here, player loses control. Let's allow control but knockback pushes.
        
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
            now = self.time_manager.time
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
        now = self.time_manager.time
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

    def _handle_mouse_click(self) -> None:
        if not self.is_alive:
            self._mouse_was_pressed = False
            return

        pressed = pygame.mouse.get_pressed(num_buttons=3)
        if pressed[0]:
            if not self._mouse_was_pressed:
                # Sprawdzenie naładowania umiejętności (5 killi)
                if self.wave_charge < self.max_wave_charge:
                    # Opcjonalnie dźwięk błędu, jeśli chcemy sygnalizować brak naładowania
                    # if self.sound_fail:
                    #     self.sound_fail.play()
                    self._mouse_was_pressed = True
                    return

                now = self.time_manager.time
                if now >= self._next_attack_time_ms:
                    # sprawdzenie beatu
                    on_beat_now = False
                    if callable(self._on_beat_checker):
                        try:
                            on_beat_now = bool(self._on_beat_checker())
                        except Exception:
                            on_beat_now = False

                    # animacja ataku
                    self.is_attacking_anim = True
                    self.attack_anim_index = 0.0

                    if not on_beat_now:
                        if self.sound_fail:
                            self.sound_fail.play()
                        # Nie tworzymy fali, jeśli nie trafiono w beat
                        self._next_attack_time_ms = now + self.attack_cooldown_ms
                        self._mouse_was_pressed = True
                        return

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
                        "hit_enemies": set(),  # Zbiór trafionych wrogów
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
                        # licznik beatu / bonus dmg
                        self.beat_counter += 1
                        self.wave_damage_bonus += 15
                        # proste: zapal timer napisu PERFECT! na ~0.6 s
                        self.perfect_text_timer_ms = 600
                        
                        # Zużywamy ładunek po udanym ataku
                        self.wave_charge = 0
                        
                        if self.sound_left:
                            self.sound_left.play()
                    else:
                        if self.sound_fail:
                            self.sound_fail.play()

                    # self.play_sound("guitar")
                    self._next_attack_time_ms = now + self.attack_cooldown_ms
            self._mouse_was_pressed = True
        else:
            self._mouse_was_pressed = False

    def _update_waves(self) -> None:
        dt = self.time_manager.dt
        for wave in self.sound_waves:
            wave["radius"] += self.wave_speed * dt
        self.sound_waves = [
            w for w in self.sound_waves if w["radius"] <= w["max_radius"]
        ]

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

        # dt do liczenia timera PERFECT!
        delta_ms = self.time_manager.dt_ms

        if not self.is_dashing:
            self._handle_input()

        self._handle_look_direction()
        self._try_start_dash()
        self._update_dash()
        self._handle_mouse_click()
        self._update_waves()
        self._update_attack_animation()

        # zmniejszamy timer PERFECT!
        if self.perfect_text_timer_ms > 0:
            self.perfect_text_timer_ms = max(0, self.perfect_text_timer_ms - delta_ms)

        if self.coin_anim_timer > 0:
            self.coin_anim_timer = max(0, self.coin_anim_timer - delta_ms)

        # Feedback timers
        if self.damage_tint_timer > 0:
            self.damage_tint_timer = max(0, self.damage_tint_timer - delta_ms)
        
        if self.shake_timer > 0:
            self.shake_timer = max(0, self.shake_timer - delta_ms)

    def draw(self, screen: pygame.Surface) -> None:
        cam_x, cam_y = 0, 0
        if self.camera is not None:
            cam_x, cam_y = self.camera.x, self.camera.y

        # Offset for drawing sprite relative to hitbox
        draw_x = self.rect.x - getattr(self, "hitbox_offset_x", 0) - cam_x
        draw_y = self.rect.y - getattr(self, "hitbox_offset_y", 0) - cam_y

        if self.is_attacking_anim and self.attack_anim_frames:
            frame_idx = int(self.attack_anim_index)
            attack_sprite = self.attack_anim_frames[frame_idx]
            if not self.facing_right:
                attack_sprite = pygame.transform.flip(attack_sprite, True, False)
            screen.blit(
                attack_sprite,
                (draw_x, draw_y),
            )
        elif self.is_dashing and self.is_alive:
            base_sprite = self.sprite if self.facing_right else self.sprite_flipped
            now = self.time_manager.time
            elapsed = now - self.dash_start_time_ms
            t = max(
                0.0,
                min(1.0, elapsed / (self.dash_duration_ms if self.dash_duration_ms > 0 else 1)),
            )
            angle = 360 * t if self.facing_right else -360 * t
            spun = pygame.transform.rotozoom(base_sprite, -angle, self.dash_scale)
            
            # Center spun sprite on the visual center of the character
            # Visual center is hitbox center adjusted by offset
            visual_center_x = self.rect.centerx
            visual_center_y = self.rect.centery - 5 # Approximate visual center adjustment
            
            spun_rect = spun.get_rect(
                center=(visual_center_x - cam_x, visual_center_y - cam_y)
            )
            screen.blit(spun, spun_rect)
        else:
            current_sprite = self.sprite if self.facing_right else self.sprite_flipped
            screen.blit(
                current_sprite,
                (draw_x, draw_y),
            )

        # Fale
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

        # Dot w stronę myszy
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

        # Pasek życia
        self._draw_health_bar(screen)

        # HUD (Coins + Wave)
        self._draw_hud(screen)

        # ===========================
        # NAPIS PERFECT!
        # ===========================
        if self.perfect_text_timer_ms > 0 and Player._perfect_font is not None:
            text_surf = Player._perfect_font.render("PERFECT!", True, (255, 255, 0))
            tw, th = text_surf.get_size()

            # okolice metronomu: metronom masz na (SCREEN_W-200, SCREEN_H-50)
            x = int(self.SCREEN_W - 200 - tw / 2)
            y = int(self.SCREEN_H - 120 - th / 2)

            screen.blit(text_surf, (x, y))

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
        
        # Draw HP Text
        hp_text = f"{int(self.current_health)} / {self.max_health}"
        text_surf = self.small_font.render(hp_text, True, (255, 255, 255))
        text_rect = text_surf.get_rect(center=(x + bar_width // 2, y + bar_height // 2))
        screen.blit(text_surf, text_rect)

    def take_damage(self, amount: int, source_pos: tuple[int, int] = None) -> None:
        if not self.is_alive:
            return
        try:
            dmg = int(amount)
        except Exception:
            dmg = 0
        if dmg <= 0:
            return
        self.current_health -= dmg
        
        # Feedback
        self.damage_tint_timer = 200.0 # ms
        self.shake_timer = 300.0 # ms
        
        if self.sound_hurt:
            self.sound_hurt.play()
            
        # Knockback
        if source_pos:
            sx, sy = source_pos
            cx, cy = self.rect.center
            dx = cx - sx
            dy = cy - sy
            dist = math.hypot(dx, dy)
            if dist > 0:
                # Push away
                force = 20.0 # Knockback strength
                self.knockback_velocity = pygame.math.Vector2(dx/dist * force, dy/dist * force)

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

    def add_kill(self) -> None:
        self.coins += 1
        if self.wave_charge < self.max_wave_charge:
            self.wave_charge += 1
        if self.slow_time_charge < self.max_slow_time_charge:
            self.slow_time_charge += 1
        # Trigger coin animation
        self.coin_anim_timer = 500

    def _draw_hud(self, screen: pygame.Surface) -> None:
        # 1. Coins
        # Icon
        icon_radius = 25
        icon_x = self.SCREEN_W - 160
        icon_y = 50
        pygame.draw.circle(screen, (255, 215, 0), (icon_x, icon_y), icon_radius)
        pygame.draw.circle(screen, (200, 170, 0), (icon_x, icon_y), icon_radius, 3) # border
        
        # Text
        scale = 1.0
        if self.coin_anim_timer > 0:
            t = self.coin_anim_timer / 500.0
            s = math.sin(t * math.pi) 
            scale = 1.0 + 0.5 * s
            
        text = f"{self.coins}"
        txt_surf = self.coin_font.render(text, True, (255, 215, 0))
        
        if scale != 1.0:
            w = int(txt_surf.get_width() * scale)
            h = int(txt_surf.get_height() * scale)
            txt_surf = pygame.transform.scale(txt_surf, (w, h))
            
        text_x = icon_x + 35
        text_y = icon_y - txt_surf.get_height() // 2
        screen.blit(txt_surf, (text_x, text_y))
        
        # 2. Wave Ability
        wave_x = self.SCREEN_W - 110
        wave_y = 100
        wave_w = 60
        wave_h = 60
        
        is_full = (self.wave_charge >= self.max_wave_charge)
        
        draw_x = wave_x
        draw_y = wave_y
        draw_w = wave_w
        draw_h = wave_h
        
        if is_full:
            draw_x -= 8
            draw_y -= 8
            draw_w += 16
            draw_h += 16
            
        rect = pygame.Rect(draw_x, draw_y, draw_w, draw_h)
        pygame.draw.rect(screen, (100, 100, 100), rect)
        
        if self.wave_charge > 0:
            fill_pct = self.wave_charge / self.max_wave_charge
            fill_h = int(draw_h * fill_pct)
            fill_rect = pygame.Rect(draw_x, draw_y + draw_h - fill_h, draw_w, fill_h)
            pygame.draw.rect(screen, (0, 255, 255), fill_rect)
            
        border_color = (255, 255, 255) if is_full else (50, 50, 50)
        pygame.draw.rect(screen, border_color, rect, 4 if is_full else 2)
        
        start_x = draw_x + 8
        end_x = draw_x + draw_w - 8
        mid_y = draw_y + draw_h / 2
        points = []
        steps = int(end_x - start_x)
        if steps > 0:
            for i in range(steps):
                x = start_x + i
                y = mid_y + math.sin(i * 0.2) * (draw_h * 0.25)
                points.append((x, y))
            if len(points) > 1:
                pygame.draw.lines(screen, (0, 0, 0), False, points, 3)

        # Wave count text
        if not is_full:
            needed = self.max_wave_charge - self.wave_charge
            count_surf = self.small_font.render(f"{needed}", True, (200, 200, 200))
            screen.blit(count_surf, (draw_x + draw_w + 5, draw_y + draw_h // 2 - 10))
        else:
            # Blink "LPM"
            if (pygame.time.get_ticks() // 500) % 2 == 0:
                lpm_surf = self.small_font.render("LPM", True, (0, 255, 255))
                screen.blit(lpm_surf, (draw_x + draw_w + 5, draw_y + draw_h // 2 - 10))

        # 3. Slow Time Ability
        # Below Wave
        slow_x = wave_x
        slow_y = wave_y + 80 # Spacing
        slow_w = 60
        slow_h = 60
        
        is_slow_full = (self.slow_time_charge >= self.max_slow_time_charge)
        
        s_draw_x = slow_x
        s_draw_y = slow_y
        s_draw_w = slow_w
        s_draw_h = slow_h
        
        if is_slow_full:
            s_draw_x -= 8
            s_draw_y -= 8
            s_draw_w += 16
            s_draw_h += 16
            
        s_rect = pygame.Rect(s_draw_x, s_draw_y, s_draw_w, s_draw_h)
        pygame.draw.rect(screen, (100, 100, 100), s_rect)
        
        if self.slow_time_charge > 0:
            fill_pct = self.slow_time_charge / self.max_slow_time_charge
            fill_h = int(s_draw_h * fill_pct)
            fill_rect = pygame.Rect(s_draw_x, s_draw_y + s_draw_h - fill_h, s_draw_w, fill_h)
            pygame.draw.rect(screen, (100, 0, 255), fill_rect) # Purple for time
            
        s_border_color = (255, 255, 255) if is_slow_full else (50, 50, 50)
        pygame.draw.rect(screen, s_border_color, s_rect, 4 if is_slow_full else 2)
        
        # Icon symbol (Clock / Hourglass simplified)
        # Draw a circle and hands
        cx = s_draw_x + s_draw_w // 2
        cy = s_draw_y + s_draw_h // 2
        cr = s_draw_w // 3
        pygame.draw.circle(screen, (200, 200, 200), (cx, cy), cr, 2)
        pygame.draw.line(screen, (200, 200, 200), (cx, cy), (cx, cy - cr + 4), 2)
        pygame.draw.line(screen, (200, 200, 200), (cx, cy), (cx + cr - 4, cy), 2)

        # Slow count text
        if not is_slow_full:
            needed = self.max_slow_time_charge - self.slow_time_charge
            count_surf = self.small_font.render(f"{needed}", True, (200, 200, 200))
            screen.blit(count_surf, (s_draw_x + s_draw_w + 5, s_draw_y + s_draw_h // 2 - 10))
        else:
            # Blink "SPACE"
            if (pygame.time.get_ticks() // 500) % 2 == 0:
                space_surf = self.small_font.render("SPACE", True, (100, 0, 255))
                screen.blit(space_surf, (s_draw_x + s_draw_w + 5, s_draw_y + s_draw_h // 2 - 10))

