import pygame
from objects.game_object import GameObject

class Player(GameObject):
    def __init__(self, x, y, SCREEN_W, SCREEN_H, MAP_HEIGHT, MAP_WIDTH):
        super().__init__(x, y, SCREEN_W, SCREEN_H, "player")
        self.map_height = MAP_HEIGHT
        self.map_width = MAP_WIDTH
        self.frames = []
        for i in range(25):
            img = pygame.image.load(
                f"assets/pictures/walk_animation/mariachi_walk{i:04}.png"
            ).convert_alpha()
            self.frames.append(img)
        self.index = 0
        self.speed = 15

    def update(self, keys):
        # ... your existing update logic ...
        moved = False
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.rect.x -= self.speed
            self.facing_right = False
            moved = True
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.rect.x += self.speed
            self.facing_right = True
            moved = True
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.rect.y -= self.speed
            moved = True
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.rect.y += self.speed
            moved = True

        if moved:
            self.index = (self.index + 0.25) % len(self.frames)
            

        frame = self.frames[int(self.index)]
        self.sprite = frame if self.facing_right else pygame.transform.flip(frame, True, False)

        # Clamp to screen
        self.rect.x = max(0, min(self.rect.x, self.map_width - self.rect.width))
        self.rect.y = max(0, min(self.rect.y, self.map_height - self.rect.height))

    # --- override draw to always show rect ---
    def draw(self, screen):
        # draw sprite centered on hitbox
        sprite_rect = self.sprite.get_rect()
        sprite_rect.center = self.rect.center
        screen.blit(self.sprite, sprite_rect)

        # draw hitbox rectangle
        pygame.draw.rect(screen, (255, 0, 0), self.rect, 2)
