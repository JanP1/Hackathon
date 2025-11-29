import pygame
import sys
from objects.player import Player

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
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.game_state_manager = GameStateManager("start") # <- tutaj podać początkowy poziom

        # =============================================================
        # Tutaj definiowane poziomy np -> self.level1 = Level1(self.screen, self.game_state_manager)

        self.start = Start(self.screen, self.game_state_manager)


        # uzupełniane nazwami poziomu i wartoscia np self.states = {"level1":self.level1}
        self.states = {"start": self.start,}

        # =============================================================



    def run(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
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
        # Initialize player roughly at screen center
        self.player = Player(WIDTH // 2, HEIGHT // 2, WIDTH, HEIGHT, "player")
        # Optionally initialize sounds if you have a guitar sound file
        # self.player.init_sounds({"guitar": "assets/sounds/guitar.wav"})

    def run(self):
        self.display.fill("green")

        # jak wywoływać i rysować elementy 
        # game_object.update()
        # game_object.draw(self.display)
        self.player.update()
        self.player.draw(self.display)




if __name__ == "__main__":
    game = Game()
    game.run()
