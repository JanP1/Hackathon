import pygame
from objects.enemy import Enemy


class CloseEnemy(Enemy):
    def __init__(self, x_pos: int, y_pos: int, SCREEN_W: int, SCREEN_H: int, scale: float, target):
        """
        Close-range suicide bomber enemy that explodes on contact with player.
        
        Args:
            x_pos, y_pos: Starting position
            SCREEN_W, SCREEN_H: Screen dimensions
            scale: Sprite scale
            target: Player object to chase
        """
        super().__init__(
            x_pos, y_pos, SCREEN_W, SCREEN_H, scale,
            name="close_enemy",
            max_health=40,  # Lower health than ranged
            attack_cooldown=4,  # Dash every 4 beats
            damage=20  # Explosion damage
        )
        
        self.target = target
        self.target_x = None
        self.target_y = None
        self.move_speed = 2  # Normal movement speed
        self.dash_speed = 12  # Fast dash speed during attack
        self.explosion_radius = 80  # Explosion hitbox radius
        self.has_exploded = False
        
        # Dash attack properties
        self.is_dashing = False
        self.dash_duration = 500  # milliseconds
        self.dash_start_time = 0
        self.dash_direction_x = 0
        self.dash_direction_y = 0
        
        # Explosion animation properties
        self.explosion_active = False
        self.explosion_start_time = 0
        self.explosion_duration = 300  # milliseconds
        self.explosion_max_radius = self.explosion_radius
        
        # Sprite scaffolding
        self.sprite_walk = None  # TODO: Load walking sprite
        self.sprite_dash = None  # TODO: Load dash sprite
        self.sprite_explode = None  # TODO: Load explosion sprite frames
        
        # Visual feedback
        self.flash_timer = 0
        self.flash_duration = 100  # Flash red when dashing
    
    
    def set_target(self):
        """Set target position (required by base_level.py)."""
        if self.target is not None:
            self.target_x = self.target.rect.centerx
            self.target_y = self.target.rect.centery
    
    
    def update_behavior(self, delta_time: float = 0):
        """Chase the player and handle dashing."""
        if self.has_exploded or self.explosion_active:
            return
        
        # Update target position
        self.set_target()
        
        if self.target_x is None or self.target_y is None:
            return
        
        # Calculate direction to player
        dx = self.target_x - self.rect.centerx
        dy = self.target_y - self.rect.centery
        distance = (dx**2 + dy**2) ** 0.5
        
        # Update facing direction
        self.facing_right = dx > 0
        
        # Handle dashing
        if self.is_dashing:
            elapsed = pygame.time.get_ticks() - self.dash_start_time
            if elapsed >= self.dash_duration:
                # Stop dashing
                self.is_dashing = False
                self.flash_timer = 0
            else:
                # Continue dash
                self.rect.x += self.dash_direction_x * self.dash_speed
                self.rect.y += self.dash_direction_y * self.dash_speed
                
                # Flash effect during dash
                self.flash_timer = self.flash_duration
        else:
            # Normal movement (slower, tracking player)
            if distance > 0:
                move_x = (dx / distance) * self.move_speed
                move_y = (dy / distance) * self.move_speed
                self.rect.x += move_x
                self.rect.y += move_y
        
        # Check for collision with player
        if self.rect.colliderect(self.target.rect):
            self.trigger_explosion()
    
    
    def on_beat(self):
        """Called on every beat - trigger dash attack every 4th beat."""
        # Call parent's on_beat to handle attack cooldown
        super().on_beat()
    
    
    def on_attack(self):
        """Triggered every 4th beat - perform dash attack towards player."""
        if self.has_exploded or self.explosion_active or self.is_dashing:
            return
        
        print(f"[{self.name}] DASH ATTACK!")
        
        # Update target position
        self.set_target()
        
        if self.target_x is None or self.target_y is None:
            return
        
        # Calculate dash direction (normalized)
        dx = self.target_x - self.rect.centerx
        dy = self.target_y - self.rect.centery
        distance = (dx**2 + dy**2) ** 0.5
        
        if distance > 0:
            self.dash_direction_x = dx / distance
            self.dash_direction_y = dy / distance
        else:
            self.dash_direction_x = 1 if self.facing_right else -1
            self.dash_direction_y = 0
        
        # Start dash
        self.is_dashing = True
        self.dash_start_time = pygame.time.get_ticks()
    
    
    def trigger_explosion(self):
        """Trigger the explosion attack."""
        if self.has_exploded:
            return
        
        print(f"[{self.name}] EXPLOSION!")
        self.explosion_active = True
        self.explosion_start_time = pygame.time.get_ticks()
        self.has_exploded = True
        self.is_dashing = False  # Stop dashing
        
        # Check if player is in explosion radius
        dx = self.target.rect.centerx - self.rect.centerx
        dy = self.target.rect.centery - self.rect.centery
        distance = (dx**2 + dy**2) ** 0.5
        
        if distance <= self.explosion_radius:
            self.target.take_damage(self.damage)
            print(f"[{self.name}] Player hit by explosion for {self.damage} damage!")
        
        # Schedule death after explosion
        self.death_timer = self.explosion_duration
    
    
    def update(self, delta_time: float = 0):
        """Override update to handle explosion timer."""
        # Call parent update (but skip Enemy's update_behavior since we override it)
        if not self.has_exploded:
            self.update_behavior(delta_time)
        
        # Handle death timer after explosion
        if self.has_exploded and hasattr(self, 'death_timer'):
            self.death_timer -= delta_time if delta_time > 0 else 16  # ~60fps
            if self.death_timer <= 0:
                self.is_alive = False
                self.is_active = False
    
    
    def draw_attack(self, screen):
        """Draw explosion effect."""
        if not self.explosion_active:
            return
        
        cam_x, cam_y = self.get_camera_offset()
        
        # Calculate current explosion radius (grows over time)
        elapsed = pygame.time.get_ticks() - self.explosion_start_time
        progress = min(1.0, elapsed / self.explosion_duration)
        current_radius = int(self.explosion_max_radius * progress)
        
        # Draw expanding circle (explosion wave)
        center_x = int(self.rect.centerx - cam_x)
        center_y = int(self.rect.centery - cam_y)
        
        # Outer explosion ring (red)
        pygame.draw.circle(screen, (255, 100, 0), (center_x, center_y), current_radius, 3)
        
        # Inner explosion (orange, fading)
        alpha = int(255 * (1 - progress))
        inner_radius = int(current_radius * 0.7)
        if inner_radius > 0:
            pygame.draw.circle(screen, (255, 150, 0), (center_x, center_y), inner_radius, 2)
        
        # Draw dash trail when dashing (visual feedback)
        if self.is_dashing and not self.has_exploded:
            # Draw motion blur/trail effect
            trail_length = 3
            for i in range(trail_length):
                offset = (trail_length - i) * 10
                trail_x = int(self.rect.centerx - (self.dash_direction_x * offset) - cam_x)
                trail_y = int(self.rect.centery - (self.dash_direction_y * offset) - cam_y)
                alpha = int(100 - (i * 30))
                pygame.draw.circle(screen, (255, 0, 0, alpha), (trail_x, trail_y), 8)
    
    
    def draw(self, screen):
        """Draw enemy with special effects."""
        if not self.is_active:
            return
        
        # Draw sprite (with flash effect when dashing)
        cam_x, cam_y = self.get_camera_offset()
        
        if self.is_dashing and not self.explosion_active:
            # Create red tinted sprite (dash flash)
            flash_surface = self.sprite.copy()
            flash_surface.fill((255, 0, 0, 150), special_flags=pygame.BLEND_ADD)
            current_sprite = flash_surface if self.facing_right else pygame.transform.flip(flash_surface, True, False)
            screen.blit(current_sprite, (self.rect.x - cam_x, self.rect.y - cam_y))
        else:
            # Normal sprite
            super().draw(screen)
        
        # Draw explosion effect and dash trail
        if self.explosion_active or self.is_dashing:
            self.draw_attack(screen)
    
    
    # ========== SPRITE SCAFFOLDING ==========
    # TODO: Implement these methods when sprites are available
    
    def load_sprites(self):
        """Load sprite assets. Call this after creating the enemy."""
        # TODO: Load walking animation frames
        # self.sprite_walk = pygame.image.load('assets/sprites/close_enemy_walk.png')
        
        # TODO: Load dash sprite
        # self.sprite_dash = pygame.image.load('assets/sprites/close_enemy_dash.png')
        
        # TODO: Load explosion animation frames
        # self.sprite_explode = [
        #     pygame.image.load('assets/sprites/explosion_frame1.png'),
        #     pygame.image.load('assets/sprites/explosion_frame2.png'),
        #     pygame.image.load('assets/sprites/explosion_frame3.png'),
        # ]
        pass
    
    
    def set_walk_sprite(self, sprite_path: str):
        """Set the walking sprite."""
        # TODO: Load and set walking sprite
        # self.sprite_walk = pygame.image.load(sprite_path)
        # self.sprite = self.sprite_walk
        pass
    
    
    def set_explosion_sprites(self, sprite_paths: list):
        """Set explosion animation frames."""
        # TODO: Load explosion sprites
        # self.sprite_explode = [pygame.image.load(path) for path in sprite_paths]
        pass