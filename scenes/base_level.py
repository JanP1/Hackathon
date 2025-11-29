from abc import abstractmethod
import random

from objects.player import Player
from objects.ranged_enemy import RangedEnemy
from objects.bpm_counter import BPMCounter

# klasa bazowa poziomu, posiada BPM, podstawowy spawner przeciwników, update i draw
class BaseLevel:
    def __init__(self, screen, game_state_manager, clock, bpm: int = 80) -> None:
        self.name = "Level_Test"
        self.clock = clock
        self.enemies = []

        self.screen = screen
        self.game_state_manager = game_state_manager

        self.WIDTH = self.screen.get_width()
        self.HEIGHT = self.screen.get_height()

        self.player = Player(self.WIDTH//2, self.HEIGHT//2, self.WIDTH, self.HEIGHT)

        self.spawn_timer = 0
        self.spawn_interval = 5000

        self.initBPM(bpm)
    
    @abstractmethod
    def spawnEnemies(self):
        """Spawn an enemy at a random off-screen position."""
        # Randomly choose which side to spawn from (0=top, 1=right, 2=bottom, 3=left)
        side = random.randint(0, 3)

        if side == 0:  # Top
            x = random.randint(0, self.WIDTH)
            y = -50
        elif side == 1:  # Right
            x = self.WIDTH + 50
            y = random.randint(0, self.HEIGHT)
        elif side == 2:  # Bottom
            x = random.randint(0, self.WIDTH)
            y = self.HEIGHT + 50
        else:  # Left
            x = -50
            y = random.randint(0, self.HEIGHT)
        
        enemy = RangedEnemy(x, y, self.WIDTH, self.HEIGHT, 0.25, self.player)
        self.enemies.append(enemy)


    def initBPM(self, bpm: int = 80):
        self.bpm = bpm
        self.bpm_counter = BPMCounter(self.WIDTH - 200, self.HEIGHT - 50, self.WIDTH, self.HEIGHT, bpm = self.bpm)
        self.last_beat_time = 0
        self.beat_triggered = False


    @abstractmethod
    def level_specific_functions(self):
        """
        Placeholder for level-specific functionality.
        Override this method in child classes to add custom level mechanics.
        
        Examples:
        - Special enemy spawn patterns
        - Level-specific obstacles
        - Custom power-ups
        - Boss mechanics
        - Environmental hazards
        """
        pass


    def update(self):    
        delta_time = self.clock.get_time()
        
        self.bpm_counter.update(delta_time)
        self.level_specific_functions()
        self.player.update()
        
        # Update spawn timer
        self.spawn_timer += delta_time
        if self.spawn_timer >= self.spawn_interval:
            self.spawnEnemies()
            self.spawn_timer = 0
        
        # Update all enemies
        for enemy in self.enemies[:]:
            if enemy.is_active and enemy.is_alive:
                enemy.set_target()
                enemy.update()
            elif not enemy.is_alive:
                self.enemies.remove(enemy)

        if self.bpm_counter.is_on_beat():
            if not self.beat_triggered:
                self.beat_triggered = True
                # ============== TUTAJ ROBIMY METODY on_beat() KAŻDEGO ===============
                # ================ ELEMENTU KTÓRY MA DZIAŁAĆ NA BEAT =================
                for enemy in self.enemies:
                    if enemy.is_active and enemy.is_alive:
                        enemy.on_beat()
                # ====================================================================
        else:
            self.beat_triggered = False


    def draw(self):
        self.screen.fill("green")
        self.player.draw(self.screen)

        for enemy in self.enemies:
            if enemy.is_active and enemy.is_alive:
                enemy.draw(self.screen)
        
        self.bpm_counter.draw(self.screen)


    def run(self):
        self.update()
        self.draw()
