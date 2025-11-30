import pygame
import math
from objects.enemy import Enemy

class KamikazeEnemy(Enemy):
    def __init__(self, x_pos: int, y_pos: int, SCREEN_W: int, SCREEN_H: int, scale: float = 1.0, target=None):
        super().__init__(x_pos, y_pos, SCREEN_W, SCREEN_H, scale, name="kamikaze", max_health=30, attack_cooldown=1, damage=50)
        self.target = target
        
        # References to be set by Game
        self.effects_manager = None
        self.game_enemies = None # List of enemies
        
        # Load sprite
        try:
            self.sprite = pygame.image.load("assets/pictures/default_sprite.png").convert_alpha()
            self.sprite = pygame.transform.scale(self.sprite, (50, 50))
        except Exception as e:
            print(f"Error loading kamikaze sprite: {e}")
            self.sprite = pygame.Surface((50, 50))
            self.sprite.fill((255, 100, 0)) # Orange
            
        self.rect = self.sprite.get_rect()
        self.rect.center = (x_pos, y_pos)
        
        # Movement
        self.jump_distance = 150.0
        
        # Explosion
        self.explosion_radius = 250.0
        self.explosion_damage = 50 # To player
        self.friendly_fire_damage = 100 # To enemies
        
        # Sound
        self.crash_sound = None
        try:
            self.crash_sound = pygame.mixer.Sound("assets/sounds/crash.mp3")
            self.crash_sound.set_volume(0.6)
        except Exception as e:
            print(f"Error loading crash sound: {e}")

    def update_behavior(self, delta_time: float):
        # Check collision with player
        if self.target and self.rect.colliderect(self.target.rect):
            self.explode()

    def on_attack(self):
        # Called on beat
        if not self.target:
            return
            
        # Calculate direction
        tx, ty = self.target.rect.center
        cx, cy = self.rect.center
        dx = tx - cx
        dy = ty - cy
        dist = math.hypot(dx, dy)
        
        if dist > 0:
            # Jump towards player
            jump_dist = min(dist, self.jump_distance)
            move_x = (dx / dist) * jump_dist
            move_y = (dy / dist) * jump_dist
            
            self.rect.x += int(move_x)
            self.rect.y += int(move_y)
            
            # Check collision after move
            if self.rect.colliderect(self.target.rect):
                self.explode()

    def draw_attack(self, screen):
        pass 

    def explode(self):
        if not self.is_alive:
            return
            
        print("Kamikaze Explodes!")
        
        # 1. Damage Player
        if self.target:
            # Check distance or collision
            dist = math.hypot(self.rect.centerx - self.target.rect.centerx, self.rect.centery - self.target.rect.centery)
            # If collided (dist small) or within radius
            if self.rect.colliderect(self.target.rect) or dist < self.explosion_radius * 0.5:
                 self.target.take_damage(self.explosion_damage)

        # 2. Visual Effect (Black Hole)
        if self.effects_manager:
            self.effects_manager.trigger_black_hole(self.rect.center, 1000.0)
            
        # 3. Sound
        if self.crash_sound:
            self.crash_sound.play()
            
        # 4. Friendly Fire
        if self.game_enemies:
            for enemy in self.game_enemies:
                if enemy is self:
                    continue
                if not enemy.is_alive:
                    continue
                    
                ex, ey = enemy.rect.center
                sx, sy = self.rect.center
                d = math.hypot(ex - sx, ey - sy)
                if d < self.explosion_radius:
                    enemy.take_damage(self.friendly_fire_damage, source_pos=(sx, sy))

        # Die
        self.current_health = 0
        self.is_alive = False
