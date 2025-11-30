import pygame
from objects.enemy import Enemy
from objects.projectile import Projectile

class RangedEnemy(Enemy):
    def __init__(self, x_pos: int, y_pos: int, SCREEN_W: int, SCREEN_H: int, scale: float, target):
        super().__init__(x_pos, y_pos, SCREEN_W, SCREEN_H, scale,
                        name="ranged_enemy", max_health=60, 
                        attack_cooldown=4, damage=20)
        
        self.rect.width = self.rect.width
        self.rect.height = self.rect.height

        self.projectiles = []
        self.move_speed = 150.0  # px/s
        self.target = target

        self.target_x = None
        self.target_y = None

        self.keep_distance = 300
        self.projectile_speed = 450.0 # px/s

        self.is_alive = True
        self.is_active = True
    

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
    
    
    def on_attack(self):
        """Shoot a projectile towards target."""
        print(f"{self.name} shoots projectile! Damage: {self.damage}")
        
        # Calculate direction to target
        if self.target_x is not None and self.target_y is not None:
            dx = self.target_x - self.rect.centerx
            dy = self.target_y - self.rect.centery
            distance = (dx**2 + dy**2) ** 0.5
            
            if distance > 0:
                vx = (dx / distance) * self.projectile_speed
                vy = (dy / distance) * self.projectile_speed
            else:
                vx = self.projectile_speed if self.facing_right else -self.projectile_speed
                vy = 0
        else:
            vx = self.projectile_speed if self.facing_right else -self.projectile_speed
            vy = 0
        
        # Create projectile as GameObject
        projectile = Projectile(
            self.rect.centerx, 
            self.rect.centery,
            self.SCREEN_W,
            self.SCREEN_H,
            vx, vy,
            self.damage
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