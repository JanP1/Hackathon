from typing import List, Tuple, Any
import pygame


class EffectsManager:
    """
    Centralny manager do zbierania danych o efektach wizualnych
    dla postprocessingu (np. GLSL).

    Trzyma:
    - waves_data: fale (np. od gracza),
    - bullet_objects: referencje do pocisków,
    - bullets_data: zrzut (x, y, vx, vy) gotowy dla shadera.
    """
    def __init__(self):
        # Dane fali: (cx, cy, start_time_ms, thickness)
        self.waves_data: List[Tuple[float, float, float, float]] = []
        self.wave_thickness: float = 40.0
        self.wave_max_lifetime_ms: float = 1000.0  # Jak długo fala żyje

        # Referencje do pocisków (np. PlayerBullet)
        self.bullet_objects: List[Any] = []

        # Dane pocisków: (x, y, vx, vy) – aktualizowane na podstawie bullet_objects
        self.bullets_data: List[Tuple[float, float, float, float]] = []

    # -------------------------------------------------
    # Fale
    # -------------------------------------------------
    def add_wave(self, center_pos: Tuple[float, float]):
        """
        Dodaje nową falę do renderowania.
        Zapisuje pozycję i czas startu.
        """
        cx, cy = center_pos
        start_time = pygame.time.get_ticks()
        self.waves_data.append((float(cx), float(cy), float(start_time), self.wave_thickness))

    def get_waves_data(self) -> List[Tuple[float, float, float, float]]:
        """Zwraca dane o falach dla shadera."""
        return self.waves_data

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
        self.bullet_objects = new_refs  # czyścimy referencje do martwych / niekompletnych

    def get_bullets_data(self) -> List[Tuple[float, float, float, float]]:
        """
        Zwraca dane o pociskach dla shadera.
        Dane są każdorazowo synchronizowane z bullet_objects.
        """
        self._sync_bullets_data()
        return self.bullets_data

    # -------------------------------------------------
    # Update globalny
    # -------------------------------------------------
    def update(self):
        """
        Aktualizuje stan efektów, np. usuwa stare fale.
        WOŁAĆ RAZ NA KLATKĘ!
        """
        now = pygame.time.get_ticks()
        # Usuwamy fale, które żyją zbyt długo
        self.waves_data = [
            w for w in self.waves_data
            if (now - w[2]) < self.wave_max_lifetime_ms
        ]
        # Pocisków tutaj nie ruszamy – ich filtracja dzieje się w _sync_bullets_data()
