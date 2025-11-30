import pygame
from objects.game_object import GameObject

class Projectile(GameObject):
    def __init__(self, x_pos: int, y_pos: int, SCREEN_W: int, SCREEN_H: int, 
                 vx: float, vy: float, damage: int, scale: float = 0.1):
        super().__init__(x_pos, y_pos, SCREEN_W, SCREEN_H, scale, "projectile")
        
        self.vx = vx
        self.vy = vy
        self.damage = damage
        self.is_active = True
        
        # Create a simple circular sprite if needed
        self.radius = 5
        self.color = (255, 255, 0)  # Yellow
    
    def update(self, delta_time: float = 0.0):
        """
        Move the projectile.
        delta_time jest w sekundach.
        """
        self.rect.x += self.vx * delta_time # type: ignore
        self.rect.y += self.vy * delta_time # type: ignore
        
        # Deactivate if off screen
        if (self.rect.x < 0 or self.rect.x > self.SCREEN_W or
            self.rect.y < 0 or self.rect.y > self.SCREEN_H):
            self.is_active = False
    
    def draw(self, screen, camera=None):
        """Draw the projectile."""
        if not self.is_active:
            return
        
        cam_x, cam_y = 0, 0
        if camera is not None:
            cam_x = self.camera.x
            cam_y = self.camera.y

        pygame.draw.circle(screen, self.color, 
                         (int(self.rect.centerx - cam_x), 
                          int(self.rect.centery - cam_y)), 
                         self.radius)
    
    def check_collision(self, target_rect):
        """Check if projectile collides with target."""
        return self.is_active and self.rect.colliderect(target_rect)