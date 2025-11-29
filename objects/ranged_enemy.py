import pygame
from objects.enemy import Enemy

class RangedEnemy(Enemy):
    def __init__(self, x_pos: int, y_pos: int, SCREEN_W: int, SCREEN_H: int, scale: float, target):
        super().__init__(x_pos, y_pos, SCREEN_W, SCREEN_H, scale,
                        name="ranged_enemy", max_health=60, 
                        attack_cooldown=2, damage=20)
        
        self.rect.width = self.rect.width
        self.rect.height = self.rect.height

        self.projectiles = []
        self.move_speed = 3
        self.target = target

        self.target_x = None
        self.target_y = None

        self.keep_distance = 400  # Keep this distance from target

        self.is_alive = True
        self.is_active = True
    

    def projectile_check_collision(self):
        for projectile in self.projectiles[:]:
            px = int(projectile.get('x', 0))
            py = int(projectile.get('y', 0))

            if self.target.rect.collidepoint(px, py):
                self.target.take_damage(projectile.get('damage', 0))
                print("PLAYER HIT")
                self.projectiles.remove(projectile) 
    

    def set_target(self):
        """Set target to keep distance from (e.g., player position)."""
        self.target_x = self.target.rect.centerx
        self.target_y = self.target.rect.centery
    
    
    def update_behavior(self):
        """Move to keep distance from target, update projectiles."""
        # Keep distance from target
        if self.target_x is not None and self.target_y is not None:
            dx = self.rect.centerx - self.target_x
            dy = self.rect.centery - self.target_y
            distance = (dx**2 + dy**2) ** 0.5
            
            if distance > 0:
                # If too close, move away
                if distance < self.keep_distance:
                    # Move away from target
                    dx = (dx / distance) * self.move_speed
                    dy = (dy / distance) * self.move_speed
                    self.rect.x += dx
                    self.rect.y += dy
                # If too far, move closer
                elif distance > self.keep_distance + 50:
                    # Move towards target
                    dx = -(dx / distance) * self.move_speed
                    dy = -(dy / distance) * self.move_speed
                    self.rect.x += dx
                    self.rect.y += dy
                
                # Update facing direction
                self.facing_right = (self.target_x - self.rect.centerx) > 0
        
        # Update projectile positions
        for projectile in self.projectiles[:]:
            projectile['x'] += projectile['vx']
            projectile['y'] += projectile['vy']
            
            # Remove if off screen
            if (projectile['x'] < 0 or projectile['x'] > self.SCREEN_W or
                projectile['y'] < 0 or projectile['y'] > self.SCREEN_H):
                self.projectiles.remove(projectile)
    
    
    def on_attack(self):
        """Shoot a projectile towards target."""
        print(f"{self.name} shoots projectile! Damage: {self.damage}")
        
        # Calculate direction to target if available
        if self.target_x is not None and self.target_y is not None:
            dx = self.target_x - self.rect.centerx
            dy = self.target_y - self.rect.centery
            distance = (dx**2 + dy**2) ** 0.5
            
            if distance > 0:
                speed = 5
                vx = (dx / distance) * speed
                vy = (dy / distance) * speed
            else:
                vx = 5 if self.facing_right else -5
                vy = 0
        else:
            vx = 5 if self.facing_right else -5
            vy = 0
        
        # Create projectile
        projectile = {
            'x': self.rect.centerx,
            'y': self.rect.centery,
            'vx': vx,
            'vy': vy,
            'damage': self.damage
        }
        self.projectiles.append(projectile)
    
    
    def update(self):
        self.set_target()      
        self.update_behavior()  
        self.projectile_check_collision()

    def draw(self, screen):
        """Draw enemy and projectiles."""
        super().draw(screen)
        
        # Draw projectiles
        for projectile in self.projectiles:
            pygame.draw.circle(screen, (255, 255, 0), 
                             (int(projectile['x']), int(projectile['y'])), 5)