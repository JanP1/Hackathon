import pygame


class Start:
    def __init__(self, display, game_state_manager, clock) -> None:
        self.display = display
        self.game_state_manager = game_state_manager
        self.clock = clock

    def update(self):
       print("chuj")
       
        
    def draw(self):
        self.display.fill("green")

        # Get delta time in milliseconds
        delta_time = self.clock.get_time()
        
        
        # Draw instructions
        font = pygame.font.Font(None, 36)
        text = font.render("WASD to move, Click to attack", True, (255, 255, 255))
        self.display.blit(text, (50, 50))


    def run(self):
        self.update()
        self.draw()