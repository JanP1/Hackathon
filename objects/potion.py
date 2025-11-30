import pygame
from objects.game_object import GameObject

class Potion(GameObject):
    def __init__(self, x, y, screen_w, screen_h):
        super().__init__(x, y, screen_w, screen_h, scale=0.5, name="potion")
        # Simple visual: green circle or load sprite
        self.rect = pygame.Rect(x, y, 30, 30)
        self.heal_amount = 50
        
    def draw(self, screen):
        cam_x = self.camera.x if self.camera else 0
        cam_y = self.camera.y if self.camera else 0
        
        # Draw potion
        pygame.draw.circle(screen, (0, 255, 0), (self.rect.centerx - cam_x, self.rect.centery - cam_y), 10)
        pygame.draw.circle(screen, (255, 255, 255), (self.rect.centerx - cam_x, self.rect.centery - cam_y), 10, 2)

    def update(self):
        pass
