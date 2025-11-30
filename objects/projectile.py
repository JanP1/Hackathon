import pygame
from objects.game_object import GameObject

class Projectile(GameObject):
    def __init__(self, x_pos: int, y_pos: int, SCREEN_W: int, SCREEN_H: int, 
                 direction_x: float, direction_y: float, damage: int, speed: float = 5.0, 
                 map_width: int = None, map_height: int = None, scale: float = 0.1): #type: ignore
        """
        Create a projectile.
        
        Args:
            x_pos, y_pos: Starting position
            SCREEN_W, SCREEN_H: Screen dimensions
            direction_x, direction_y: Direction vector (will be normalized)
            damage: Damage dealt on hit
            speed: Movement speed (pixels per frame)
            map_width, map_height: Map boundaries (if None, uses screen dimensions)
            scale: Sprite scale
        """
        super().__init__(x_pos, y_pos, SCREEN_W, SCREEN_H, scale, "projectile")
        
        # Normalize direction and apply speed
        length = (direction_x**2 + direction_y**2) ** 0.5
        if length > 0:
            self.vx = (direction_x / length) * speed
            self.vy = (direction_y / length) * speed
        else:
            self.vx = speed
            self.vy = 0
        
        self.damage = damage
        self.speed = speed
        self.is_active = True
        
        # Float position for precision
        self.pos_x = float(x_pos)
        self.pos_y = float(y_pos)
        
        # Map boundaries
        self.map_width = map_width if map_width is not None else SCREEN_W
        self.map_height = map_height if map_height is not None else SCREEN_H
        
        # Visual properties
        self.radius = 5
        self.color = (255, 255, 0)  # Yellow
    
    def update(self, delta_time: float = None):
        """
        Move the projectile.
        delta_time jest w sekundach.
        """
        if delta_time is None:
            delta_time = self.time_manager.dt

        self.pos_x += self.vx * delta_time
        self.pos_y += self.vy * delta_time
        
        self.rect.x = int(self.pos_x)
        self.rect.y = int(self.pos_y)
        
        # Deactivate if off map boundaries
        if (self.rect.x < 0 or self.rect.x > self.map_width or
            self.rect.y < 0 or self.rect.y > self.map_height):
            self.is_active = False
    
    def draw(self, screen, camera=None):
        """Draw the projectile."""
        if not self.is_active:
            return
        
        cam_x, cam_y = 0, 0
        if camera is not None:
            cam_x = camera.x
            cam_y = camera.y

        pygame.draw.circle(screen, self.color, 
                         (int(self.rect.centerx - cam_x), 
                          int(self.rect.centery - cam_y)), 
                         self.radius)
    
    def check_collision(self, target_rect):
        """Check if projectile collides with target."""
        return self.is_active and self.rect.colliderect(target_rect)