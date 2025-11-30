import pygame
import sys

# tutaj dodajemy elementy
from objects.bpm_counter import BPMCounter

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

        self.start = Start(self.screen, self.game_state_manager, self.clock)


        # uzupełniane nazwami poziomu i wartoscia np self.states = {"level1":self.level1}
        self.states = {"start": self.start,}

        # =============================================================



    def run(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
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
    def __init__(self, display, game_state_manager, clock) -> None:
        self.display = display
        self.game_state_manager = game_state_manager
        self.clock = clock

        # Create BPM counter
        self.bpm_counter = BPMCounter(WIDTH - 200, HEIGHT - 50 , WIDTH, HEIGHT, bpm=120)

    def run(self):
        self.display.fill("green")

        # Get delta time in milliseconds
        delta_time = self.clock.get_time()
        
        # Update and draw BPM counter
        self.bpm_counter.update(delta_time)
        self.bpm_counter.draw(self.display)
        
        # Optional: Check if on beat for gameplay mechanics
        if self.bpm_counter.is_on_beat():
            # Player can perform rhythm actions here
            pass




if __name__ == "__main__":
    game = Game()
    game.run()