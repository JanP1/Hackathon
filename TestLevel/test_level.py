import pygame
import sys
from objects.player import Player
from objects.camera import Camera

WIDTH = 1920
HEIGHT = 1080

class TestLevel:
    def __init__(self, display, game_state_manager):
        self.display = display
        self.game_state_manager = game_state_manager

        # load background
        self.bg = pygame.image.load("assets/pictures/backgrounds/main_background.png")
        self.bg_width = self.bg.get_width()
        self.bg_height = self.bg.get_height()

        # spawn player near center
        self.player = Player(WIDTH//2, HEIGHT//2,
                            WIDTH,
                            HEIGHT,
                              4096, # map width
                              4096  # map height
                              )

        # camera with smaller box (800x600)
        self.camera = Camera(self.bg_width, self.bg_height, WIDTH, HEIGHT, box_w=800, box_h=600)

    def run(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                self.game_state_manager.set_state("start")

        # update player
        self.player.update()
        

# In TestLevel.__init__ after creating player and camera
        self.player.camera = self.camera
        # update camera
        self.camera.update(self.player)
        

        # draw
        self.display.blit(self.bg, (-self.camera.x, -self.camera.y))
        #self.display.blit(self.player.sprite, self.camera.apply(self.player.rect))


        # get camera-adjusted rect
        sprite_rect = self.camera.apply(self.player.rect).copy()

        
        # draw the sprite
        self.player.draw(self.display)  # let Player handle sprite flipping, dot, waves


        # checking hitbox
        # draw hitbox rectangle (always red, thickness=2)
        pygame.draw.rect(
            self.display,
            (255, 0, 0),
            self.camera.apply(self.player.rect),  # apply camera offset
            2
        )
