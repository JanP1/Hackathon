import pygame
import sys
import ctypes
ctypes.windll.user32.SetProcessDPIAware()

# tutaj dodajemy elementy
from objects.bpm_counter import BPMCounter
from objects.ranged_enemy import RangedEnemy
from objects.player import Player

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
        self.bpm_counter = BPMCounter(WIDTH - 200, HEIGHT - 50, WIDTH, HEIGHT, bpm=120)
        
        # Create player
        self.player = Player(WIDTH // 2, HEIGHT // 2, WIDTH, HEIGHT, "player")
        # Wstrzykujemy checker beatu, by Player mógł sprawdzać on-beat w momencie kliknięcia
        if hasattr(self.player, 'set_on_beat_checker'):
            self.player.set_on_beat_checker(self.bpm_counter.is_on_beat)
        
        # Create enemies
        self.enemies = []
        
        # Ranged enemy - attacks every 4 beats
        ranged = RangedEnemy(600, 400, WIDTH, HEIGHT)
        ranged.set_attack_cooldown(4)
        self.enemies.append(ranged)
        
        # Track last beat to avoid multiple triggers
        self.last_beat_time = 0
        self.beat_triggered = False

    def run(self):
        self.display.fill("green")

        # Get delta time in milliseconds
        delta_time = self.clock.get_time()
        
        # Update and draw BPM counter
        self.bpm_counter.update(delta_time)
        self.bpm_counter.draw(self.display)
        
        # Update player
        self.player.update()
        
        # Check if on beat for enemy attacks
        if self.bpm_counter.is_on_beat():
            if not self.beat_triggered:
                self.beat_triggered = True
                # Trigger beat for player (allows beat-click bonus)
                self.player.on_beat()
                # Trigger beat for all enemies
                for enemy in self.enemies:
                    enemy.on_beat()
        else:
            self.beat_triggered = False
        
        # Update enemies
        for enemy in self.enemies:
            enemy.update(delta_time)
            
            # Set target to player position
            if isinstance(enemy, RangedEnemy):
                enemy.set_target(self.player.rect.centerx, self.player.rect.centery)

                # Sprawdź kolizje pocisków z graczem i zadaj obrażenia
                for projectile in enemy.projectiles[:]:
                    px = int(projectile.get('x', 0))
                    py = int(projectile.get('y', 0))
                    if self.player.rect.collidepoint(px, py):
                        self.player.take_damage(projectile.get('damage', 0))
                        enemy.projectiles.remove(projectile)
        
        # Draw player
        self.player.draw(self.display)
        
        # Draw enemies
        for enemy in self.enemies:
            enemy.draw(self.display)
        
        # Draw instructions
        font = pygame.font.Font(None, 36)
        text = font.render("WASD to move, Click to attack", True, (255, 255, 255))
        self.display.blit(text, (50, 50))




if __name__ == "__main__":
    game = Game()
    game.run()