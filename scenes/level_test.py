import pygame

from main import HEIGHT
from objects import ranged_enemy
from objects.player import Player
from objects.ranged_enemy import RangedEnemy
from objects.bpm_counter import BPMCounter


class Level_1:
    def __init__(self, screen, game_state_manager, clock) -> None:
        self.name = "Level1"
        self.clock = clock

        self.enemies = []

        self.screen = screen
        self.game_state_manager = game_state_manager

        self.WIDTH = self.screen.get_width()
        self.HEIGHT = self.screen.get_height()

        self.player = Player(self.WIDTH//2, self.HEIGHT//2, self.WIDTH, self.HEIGHT)
        self.ranged_enemy = RangedEnemy(self.WIDTH//4, self.HEIGHT//4, self.WIDTH, self.HEIGHT, 0.25, self.player)

        self.initBPM()
    

    def initBPM(self):
        self.bpm = 80
        self.bpm_counter = BPMCounter(self.WIDTH - 200, self.HEIGHT - 50, self.WIDTH, self.HEIGHT, bpm = self.bpm)
        self.last_beat_time = 0
        self.beat_triggered = False


    def update(self):    
        self.bpm_counter.update(self.clock.get_time())
        self.player.update()
        
        if self.ranged_enemy.is_active and self.ranged_enemy.is_alive:
            self.ranged_enemy.update()

        if self.bpm_counter.is_on_beat():
            if not self.beat_triggered:
                self.beat_triggered = True
                # ============== TUTAJ ROBIMY METODY on_beat() KAŻDEGO ===============
                # ================ ELEMENTU KTÓRY MA DZIAŁAĆ NA BEAT =================
                if self.ranged_enemy.is_active and self.ranged_enemy.is_alive:
                    self.ranged_enemy.on_beat()
                # ====================================================================
        else:
            self.beat_triggered = False


    def draw(self):
        self.screen.fill("green")
        self.player.draw(self.screen)

        if self.ranged_enemy.is_active and self.ranged_enemy.is_alive:
            self.ranged_enemy.draw(self.screen)
        
        self.bpm_counter.draw(self.screen)


    def run(self):
        self.update()
        self.draw()
