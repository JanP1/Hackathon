import pygame
from objects.game_object import GameObject
from abc import abstractmethod


class Enemy(GameObject):
    def __init__(
        self,
        x_pos: int,
        y_pos: int,
        SCREEN_W: int,
        SCREEN_H: int,
        name: str = "enemy",
        max_health: int = 100,
        attack_cooldown: int = 4,
        damage: int = 10,
    ):
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
        super().__init__(x_pos, y_pos, SCREEN_W, SCREEN_H, name)

        # Health system
        self.max_health = max_health
        self.current_health = max_health
        self.is_alive = True

        # Attack system (beat-based)
        self.attack_cooldown = attack_cooldown  # Attack every Nth beat
        self.beat_counter = 0  # Counts beats
        self.damage = damage
        self.is_attacking = False
        self.attack_animation_time = 0.0
        self.attack_duration = 200.0  # milliseconds

        # Default to active
        self.is_active = True

        # Bullet-time scale (1.0 = normal)
        self.time_scale: float = 1.0

    # -------------------------------------------------
    # Time scale (bullet-time)
    # -------------------------------------------------
    def set_time_scale(self, time_scale: float) -> None:
        """
        Ustawia skalę czasu dla wroga.
        Wszystkie operacje zależne od czasu w update() będą mnożone przez to.
        """
        self.time_scale = max(0.0, float(time_scale))

    # -------------------------------------------------
    # HP / damage
    # -------------------------------------------------
    def take_damage(self, amount: int):
        """Take damage and check if enemy dies."""
        if not self.is_alive:
            return

        self.current_health -= amount
        if self.current_health <= 0:
            self.current_health = 0
            self.is_alive = False
            self.on_death()

    def heal(self, amount: int):
        """Heal the enemy."""
        if not self.is_alive:
            return

        self.current_health = min(self.current_health + amount, self.max_health)

    # -------------------------------------------------
    # Beat-based attacks
    # -------------------------------------------------
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
        """Change the attack cooldown (in beats)."""
        self.attack_cooldown = max(1, cooldown)

    # -------------------------------------------------
    # HP helpers
    # -------------------------------------------------
    def get_health_percentage(self) -> float:
        """Get health as percentage (0.0 to 1.0)."""
        return self.current_health / self.max_health

    # -------------------------------------------------
    # Update / draw
    # -------------------------------------------------
    def update(self, delta_time: float = 0.0):
        """
        Update enemy state.

        Args:
            delta_time: czas od ostatniej klatki w MILISEKUNDACH (surowy),
                        wewnętrznie mnożony przez self.time_scale.
        """
        if not self.is_alive:
            return

        # zastosuj bullet-time
        effective_dt = float(delta_time) * self.time_scale

        # Update attack animation
        if self.is_attacking:
            self.attack_animation_time -= effective_dt
            if self.attack_animation_time <= 0:
                self.is_attacking = False
                self.attack_animation_time = 0

        # Call behavior update (subclass)
        self.update_behavior(effective_dt)

    def draw(self, screen):
        """Draw the enemy and health bar."""
        if not self.is_active:
            return

        # Draw sprite
        super().draw(screen)

        # Draw health bar
        self.draw_health_bar(screen)

        # Draw attack indicator if attacking
        if self.is_attacking:
            self.draw_attack_indicator(screen)

    def draw_health_bar(self, screen):
        """Draw health bar above enemy."""
        bar_width = 50
        bar_height = 5
        bar_x = self.rect.centerx - bar_width // 2
        bar_y = self.rect.top - 10

        # Background (red)
        pygame.draw.rect(
            screen,
            (255, 0, 0),
            (bar_x, bar_y, bar_width, bar_height),
        )

        # Foreground (green)
        health_width = int(bar_width * self.get_health_percentage())
        pygame.draw.rect(
            screen,
            (0, 255, 0),
            (bar_x, bar_y, health_width, bar_height),
        )

        # Border
        pygame.draw.rect(
            screen,
            (255, 255, 255),
            (bar_x, bar_y, bar_width, bar_height),
            1,
        )

    def draw_attack_indicator(self, screen):
        """Draw visual indicator when attacking."""
        # Red flash around enemy
        flash_rect = self.rect.inflate(10, 10)
        pygame.draw.rect(screen, (255, 0, 0), flash_rect, 3)

    # -------------------------------------------------
    # Hooks
    # -------------------------------------------------
    @abstractmethod
    def update_behavior(self, delta_time: float):
        """
        Update enemy-specific behavior.

        delta_time: efektowny czas w MILISEKUNDACH (już po bullet-time!), do ruchu itd.
        """
        pass

    @abstractmethod
    def on_attack(self):
        """Called when enemy attacks. Override in subclasses."""
        pass

    def on_death(self):
        """Called when enemy dies. Can be overridden."""
        print(f"{self.name} died!")
