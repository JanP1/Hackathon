import pygame
import math
from pathlib import Path
from objects.enemy import Enemy
from objects.projectile import Projectile

class RangedEnemy(Enemy):
    def __init__(self, x_pos: int, y_pos: int, SCREEN_W: int, SCREEN_H: int, scale: float, target):
        super().__init__(x_pos, y_pos, SCREEN_W, SCREEN_H, scale,
                        name="ranged_enemy", max_health=30, 
                        attack_cooldown=4, damage=10)
        
        self.rect.width = self.rect.width
        self.rect.height = self.rect.height

        self.map_width = SCREEN_W
        self.map_height = SCREEN_H

        self.projectiles = []
        self.move_speed = 150.0  # px/s
        self.target = target

        self.target_x = None
        self.target_y = None

        self.keep_distance = 300
        self.projectile_speed = 450.0 # px/s

        self.is_alive = True
        self.is_active = True

        # Load animation (Guitar Hit)
        self.frames = []
        self.current_frame_idx = 0
        self.animation_timer = 0.0
        self.frame_duration = 0.1 # seconds per frame
        
        base_path = Path("assets/pictures/guitar_hit_animation")
        if base_path.exists():
            files = sorted([f for f in base_path.iterdir() if f.suffix.lower() == '.png'])
            for f in files:
                try:
                    img = pygame.image.load(str(f)).convert_alpha()
                    if scale != 1.0:
                        w = int(img.get_width() * scale)
                        h = int(img.get_height() * scale)
                        img = pygame.transform.scale(img, (w, h))
                    self.frames.append(img)
                except Exception as e:
                    print(f"Error loading frame {f}: {e}")
        
        if not self.frames:
            # Fallback to default sprite if no frames found
            # Resize to avoid giant cubes
            self.sprite = pygame.transform.scale(self.sprite, (50, 50))
            self.frames.append(self.sprite)
            
        self.sprite = self.frames[0]
        # Update rect size but keep position
        old_x, old_y = self.rect.x, self.rect.y
        self.rect = self.sprite.get_rect()
        self.rect.x = old_x
        self.rect.y = old_y
        self.sprite_flipped = pygame.transform.flip(self.sprite, True, False)
    

    def projectile_check_collision(self):
        """Check if any projectiles hit the target."""
        for projectile in self.projectiles[:]:
            if projectile.check_collision(self.target.rect):
                self.target.take_damage(projectile.damage)
                print("PLAYER HIT")
                self.projectiles.remove(projectile)
    

    def set_target(self):
        """Set target to keep distance from (e.g., player position)."""
        self.target_x = self.target.rect.centerx
        self.target_y = self.target.rect.centery
    
    
    def update_behavior(self, delta_time: float = 0.0):
        """
        Move to keep distance from target, update projectiles.
        delta_time jest w milisekundach, przeliczamy na sekundy.
        """
        dt_sec = delta_time / 1000.0
        
        # Animation
        if self.frames:
            self.animation_timer += dt_sec
            if self.animation_timer >= self.frame_duration:
                self.animation_timer = 0
                self.current_frame_idx = (self.current_frame_idx + 1) % len(self.frames)
                self.sprite = self.frames[self.current_frame_idx]
                self.sprite_flipped = pygame.transform.flip(self.sprite, True, False)

        # Keep distance from target - REMOVED CONTINUOUS MOVEMENT
        # Now handled by Enemy.on_beat dash
        # We might want to adjust dash direction in on_beat for ranged enemies to keep distance?
        # For now, let's stick to "zigzag towards player" as requested, or maybe modify on_beat for Ranged.
        
        # Update projectiles and remove inactive ones
        for projectile in self.projectiles[:]:
            projectile.update(dt_sec) # Przekazujemy dt w sekundach
            if not projectile.is_active:
                self.projectiles.remove(projectile)
        self.projectile_check_collision()
    
    def on_beat(self):
        # Override on_beat to keep distance instead of just rushing
        if not self.is_alive:
            return
        
        self.beat_counter += 1
        
        # --- Movement on Beat (Zigzag Dash) ---
        target_pos = None
        if hasattr(self, "target") and self.target:
            target_pos = self.target.rect.center
        elif hasattr(self, "player") and self.player:
             target_pos = self.player.rect.center
             
        if target_pos:
            tx, ty = target_pos
            cx, cy = self.rect.center
            dx = tx - cx
            dy = ty - cy
            dist = math.hypot(dx, dy)
            
            if dist > 0:
                # Base direction
                dir_vec = pygame.math.Vector2(dx/dist, dy/dist)
                
                # If too close, back away
                if dist < self.keep_distance:
                    dir_vec = -dir_vec
                elif dist < self.keep_distance + 100:
                    # Sweet spot - strafe only
                    dir_vec = pygame.math.Vector2(0, 0)
                
                # Perpendicular vector for zigzag
                # If strafing (dir_vec ~ 0), use perpendicular to target direction
                if dir_vec.length() == 0:
                     base_dir = pygame.math.Vector2(dx/dist, dy/dist)
                     perp_vec = pygame.math.Vector2(-base_dir.y, base_dir.x)
                     final_vec = perp_vec * self.zigzag_direction
                else:
                    perp_vec = pygame.math.Vector2(-dir_vec.y, dir_vec.x)
                    side_strength = 0.8
                    final_vec = dir_vec + perp_vec * (side_strength * self.zigzag_direction)
                
                if final_vec.length() > 0:
                    final_vec = final_vec.normalize()
                
                self.dash_vector = final_vec * self.dash_speed
                self.dash_timer = self.dash_duration
                
                # Flip zigzag
                self.zigzag_direction *= -1
        
        # Attack on cooldown interval
        if self.beat_counter >= self.attack_cooldown:
            self.beat_counter = 0
            self.trigger_attack()

    def on_attack(self):
        """Shoot a projectile towards target."""
        # Check if visible on camera (with margin)
        if self.camera:
            margin = 200
            cam_rect = pygame.Rect(
                self.camera.x - margin, 
                self.camera.y - margin, 
                self.camera.screen_width + margin * 2, 
                self.camera.screen_height + margin * 2
            )
            if not self.rect.colliderect(cam_rect):
                return

        # print(f"{self.name} shoots projectile! Damage: {self.damage}")
        
        # Calculate direction to target
        if self.target_x is not None and self.target_y is not None:
            dx = self.target_x - self.rect.centerx
            dy = self.target_y - self.rect.centery
            distance = (dx**2 + dy**2) ** 0.5
        else:
            # Jeśli nie ma celu, strzel w kierunku, w którym patrzysz
            dx = 1 if self.facing_right else -1
            dy = 0
        
        # Create projectile as GameObject
        projectile = Projectile(
            self.rect.centerx, 
            self.rect.centery,
            self.SCREEN_W,
            self.SCREEN_H,
            dx, dy, # Przekazujemy wektor kierunku, a nie finalną prędkość
            self.damage,
            speed=self.projectile_speed, # Przekazujemy prędkość jako nazwany argument
            map_width=self.map_width,
            map_height=self.map_height
        )
        projectile.camera = self.camera  # Pass camera reference
        self.projectiles.append(projectile)
    
    def draw_attack(self, screen):
        print("drawing ranged enemy attack")
    
    def draw(self, screen):
        """Draw enemy and projectiles."""
        super().draw(screen)
        
        # Draw all projectiles
        for projectile in self.projectiles:
            projectile.draw(screen, self.camera)