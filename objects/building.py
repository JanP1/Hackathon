import pygame
from objects.game_object import GameObject

class Building(GameObject):
    def __init__(self, x_pos: int, y_pos: int, SCREEN_W: int, SCREEN_H: int, scale: float = 1.0):
        super().__init__(x_pos, y_pos, SCREEN_W, SCREEN_H, scale, "building")
        
        # Load sprite
        try:
            self.sprite = pygame.image.load("assets/pictures/buildings/house.png").convert_alpha()
        except FileNotFoundError:
            print("Warning: assets/pictures/buildings/house.png not found, using default.")
            # Fallback is handled by GameObject default sprite, but we want to ensure we have something
            pass

        if self.scale != 1.0:
            w = self.sprite.get_width()
            h = self.sprite.get_height()
            self.sprite = pygame.transform.scale(self.sprite, (int(w * self.scale), int(h * self.scale)))
            
        self.rect = self.sprite.get_rect()
        self.rect.topleft = (x_pos, y_pos)
        
        # Calculate collision rect based on visible pixels (bounding box of non-transparent pixels)
        # get_bounding_rect() returns a Rect relative to the sprite's top-left (0,0)
        visible_rect = self.sprite.get_bounding_rect()
        
        # Translate to world coordinates
        self.collision_rect = visible_rect.copy()
        self.collision_rect.x += self.rect.x
        self.collision_rect.y += self.rect.y

    def update(self):
        pass
        
    def draw(self, screen):
        super().draw(screen)
        # Debug collision rect
        # cam_x = self.camera.x if self.camera else 0
        # cam_y = self.camera.y if self.camera else 0
        # r = self.collision_rect.move(-cam_x, -cam_y)
        # pygame.draw.rect(screen, (255, 0, 0), r, 2)
