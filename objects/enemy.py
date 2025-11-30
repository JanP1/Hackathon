import pygame
import math
from objects.game_object import GameObject
from abc import abstractmethod

class Enemy(GameObject):
    def __init__(self, x_pos: int, y_pos: int, SCREEN_W: int, SCREEN_H: int, scale: float = 1,  
                 name: str = "enemy", max_health: int = 100, 
                 attack_cooldown: int = 4, damage: int = 10):
        """
        Base Enemy class with beat-based attack system.
        
        Args:
            x_pos: X position
            y_pos: Y position
            SCREEN_W: Screen width
            SCREEN_H: Screen height
            name: Enemy name
            max_health: Maximum health
            attack_cooldown: Attack every Nth beat (e.g., 4 = every 4th beat)
            damage: Damage dealt per attack
        """
        super().__init__(x_pos, y_pos, SCREEN_W, SCREEN_H, scale, name)
        
        # Health system
        self.max_health = max_health
        self.current_health = max_health
        self.is_alive = True
        
        # Attack system (beat-based)
        self.attack_cooldown = attack_cooldown  # Attack every Nth beat
        self.beat_counter = 0  # Counts beats
        self.damage = damage
        self.is_attacking = False
        self.attack_animation_time = 0
        self.attack_duration = 200  # milliseconds
        
        # Default to active
        self.is_active = True

        # Feedback & Physics
        self.damage_tint_timer = 0.0
        self.knockback_velocity = pygame.math.Vector2(0, 0)
        self.knockback_friction = 0.9
    
    
    def take_damage(self, amount: int, source_pos: tuple[int, int] = None):
        """Take damage and check if enemy dies."""
        if not self.is_alive:
            return
        
        self.current_health -= amount
        
        # Visual feedback
        self.damage_tint_timer = 200.0 # ms

        # Knockback
        if source_pos:
            sx, sy = source_pos
            cx, cy = self.rect.center
            dx = cx - sx
            dy = cy - sy
            dist = math.hypot(dx, dy)
            if dist > 0:
                force = 15.0 # Knockback strength
                self.knockback_velocity = pygame.math.Vector2(dx/dist * force, dy/dist * force)

        if self.current_health <= 0:
            self.current_health = 0
            self.is_alive = False
            self.on_death()
    
    
    def heal(self, amount: int):
        """Heal the enemy."""
        if not self.is_alive:
            return
        
        self.current_health = min(self.current_health + amount, self.max_health)
    
    
    def on_beat(self):
        """Called when a beat hits. Handles attack timing."""
        if not self.is_alive:
            return
        
        self.beat_counter += 1
        
        # Attack on cooldown interval
        if self.beat_counter >= self.attack_cooldown:
            self.beat_counter = 0
            self.trigger_attack()
    
    
    def trigger_attack(self):
        """Trigger an attack."""
        if not self.is_alive:
            return
        
        self.is_attacking = True
        self.attack_animation_time = self.attack_duration
        self.on_attack()
    
    
    def set_attack_cooldown(self, cooldown: int):
        """Change the attack cooldown."""
        self.attack_cooldown = max(1, cooldown)
    
    
    def get_health_percentage(self) -> float:
        """Get health as percentage (0.0 to 1.0)."""
        return self.current_health / self.max_health
    
    
    def update(self, delta_time: float = None):
        """Update enemy state."""
        if not self.is_alive:
            return
        
        if delta_time is None:
            delta_time = self.time_manager.dt_ms
        
        # Update feedback timers
        if self.damage_tint_timer > 0:
            self.damage_tint_timer = max(0, self.damage_tint_timer - delta_time)

        # Apply knockback
        if self.knockback_velocity.length_squared() > 0.1:
            self.rect.x += int(self.knockback_velocity.x)
            self.rect.y += int(self.knockback_velocity.y)
            self.knockback_velocity *= self.knockback_friction
            if self.knockback_velocity.length_squared() < 0.1:
                self.knockback_velocity = pygame.math.Vector2(0, 0)

        # Update attack animation
        if self.is_attacking:
            self.attack_animation_time -= delta_time
            if self.attack_animation_time <= 0:
                self.is_attacking = False
                self.attack_animation_time = 0
        
        # Call behavior update
        self.update_behavior(delta_time)
    
    
    def draw(self, screen):
        """Draw the enemy and health bar."""
        if not self.is_active:
            return
        
        # Draw sprite with tint if damaged
        if self.damage_tint_timer > 0:
            # Create a tinted copy
            tinted_sprite = self.sprite.copy()
            # Fill with red, using special flags to keep alpha
            tinted_sprite.fill((255, 0, 0, 100), special_flags=pygame.BLEND_RGBA_MULT)
            
            cam_x, cam_y = 0, 0
            if hasattr(self, "camera") and self.camera is not None:
                cam_x = self.camera.x
                cam_y = self.camera.y
            
            screen.blit(tinted_sprite, (self.rect.x - cam_x, self.rect.y - cam_y))
        else:
            super().draw(screen)
        
        # Draw health bar
        self.draw_health_bar(screen)
        
        # Draw attack indicator if attacking
        if self.is_attacking:
            self.draw_attack(screen)
    
    
    def draw_health_bar(self, screen):
        """Draw health bar above enemy."""
        cam_x, cam_y = 0, 0
        if hasattr(self, "camera") and self.camera is not None:
            cam_x = self.camera.x
            cam_y = self.camera.y

        bar_width = 50
        bar_height = 5
        bar_x = self.rect.centerx - bar_width // 2 - cam_x
        bar_y = self.rect.top - 10 - cam_y
        
        # Background (red)
        pygame.draw.rect(screen, (255, 0, 0), 
                        (bar_x, bar_y, bar_width, bar_height))
        
        # Foreground (green)
        health_width = int(bar_width * self.get_health_percentage())
        pygame.draw.rect(screen, (0, 255, 0), 
                        (bar_x, bar_y, health_width, bar_height))
        
        # Border
        pygame.draw.rect(screen, (255, 255, 255), 
                        (bar_x, bar_y, bar_width, bar_height), 1)
    
    
    @abstractmethod
    def update_behavior(self, delta_time: float):
        """Update enemy-specific behavior. Override in subclasses."""
        pass
    
    
    @abstractmethod
    def on_attack(self):
        """Called when enemy attacks. Override in subclasses."""
        pass

    @abstractmethod
    def draw_attack(self, screen):
        """Draws enemies attack. Override in subclasses."""
        pass
    
    
    def on_death(self):
        """Called when enemy dies. Can be overridden."""
        print(f"{self.name} died!")