import pygame
from pathlib import Path
from objects.enemy import Enemy

class MeleeEnemy(Enemy):
    def __init__(self, x_pos: int, y_pos: int, SCREEN_W: int, SCREEN_H: int, scale: float, target):
        super().__init__(x_pos, y_pos, SCREEN_W, SCREEN_H, scale,
                        name="melee_enemy", max_health=60, 
                        attack_cooldown=2, damage=10)
        
        self.target = target
        self.move_speed = 200.0
        self.attack_range = 60
        
        # Load animation
        self.frames = []
        self.current_frame_idx = 0
        self.animation_timer = 0.0
        self.frame_duration = 0.05 # seconds per frame
        
        # Load walk animation
        base_path = Path("assets/pictures/walk_animation")
        if base_path.exists():
            # Sort files to ensure correct order
            files = sorted([f for f in base_path.iterdir() if f.suffix.lower() == '.png'])
            for f in files:
                try:
                    img = pygame.image.load(str(f)).convert_alpha()
                    # Scale
                    if scale != 1.0:
                        w = int(img.get_width() * scale)
                        h = int(img.get_height() * scale)
                        img = pygame.transform.scale(img, (w, h))
                    self.frames.append(img)
                except Exception as e:
                    print(f"Error loading frame {f}: {e}")
        
        if not self.frames:
            # Fallback to default sprite if no frames found
            self.frames.append(self.sprite)
            
        self.sprite = self.frames[0]
        # Update rect size but keep position
        old_x, old_y = self.rect.x, self.rect.y
        self.rect = self.sprite.get_rect()
        self.rect.x = old_x
        self.rect.y = old_y
        
        self.sprite_flipped = pygame.transform.flip(self.sprite, True, False)
        
        self.damage_cooldown = 0.0
        self.damage_interval = 1.0 # seconds

    def update_behavior(self, delta_time: float):
        dt_sec = delta_time / 1000.0
        
        if self.damage_cooldown > 0:
            self.damage_cooldown -= dt_sec
        
        # Animation
        if self.frames:
            self.animation_timer += dt_sec
            if self.animation_timer >= self.frame_duration:
                self.animation_timer = 0
                self.current_frame_idx = (self.current_frame_idx + 1) % len(self.frames)
                self.sprite = self.frames[self.current_frame_idx]
                self.sprite_flipped = pygame.transform.flip(self.sprite, True, False)
            
        # Movement
        if self.target:
            tx, ty = self.target.rect.center
            sx, sy = self.rect.center
            
            dx = tx - sx
            dy = ty - sy
            dist = (dx**2 + dy**2)**0.5
            
            if dist > self.attack_range:
                if dist > 0:
                    move_x = (dx / dist) * self.move_speed * dt_sec
                    move_y = (dy / dist) * self.move_speed * dt_sec
                    self.rect.x += move_x
                    self.rect.y += move_y
                    
                self.facing_right = dx > 0
            else:
                # Attack logic here if continuous
                if self.damage_cooldown <= 0:
                    self.on_attack()

    def on_attack(self):
        # Check distance
        if self.target:
            tx, ty = self.target.rect.center
            sx, sy = self.rect.center
            dist = ((tx-sx)**2 + (ty-sy)**2)**0.5
            
            if dist <= self.attack_range + 30: # Tolerance
                if self.damage_cooldown <= 0:
                    print(f"{self.name} melee attack!")
                    # Pass source_pos for knockback
                    self.target.take_damage(self.damage, source_pos=self.rect.center)
                    self.damage_cooldown = self.damage_interval

    def draw_attack(self, screen):
        # Visual feedback for attack could be added here
        pass
