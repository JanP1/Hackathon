import pygame
import sys

#=========== SCENES IMPORTS ============
from scenes.start import Start
from scenes.base_level import BaseLevel
from scenes.level_1 import Level_1


WIDTH = 1920
HEIGHT = 1080

FPS = 60


class Game:
    def __init__(self) -> None:
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.game_state_manager = GameStateManager("start") # <- tutaj podać początkowy poziom

        # =============================================================
        # Tutaj definiowane poziomy np -> self.level1 = Level1(self.screen, self.game_state_manager)

        self.start_scene = Start(self.screen, self.game_state_manager, self.clock)
        self.level_test_scene = BaseLevel(self.screen, self.game_state_manager, self.clock)
        self.level_1 = Level_1(self.screen, self.game_state_manager, self.clock)

        # uzupełniane nazwami poziomu i wartoscia np self.states = {"level1":self.level1}
        self.states = {
            "start": self.start_scene,
            "level_test": self.level_test_scene,
            "level_1": self.level_1
        }

        # =============================================================


    def run(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

            self.game_state_manager.set_state("level_1")

            self.states[self.game_state_manager.get_state()].run()

            pygame.display.update()
            
            self.clock.tick(FPS)


class GameStateManager:
    def __init__(self, current_state) -> None:
        self.current_state = current_state

    def get_state(self):
        return self.current_state

    def set_state(self, current_state):
        self.current_state = current_state


if __name__ == "__main__":
    game = Game()
    game.run()