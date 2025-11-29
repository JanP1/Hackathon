import pygame
import sys

class TestLevel:
    def __init__(self, display, game_state_manager) -> None:
        self.display = display
        self.game_state_manager = game_state_manager

    def run(self):
        self.display.fill("red")
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.game_state_manager.set_state("start")


        # jak wywoływać i rysować elementy 
        # game_object.update()
        # game_object.draw(self.display)
