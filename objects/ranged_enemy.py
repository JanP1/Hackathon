import pygame
from objects.enemy import Enemy


class EnemyProjectile:
    """
    Prosty pocisk wroga, kompatybilny z EffectsManager.add_bullet:
    - ma x, y, vx, vy, alive, damage
    """
    def __init__(
        self,
        x: float,
        y: float,
        vx: float,
        vy: float,
        damage: int,
        screen_w: int,
        screen_h: int,
    ):
        self.x = float(x)
        self.y = float(y)
        self.vx = float(vx)
        self.vy = float(vy)
        self.damage = int(damage)
        self.alive = True

        self.SCREEN_W = screen_w
        self.SCREEN_H = screen_h

    def update(self, delta_time: float) -> None:
        """
        Aktualizacja pozycji pocisku.

        Tutaj nadal lecimy „na klatkę” (tak jak miałeś wcześniej),
        nie używamy delta_time do skalowania prędkości, żeby nie zmieniać logiki.
        """
        self.x += self.vx
        self.y += self.vy

        # jeśli wyleci poza ekran – oznacz jako martwy
        if (
            self.x < 0
            or self.x > self.SCREEN_W
            or self.y < 0
            or self.y > self.SCREEN_H
        ):
            self.alive = False

    def get_pos_int(self) -> tuple[int, int]:
        return int(self.x), int(self.y)


class RangedEnemy(Enemy):
    def __init__(self, x_pos: int, y_pos: int, SCREEN_W: int, SCREEN_H: int):
        super().__init__(
            x_pos,
            y_pos,
            SCREEN_W,
            SCREEN_H,
            name="ranged_enemy",
            max_health=60,
            attack_cooldown=4,
            damage=20,
        )

        # teraz to lista obiektów EnemyProjectile
        self.projectiles: list[EnemyProjectile] = []
        self.move_speed = 1.5
        self.target_x = None
        self.target_y = None
        self.keep_distance = 200  # Keep this distance from target

        # Manager efektów (wstrzykiwany z zewnątrz)
        self.effects_manager = None

    def set_target(self, x: int, y: int):
        """Set target to keep distance from (e.g., player position)."""
        self.target_x = x
        self.target_y = y

    def set_effects_manager(self, manager) -> None:
        """Wstrzykuje manager efektów do obiektu wroga."""
        self.effects_manager = manager

    def update_behavior(self, delta_time: float):
        """Move to keep distance from target, update projectiles."""
        # Keep distance from target
        if self.target_x is not None and self.target_y is not None:
            dx = self.rect.centerx - self.target_x
            dy = self.rect.centery - self.target_y
            distance = (dx**2 + dy**2) ** 0.5

            if distance > 0:
                # If too close, move away
                if distance < self.keep_distance:
                    # Move away from target
                    dx = (dx / distance) * self.move_speed
                    dy = (dy / distance) * self.move_speed
                    self.rect.x += dx
                    self.rect.y += dy
                # If too far, move closer
                elif distance > self.keep_distance + 50:
                    # Move towards target
                    dx = -(dx / distance) * self.move_speed
                    dy = -(dy / distance) * self.move_speed
                    self.rect.x += dx
                    self.rect.y += dy

                # Update facing direction
                self.facing_right = (self.target_x - self.rect.centerx) > 0

        # Update projectile positions
        for projectile in self.projectiles[:]:
            projectile.update(delta_time)

            # Remove if off screen / dead
            if not projectile.alive:
                self.projectiles.remove(projectile)

    def on_attack(self):
        """Shoot a projectile towards target."""
        print(f"{self.name} shoots projectile! Damage: {self.damage}")

        # Calculate direction to target if available
        if self.target_x is not None and self.target_y is not None:
            dx = self.target_x - self.rect.centerx
            dy = self.target_y - self.rect.centery
            distance = (dx**2 + dy**2) ** 0.5

            if distance > 0:
                speed = 5
                vx = (dx / distance) * speed
                vy = (dy / distance) * speed
            else:
                vx = 5 if self.facing_right else -5
                vy = 0
        else:
            vx = 5 if self.facing_right else -5
            vy = 0

        # Create projectile jako obiekt
        projectile = EnemyProjectile(
            x=self.rect.centerx,
            y=self.rect.centery,
            vx=vx,
            vy=vy,
            damage=self.damage,
            screen_w=self.SCREEN_W,
            screen_h=self.SCREEN_H,
        )
        self.projectiles.append(projectile)

        # Rejestrujemy pocisk w managerze efektów (add_bullet)
        if self.effects_manager:
            self.effects_manager.add_bullet(projectile)
            # Dodaj też efekt fali przy strzale (jak miałeś)
            # self.effects_manager.add_wave(self.rect.center)

    def draw(self, screen):
        """Draw enemy and projectiles."""
        super().draw(screen)

        # Draw projectiles
        for projectile in self.projectiles:
            px, py = projectile.get_pos_int()
            pygame.draw.circle(screen, (255, 255, 0), (px, py), 5)
