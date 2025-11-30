import pygame
import sys
from TestLevel.test_level import TestLevel

# tutaj dodajemy elementy
# from objects.game_object import GameObject

WIDTH = 1920
HEIGHT = 1080

FPS = 60

# jak używać spriteów obiektu gry
# game_object = GameObject(10, 10, WIDTH, HEIGHT, "rafal")
# sprite_dict = {"mike": "assets/pictures/default_mike.png"}
# game_object.init_sprites(sprite_dict)
# game_object.set_sprite("mike")

class Game:
    def __init__(self) -> None:
        pygame.init()

        info = pygame.display.Info()
        self.screen = pygame.display.set_mode((info.current_w, info.current_h), pygame.FULLSCREEN | pygame.SCALED)
        self.clock = pygame.time.Clock()
        self.game_state_manager = GameStateManager("start") # <- tutaj podać początkowy poziom

        # =============================================================
        # Tutaj definiowane poziomy np -> self.level1 = Level1(self.screen, self.game_state_manager)

        self.start = Start(self.screen, self.game_state_manager)
        self.test_level = TestLevel(self.screen, self.game_state_manager)


        # uzupełniane nazwami poziomu i wartoscia np self.states = {"level1":self.level1}
        self.states = {"start": self.start, "test_level": self.test_level}

        # =============================================================



    def run(self):
        while True:
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



class Start:
    def __init__(self, display, game_state_manager) -> None:
        self.display = display
        self.game_state_manager = game_state_manager

    def run(self):
        self.display.fill("green")
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.game_state_manager.set_state("test_level")


        # jak wywoływać i rysować elementy 
        # game_object.update()
        # game_object.draw(self.display)




if __name__ == "__main__":
    game = Game()
    game.run()
