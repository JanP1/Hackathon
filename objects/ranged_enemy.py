import pygame
from objects.enemy import Enemy


class EnemyProjectile:
    """
    Prosty pocisk wroga, kompatybilny z EffectsManager.add_bullet:
    - ma x, y, vx, vy, alive, damage
    - zna rozmiar ekranu, żeby sam się "zabijać" po wylocie poza ekran
    - posiada radius (do rysowania / kolizji)
    - posiada trail_length i trail_half_width (parametry trójkąta za pociskiem)
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
        radius: int = 7,
        trail_length: float | None = None,
        trail_half_width: float | None = None,
    ):
        self.x = float(x)
        self.y = float(y)
        self.vx = float(vx)
        self.vy = float(vy)
        self.damage = int(damage)
        self.alive = True

        self.SCREEN_W = screen_w
        self.SCREEN_H = screen_h

        # promień wizualny/kolizyjny pocisku
        self.radius = int(radius)

        # domyślne parametry trójkąta: węższy i krótszy niż u gracza
        if trail_length is None:
            # np. ok. 9 * radius
            self.trail_length = float(self.radius) * 9.0
        else:
            self.trail_length = float(trail_length)

        if trail_half_width is None:
            # np. ok. 1.4 * radius
            self.trail_half_width = float(self.radius) * 1.4
        else:
            self.trail_half_width = float(trail_half_width)

    def update(self, delta_time: float = 0.0) -> None:
        """
        Aktualizacja pozycji pocisku.

        UWAGA: jak w Twojej drugiej wersji – delta_time nie jest używane do
        skalowania prędkości, ruch jest nadal "na klatkę", żeby nie rozwalać logiki.
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
    def __init__(
        self,
        x_pos: int,
        y_pos: int,
        SCREEN_W: int,
        SCREEN_H: int,
        scale: float = 1.0,
        target=None,
        attack_cooldown: int = 4,
    ):
        """
        Połączony konstruktor:

        - może działać w "starym" stylu:
            RangedEnemy(x, y, W, H, 0.25, player)
        - może działać w "nowym" stylu:
            RangedEnemy(x, y, W, H)  # target ustawiany set_target(...)
        """

        # KLUCZOWA ZMIANA: nie przekazujemy name= jako keyword,
        # żeby Enemy.__init__ nie dostał dwóch wartości dla 'name'.
        super().__init__(
            x_pos,
            y_pos,
            SCREEN_W,
            SCREEN_H,
            scale,
            max_health=60,
            attack_cooldown=attack_cooldown,
            damage=20,
        )

        # Ustawiamy nazwę ręcznie po super().__init__
        self.name = "ranged_enemy"

        self.SCREEN_W = SCREEN_W
        self.SCREEN_H = SCREEN_H

        # pociski jako obiekty EnemyProjectile
        self.projectiles: list[EnemyProjectile] = []

        # parametry ruchu / AI
        self.move_speed = 2.0  # kompromis między 3 a 1.5
        self.keep_distance = 400  # z pierwszej wersji – trzyma się dalej

        # target może być:
        # - obiektem (np. Player),
        # - koordynatami target_x/target_y
        self.target = target
        self.target_x: int | None = None
        self.target_y: int | None = None

        # flagi ze starej wersji
        self.is_alive: bool = True
        self.is_active: bool = True

        # Manager efektów (wstrzykiwany z zewnątrz)
        self.effects_manager = None

        # time_scale (podpinany z zewnątrz przez BaseLevel)
        self.time_scale: float = 1.0

    # ======================================================================
    # Integracja z BaseLevel / EffectsManager / time_scale
    # ======================================================================

    def set_effects_manager(self, manager) -> None:
        """Wstrzykuje manager efektów do obiektu wroga."""
        self.effects_manager = manager

    def set_time_scale(self, time_scale: float) -> None:
        """
        Podpinany przez BaseLevel. Na razie tylko przechowujemy,
        żeby nie mnożyć time_scale podwójnie (ruch i tak jest już
        skalowany wewnątrz dt wyżej).
        """
        self.time_scale = float(time_scale)

    # ======================================================================
    # Target – obsługa zarówno obiektu, jak i koordynatów
    # ======================================================================

    def set_target(self, *args):
        """
        API połączone:

        - enemy.set_target(player)      # ustaw target jako obiekt
        - enemy.set_target(x, y)        # ustaw bezpośrednio koordynaty

        target_x/target_y są odświeżane na bieżąco w update() jeśli
        target (obiekt) jest ustawiony.
        """
        if len(args) == 1:
            # obiekt (np. Player)
            self.target = args[0]
        elif len(args) == 2:
            # koordynaty
            self.target_x = int(args[0])
            self.target_y = int(args[1])
        else:
            raise TypeError(
                "set_target expect 1 (object) or 2 (x, y) arguments."
            )

    def _refresh_target_from_object(self) -> None:
        """
        Jeżeli mamy przypięty target jako obiekt z rect,
        przepisz jego pozycję do target_x / target_y.
        """
        if self.target is not None and hasattr(self.target, "rect"):
            self.target_x = self.target.rect.centerx
            self.target_y = self.target.rect.centery

    # ======================================================================
    # Ruch + AI
    # ======================================================================

    def update_behavior(self, delta_time: float = 0.0) -> None:
        """Move to keep distance from target, update projectiles."""
        # Uaktualnij target z obiektu, jeżeli taki jest
        self._refresh_target_from_object()

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

    # ======================================================================
    # Kolizje pocisków z targetem (wersja ze "starego" ranged_enemy)
    # ======================================================================

    def projectile_check_collision(self) -> None:
        """
        Wersja z pierwszego pliku:
        - pociski sprawdzają kolizję z target.rect,
        - target dostaje take_damage(damage).
        Teraz działa na EnemyProjectile, nie na dict-ach.
        """
        if self.target is None or not hasattr(self.target, "rect"):
            return

        for projectile in self.projectiles[:]:
            px, py = projectile.get_pos_int()

            if self.target.rect.collidepoint(px, py):
                if hasattr(self.target, "take_damage"):
                    self.target.take_damage(projectile.damage)
                print("PLAYER HIT")
                projectile.alive = False
                self.projectiles.remove(projectile)

    # ======================================================================
    # Atak
    # ======================================================================

    def on_attack(self) -> None:
        """Shoot a projectile towards target."""
        print(f"{self.name} shoots projectile! Damage: {self.damage}")

        # Upewniamy się, że target_x / target_y są aktualne
        self._refresh_target_from_object()

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

        # Create projectile jako obiekt – węższy/krótszy trójkąt niż u gracza
        projectile = EnemyProjectile(
            x=self.rect.centerx,
            y=self.rect.centery,
            vx=vx,
            vy=vy,
            damage=self.damage,
            screen_w=self.SCREEN_W,
            screen_h=self.SCREEN_H,
            radius=7,             # mniejszy pocisk
            trail_length=70.0,    # krótszy trójkąt za pociskiem
            trail_half_width=10.0 # węższy trójkąt za pociskiem
        )
        self.projectiles.append(projectile)

        # Rejestrujemy pocisk w managerze efektów (add_bullet)
        if self.effects_manager is not None:
            self.effects_manager.add_bullet(projectile)
            # Jeśli chcesz falę przy strzale:
            # if hasattr(self.effects_manager, "add_wave"):
            #     self.effects_manager.add_wave(self.rect.center)

    # ======================================================================
    # Update – kompatybilny z obydwoma stylami (z dt i bez dt)
    # ======================================================================

    def update(self, delta_time: float = 0.0) -> None:
        """
        Łączy zachowanie obu wersji:

        - stary kod może wywołać: enemy.update()
        - nowy kod (BaseLevel) może wywołać: enemy.update(delta_ms)

        W środku:
        - update_behavior() (ruch + update pocisków),
        - projectile_check_collision().
        """
        if not self.is_active or not self.is_alive:
            return

        self.update_behavior(delta_time)
        self.projectile_check_collision()

    # ======================================================================
    # Rysowanie
    # ======================================================================

    def draw(self, screen: pygame.Surface) -> None:
        """Draw enemy and projectiles."""
        super().draw(screen)

        for projectile in self.projectiles:
            px, py = projectile.get_pos_int()
            pygame.draw.circle(screen, (255, 255, 0), (px, py), projectile.radius)
