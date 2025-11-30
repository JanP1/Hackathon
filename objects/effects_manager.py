from typing import List, Tuple, Any
import pygame


class EffectsManager:
    """
    Centralny manager do zbierania danych o efektach wizualnych
    dla postprocessingu (np. GLSL).

    Trzyma:
    - waves_data: fale (np. od gracza),
    - bullet_objects: referencje do pocisków,
    - bullets_data: zrzut (x, y, vx, vy) gotowy dla shadera (podstawowa wersja),
    - (dodatkowo) get_bullets_extended_data() zwraca też trail_length i trail_half_width.
    """
    def __init__(self):
        # Dane fali: (cx, cy, start_time_ms, thickness)
        self.waves_data: List[Tuple[float, float, float, float]] = []
        self.wave_thickness: float = 40.0
        self.wave_max_lifetime_ms: float = 1000.0  # Jak długo fala żyje

        # Czas gry (skalowany) w ms
        self.current_time: float = 0.0

        # Referencje do pocisków (np. PlayerBullet, EnemyProjectile)
        self.bullet_objects: List[Any] = []

        # Dane pocisków: (x, y, vx, vy) – aktualizowane na podstawie bullet_objects
        self.bullets_data: List[Tuple[float, float, float, float]] = []

        # Black Hole
        self.black_hole_active = False
        self.black_hole_pos = (0.0, 0.0)
        self.black_hole_timer = 0.0
        self.black_hole_duration = 1000.0 # ms

    # -------------------------------------------------
    # Fale
    # -------------------------------------------------
    def add_wave(self, center_pos: Tuple[float, float]):
        """
        Dodaje nową falę do renderowania.
        Zapisuje pozycję i czas startu.
        """
        cx, cy = center_pos
        start_time = self.current_time
        self.waves_data.append((float(cx), float(cy), float(start_time), self.wave_thickness))

    def get_waves_data(self) -> List[Tuple[float, float, float, float]]:
        """Zwraca dane o falach dla shadera."""
        return self.waves_data

    def trigger_black_hole(self, pos: Tuple[float, float], duration_ms: float = 1000.0):
        self.black_hole_active = True
        self.black_hole_pos = pos
        self.black_hole_timer = duration_ms
        self.black_hole_duration = duration_ms

    # -------------------------------------------------
    # Pociski – styl add_bullet
    # -------------------------------------------------
    def add_bullet(self, bullet: Any) -> None:
        """
        Rejestruje nowy pocisk w managerze efektów.

        Oczekiwane minimalne pola pocisku:
        - bullet.x, bullet.y
        - bullet.vx, bullet.vy
        - opcjonalnie bullet.alive (bool) – jeśli jest, to martwe będą pomijane.
        """
        if bullet not in self.bullet_objects:
            self.bullet_objects.append(bullet)

    def _sync_bullets_data(self) -> None:
        """
        Buduje bullets_data na podstawie aktualnych obiektów bullet_objects.
        Filtruje martwe/niekompletne pociski.

        Uwaga: ta wersja trzyma stary format (x, y, vx, vy) – dla kompatybilności.
        Rozszerzone dane są dostępne w get_bullets_extended_data().
        """
        new_data: List[Tuple[float, float, float, float]] = []
        new_refs: List[Any] = []

        for b in self.bullet_objects:
            # jeśli jest flaga alive – filtruj martwe
            if hasattr(b, "alive") and not b.alive:
                continue

            # wymagane atrybuty
            if not (hasattr(b, "x") and hasattr(b, "y") and hasattr(b, "vx") and hasattr(b, "vy")):
                continue

            new_data.append(
                (float(b.x), float(b.y), float(b.vx), float(b.vy))
            )
            new_refs.append(b)

        self.bullets_data = new_data
        # czyścimy referencje do martwych / niekompletnych
        self.bullet_objects = new_refs

    def get_bullets_data(self) -> List[Tuple[float, float, float, float]]:
        """
        Zwraca dane o pociskach dla shadera (podstawowy format).
        Dane są każdorazowo synchronizowane z bullet_objects.

        Format: (x, y, vx, vy)
        """
        self._sync_bullets_data()
        return self.bullets_data

    def get_bullets_extended_data(self) -> List[Tuple[float, float, float, float, float, float]]:
        """
        Rozszerzona wersja danych o pociskach.

        Zwraca listę krotek:
            (x, y, vx, vy, trail_length, trail_half_width)

        - jeśli pocisk nie ma trail_length / trail_half_width,
          używane są sensowne domyślne wartości.
        """
        extended: List[Tuple[float, float, float, float, float, float]] = []

        for b in self.bullet_objects:
            # jeśli jest flaga alive – filtruj martwe
            if hasattr(b, "alive") and not b.alive:
                continue

            # wymagane atrybuty pozycji/prędkości
            if not (hasattr(b, "x") and hasattr(b, "y") and hasattr(b, "vx") and hasattr(b, "vy")):
                continue

            # długość i szerokość trójkąta – jeśli brak, daj domyślne
            base_length = float(getattr(b, "trail_length", 160.0))
            base_half_width = float(getattr(b, "trail_half_width", 30.0))

            extended.append(
                (float(b.x), float(b.y), float(b.vx), float(b.vy), base_length, base_half_width)
            )

        return extended

    # -------------------------------------------------
    # Update globalny
    # -------------------------------------------------
    def update(self, scaled_dt: float = 0.0):
        """
        Aktualizuje stan efektów, np. usuwa stare fale.
        WOŁAĆ RAZ NA KLATKĘ!
        scaled_dt: czas w sekundach (już przeskalowany przez time_scale)
        """
        # Aktualizujemy wewnętrzny licznik czasu (w ms)
        self.current_time += scaled_dt * 1000.0
        
        now = self.current_time
        # Usuwamy fale, które żyją zbyt długo
        self.waves_data = [
            w for w in self.waves_data
            if (now - w[2]) < self.wave_max_lifetime_ms
        ]
        
        # Update Black Hole
        if self.black_hole_active:
            self.black_hole_timer -= scaled_dt * 1000.0
            if self.black_hole_timer <= 0:
                self.black_hole_active = False

        # Pocisków tutaj nie ruszamy – ich filtracja dzieje się w _sync_bullets_data()
