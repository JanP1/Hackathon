from abc import abstractmethod
import random
import math
import pygame

from objects.player import Player
from objects.ranged_enemy import RangedEnemy
from objects.bpm_counter import BPMCounter
from objects.camera import Camera

# klasa bazowa poziomu, posiada BPM, podstawowy spawner przeciwników, update i draw
class BaseLevel:
    def __init__(self, screen, game_state_manager, clock, bpm: int = 80, path_to_background: str = "assets/pictures/backgrounds/main_background.png") -> None:
        self.name = "Level_Test"
        self.clock = clock
        self.enemies = []

        self.screen = screen
        self.game_state_manager = game_state_manager

        self.WIDTH = self.screen.get_width()
        self.HEIGHT = self.screen.get_height()

        self.initBackground(path_to_background)

        self.player = Player(self.WIDTH//2, self.HEIGHT//2, self.WIDTH, self.HEIGHT, 1, 4096, 4096)

        self.spawn_timer = 0
        self.spawn_interval = 5000

        self.camera = Camera(self.bg_width, self.bg_height, self.WIDTH, self.HEIGHT, box_w=800, box_h=600)
        
        # assign camera to player; ignore type-checker if Player.camera is annotated as None
        self.player.camera = self.camera # type: ignore
        
        self.initBPM(bpm)
        # Provide player's on-beat checker so clicks can detect on-beat in the same frame
        try:
            self.player.set_on_beat_checker(self.bpm_counter.is_on_beat)
        except Exception:
            pass
    

    def initBackground(self, path_to_background):
        # load background
        self.bg = pygame.image.load(path_to_background)
        self.bg_width = self.bg.get_width()
        self.bg_height = self.bg.get_height()


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
        enemy.camera = self.camera # type: ignore
        enemy.map_height = self.bg_width #type: ignore
        enemy.map_width = self.bg_height #type: ignore

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
        Override this method in child classes to add custom leve❯ git push origin player-enemies-scrolling-map-feature
fatal: cannot exec '/usr/bin/ksshaskpass': No such file or directory
Username for 'https://github.com': l mechanics.
        
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
        self.camera.update(self.player)
        
        # Update spawn timer
        self.spawn_timer += delta_time
        if self.spawn_timer >= self.spawn_interval:
            self.spawnEnemies()
            self.spawn_timer = 0
        
        # Handle wave-enemy interactions (damage on ring contact)
        if hasattr(self.player, 'sound_waves') and self.player.sound_waves:
            for wave in self.player.sound_waves:
                # Ensure we have a hit registry to avoid multi-hitting the same enemy with one wave
                hit_set = wave.setdefault("_hit_ids", set())
                wx, wy = wave.get("pos", (0, 0))
                radius = float(wave.get("radius", 0.0))
                thickness = float(wave.get("thickness", 0.0))
                on_beat = bool(wave.get("on_beat", False))

                # Precompute ring bounds
                half_th = max(1.0, thickness * 0.5)
                inner = max(0.0, radius - half_th)
                outer = radius + half_th

                for enemy in self.enemies:
                    if not (enemy.is_active and enemy.is_alive):
                        continue
                    eid = id(enemy)
                    if eid in hit_set:
                        continue
                    ex, ey = enemy.rect.centerx, enemy.rect.centery
                    dx = ex - wx
                    dy = ey - wy
                    dist = (dx*dx + dy*dy) ** 0.5

                    # Simple ring-overlap check; enemies have some size, so be a bit forgiving
                    enemy_pad = max(enemy.rect.width, enemy.rect.height) * 0.25
                    if inner - enemy_pad <= dist <= outer + enemy_pad:
                        # Compute damage: on-beat → full health; otherwise half of MAX health (ceil)
                        if on_beat:
                            dmg = enemy.current_health
                        else:
                            dmg = int(math.ceil(enemy.max_health / 2))
                        if dmg > 0:
                            enemy.take_damage(dmg)
                        hit_set.add(eid)

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
        # draw background
        self.screen.blit(self.bg, (-self.camera.x, -self.camera.y))
        
        self.player.draw(self.screen)

        # draw hitbox for player
        # pygame.draw.rect(
        #     self.screen,
        #     (255, 0, 0),
        #     self.camera.apply(self.player.rect),  # apply camera offset
        #     2
        # )

        for enemy in self.enemies:
            if enemy.is_active and enemy.is_alive:
                enemy.draw(self.screen)

        self.bpm_counter.draw(self.screen)


    def run(self):
        self.update()
        self.draw()
