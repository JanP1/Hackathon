import pygame
from pathlib import Path
from objects.enemy import Enemy
from objects.projectile import Projectile

class RangedEnemy(Enemy):
    def __init__(self, x_pos: int, y_pos: int, SCREEN_W: int, SCREEN_H: int, scale: float, target):
        super().__init__(x_pos, y_pos, SCREEN_W, SCREEN_H, scale,
                        name="ranged_enemy", max_health=30, 
                        attack_cooldown=4, damage=20)
        
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

        # Keep distance from target
        if self.target_x is not None and self.target_y is not None:
            dx = self.rect.centerx - self.target_x
            dy = self.rect.centery - self.target_y
            distance = (dx**2 + dy**2) ** 0.5
            
            if distance > 0:
                if distance < self.keep_distance:
                    dx = (dx / distance) * self.move_speed * dt_sec
                    dy = (dy / distance) * self.move_speed * dt_sec
                    self.rect.x += dx
                    self.rect.y += dy
                elif distance > self.keep_distance + 50:
                    dx = -(dx / distance) * self.move_speed * dt_sec
                    dy = -(dy / distance) * self.move_speed * dt_sec
                    self.rect.x += dx
                    self.rect.y += dy
                
                self.facing_right = (self.target_x - self.rect.centerx) > 0
        
        # Update projectiles and remove inactive ones
        for projectile in self.projectiles[:]:
            projectile.update(dt_sec) # Przekazujemy dt w sekundach
            if not projectile.is_active:
                self.projectiles.remove(projectile)
        self.projectile_check_collision()
    
    
    def on_attack(self):
        """Shoot a projectile towards target."""
        print(f"{self.name} shoots projectile! Damage: {self.damage}")
        
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