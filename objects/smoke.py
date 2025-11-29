# objects/smoke.py

import math
import random
import pygame


# ============================================================
# 1) TRÓJKĄTNY DISTORT ZA POCISKIEM
# ============================================================

class BulletTriangleSmoke:
    """
    Zniekształcający trójkąt za pociskiem.

    Użycie:
        self.distortion = BulletTriangleSmoke()
        ...
        self.distortion.draw(surface, self.x, self.y, self.vx, self.vy,
                             length_override=self.trail_length,
                             half_width_override=self.trail_half_width)
    """

    def __init__(self,
                 length: float = 180.0,
                 half_width: float = 60.0,
                 strength: float = 0.28):
        # DOMYŚLNA maksymalna długość trójkąta za pociskiem (px)
        self.length = float(length)
        # DOMYŚLNA połowa szerokości podstawy trójkąta (px)
        self.half_width = float(half_width)
        # siła zniekształcenia
        self.strength = float(strength)

        # punkt startowy efektu (tam, gdzie pocisk był przy pierwszym rysowaniu)
        self.origin_x: float | None = None
        self.origin_y: float | None = None

    def reset(self) -> None:
        """
        Wyzerowanie punktu startowego.
        Wołaj, gdy używasz tego samego obiektu do nowego pocisku.
        """
        self.origin_x = None
        self.origin_y = None

    def draw(self,
             surface: pygame.Surface,
             tip_x: float,
             tip_y: float,
             vx: float,
             vy: float,
             length_override: float | None = None,
             half_width_override: float | None = None) -> None:
        """
        Rysuje trójkątne zniekształcenie za pociskiem.

        length_override      – maksymalna długość trójkąta TYLKO dla tego wywołania
        half_width_override  – połowa szerokości podstawy TYLKO dla tego wywołania

        Jeśli override'y są None – używa self.length / self.half_width.
        """
        # jeśli pocisk stoi – nie ma sensu robić efektu
        speed_sq = vx * vx + vy * vy
        if speed_sq <= 0.0001:
            return

        # DOMYŚLNE / NADPISANE parametry
        base_max_length = float(length_override) if length_override is not None else self.length
        base_half_width = float(half_width_override) if half_width_override is not None else self.half_width

        if base_max_length <= 1.0 or base_half_width <= 0.0:
            return

        # ustaw punkt startowy przy pierwszym rysowaniu
        tip_xf = float(tip_x)
        tip_yf = float(tip_y)

        if self.origin_x is None or self.origin_y is None:
            self.origin_x = tip_xf
            self.origin_y = tip_yf

        # odległość od punktu startowego – nie chcemy wyjść poza ten punkt
        dx0 = tip_xf - self.origin_x
        dy0 = tip_yf - self.origin_y
        dist_from_origin = math.hypot(dx0, dy0)

        # EFEKTYWNA długość = min(deklarowana_max, ile pocisk faktycznie przeleciał)
        effective_length = min(base_max_length, dist_from_origin)
        if effective_length <= 1.0:
            # jeszcze za wcześnie, żeby rysować sensowny trójkąt
            return

        # kierunek lotu pocisku
        speed = math.sqrt(speed_sq)
        dir_x = vx / speed
        dir_y = vy / speed

        # trójkąt MA BYĆ ZA pociskiem, więc bierzemy przeciwny kierunek
        dir_x = -dir_x
        dir_y = -dir_y

        # wektor prostopadły (w lewo)
        perp_x = -dir_y
        perp_y = dir_x

        # środek podstawy trójkąta (używamy effective_length i base_half_width)
        base_cx = tip_xf + dir_x * effective_length
        base_cy = tip_yf + dir_y * effective_length

        base_left_x = base_cx + perp_x * base_half_width
        base_left_y = base_cy + perp_y * base_half_width

        base_right_x = base_cx - perp_x * base_half_width
        base_right_y = base_cy - perp_y * base_half_width

        # bounding box trójkąta
        min_x = int(min(tip_xf, base_left_x, base_right_x))
        max_x = int(max(tip_xf, base_left_x, base_right_x)) + 1
        min_y = int(min(tip_yf, base_left_y, base_right_y))
        max_y = int(max(tip_yf, base_left_y, base_right_y)) + 1

        rect = pygame.Rect(min_x, min_y, max_x - min_x, max_y - min_y)
        rect = rect.clip(surface.get_rect())
        if rect.width <= 0 or rect.height <= 0:
            return

        try:
            sub = surface.subsurface(rect).copy()
        except ValueError:
            return

        temp = sub.copy()
        w, h = sub.get_width(), sub.get_height()

        # w lokalnym układzie współrzędnych (względem rect)
        tip_local_x = tip_xf - rect.left
        tip_local_y = tip_yf - rect.top

        time_s = pygame.time.get_ticks() / 1000.0

        for y in range(h):
            vy_pix = y - tip_local_y
            for x in range(w):
                vx_pix = x - tip_local_x

                # rzut na kierunek trójkąta (d) i prostopadły (s)
                d = vx_pix * dir_x + vy_pix * dir_y
                if d < 0.0 or d > effective_length:
                    continue

                s = vx_pix * perp_x + vy_pix * perp_y
                # trójkąt zwęża się przy wierzchołku
                max_side = base_half_width * (d / effective_length)
                if s < -max_side or s > max_side:
                    continue

                # normalizacja po długości 0..1
                norm_d = d / effective_length

                # falowanie na boki (wzdłuż prostopadłej)
                wave = math.sin(d * 0.08 - time_s * 6.0)
                side_offset = wave * self.strength * (1.0 - norm_d) * base_half_width * 0.5

                # lekkie "ściśnięcie" w kierunku pocisku
                compress = 1.0 - self.strength * 0.35 * (1.0 - norm_d)
                new_d = d * compress
                new_s = s + side_offset

                # przelicz z powrotem na xy (lokalne)
                src_vx = dir_x * new_d + perp_x * new_s
                src_vy = dir_y * new_d + perp_y * new_s

                src_x = tip_local_x + src_vx
                src_y = tip_local_y + src_vy

                sx = int(src_x)
                sy = int(src_y)

                if 0 <= sx < w and 0 <= sy < h:
                    sub.set_at((x, y), temp.get_at((sx, sy)))

        # wklejamy zniekształcony obraz na główną powierzchnię
        surface.blit(sub, rect)


# ============================================================
# 2) PIERŚCIEŃ FALI OD GRACZA
# ============================================================

class WaveRingSmoke:
    """
    Zniekształcający pierścień (fala od gracza).

    Użycie:
        self.wave_smoke = WaveRingSmoke()
        ...
        for wave in self.sound_waves:
            self.wave_smoke.draw(surface, wave["pos"][0], wave["pos"][1], wave["radius"])
    """

    def __init__(self,
                 thickness: float = 40.0,
                 strength: float = 0.25):
        # grubość pierścienia (px)
        self.thickness = float(thickness)
        # siła zniekształcenia
        self.strength = float(strength)

    def draw(self,
             surface: pygame.Surface,
             cx: float,
             cy: float,
             radius: float) -> None:
        radius = float(radius)
        if radius <= 1.0:
            return

        thickness = self.thickness
        inner = max(0.0, radius - thickness * 0.5)
        outer = radius + thickness * 0.5

        # bounding box pierścienia
        min_x = int(cx - outer)
        max_x = int(cx + outer) + 1
        min_y = int(cy - outer)
        max_y = int(cy + outer) + 1

        rect = pygame.Rect(min_x, min_y, max_x - min_x, max_y - min_y)
        rect = rect.clip(surface.get_rect())
        if rect.width <= 0 or rect.height <= 0:
            return

        try:
            sub = surface.subsurface(rect).copy()
        except ValueError:
            return

        temp = sub.copy()
        w, h = sub.get_width(), sub.get_height()

        center_x = cx - rect.left
        center_y = cy - rect.top

        inner_sq = inner * inner
        outer_sq = outer * outer

        time_s = pygame.time.get_ticks() / 1000.0

        for y in range(h):
            dy = y - center_y
            for x in range(w):
                dx = x - center_x
                dist_sq = dx * dx + dy * dy

                if dist_sq <= inner_sq or dist_sq >= outer_sq:
                    continue

                dist = math.sqrt(dist_sq)
                if dist <= 0.0:
                    continue

                # -1 .. 1 – położenie w obrębie grubości pierścienia
                ring_pos = (dist - radius) / (thickness * 0.5)
                if ring_pos < -1.0 or ring_pos > 1.0:
                    continue

                # fala wzdłuż promienia
                wave = math.sin(dist * 0.15 - time_s * 4.5)

                # im bliżej środka pierścienia, tym mocniej
                falloff = 1.0 - abs(ring_pos)

                offset = wave * self.strength * thickness * falloff

                new_r = dist + offset
                if new_r <= 0.0:
                    continue

                scale = new_r / dist
                src_x = center_x + dx * scale
                src_y = center_y + dy * scale

                sx = int(src_x)
                sy = int(src_y)

                if 0 <= sx < w and 0 <= sy < h:
                    sub.set_at((x, y), temp.get_at((sx, sy)))

        surface.blit(sub, rect)


# ============================================================
# 3) SmokeTrail DO EKSPLOZJI (bez distort, lekkie kółka)
# ============================================================

class _SimpleSmokeParticle:
    def __init__(self, x: float, y: float, dx: float, dy: float, border: int):
        self.x = float(x)
        self.y = float(y)

        # kierunek lotu cząstki (normalizujemy)
        length = math.hypot(dx, dy)
        if length == 0:
            nx, ny = 0.0, 0.0
        else:
            nx, ny = dx / length, dy / length

        # prędkość w px/klatkę (do eksplozji wystarczy stałe tempo)
        speed = random.uniform(2.0, 6.0)
        self.vx = nx * speed
        self.vy = ny * speed

        # promień
        self.radius = random.uniform(4.0, 10.0)
        self.grow = random.uniform(0.2, 0.5)

        # życie w klatkach
        self.lifespan = random.randint(25, 45)
        self.age = 0

        # kolor – inny dla border=1 (jaśniejszy)
        base = 230 if border == 1 else 200
        jitter = random.randint(-20, 20)
        c = max(0, min(255, base + jitter))
        self.color = (c, c, c)

    @property
    def alive(self) -> bool:
        return self.age < self.lifespan

    def update(self):
        self.age += 1
        if not self.alive:
            return

        self.x += self.vx
        self.y += self.vy
        self.radius += self.grow

    def draw(self, surface: pygame.Surface):
        if not self.alive:
            return

        alpha = 255 * (1.0 - self.age / self.lifespan)
        alpha = max(0, min(255, int(alpha)))

        if alpha <= 0 or self.radius <= 0:
            return

        diameter = int(self.radius * 2.0)
        if diameter <= 0:
            return

        temp = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
        pygame.draw.circle(temp, (*self.color, alpha),
                           (diameter // 2, diameter // 2),
                           int(self.radius))

        surface.blit(temp, (int(self.x - self.radius), int(self.y - self.radius)))


class SmokeTrail:
    """
    Lekkie, zwykłe "kółkowe" smoke do eksplozji na wrogach.

    API kompatybilne ze starym kodem:
        explosion = SmokeTrail(border=1)
        explosion.add_particle(x, y, dx, dy)
        explosion.update()
        explosion.draw(surface)
        len(explosion.particles)
    """

    def __init__(self, border: int = 0):
        self.particles: list[_SimpleSmokeParticle] = []
        self.border = int(border)

    def add_particle(self, x: float, y: float, dx: float, dy: float):
        p = _SimpleSmokeParticle(x, y, dx, dy, self.border)
        self.particles.append(p)

    def update(self):
        for p in self.particles:
            p.update()
        self.particles = [p for p in self.particles if p.alive]

    def draw(self, surface: pygame.Surface):
        for p in self.particles:
            p.draw(surface)
