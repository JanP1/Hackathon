from __future__ import annotations

import pygame


class Level1DebugHUD:
    """
    Prosty HUD: level, prędkość bazowa gracza, time_scale, efektywna prędkość, FPS.
    """

    def __init__(self, level_name: str, font: pygame.font.Font) -> None:
        self.level_name = level_name
        self.font = font

    def draw(
        self,
        surface: pygame.Surface,
        base_player_speed: float,
        time_scale: float,
        fps: float,
    ) -> None:
        effective_speed = base_player_speed * time_scale
        text = (
            f"Level: {self.level_name} | "
            f"base spd: {base_player_speed:.1f} px/s | "
            f"time: {time_scale:.2f}x | "
            f"eff: {effective_speed:.1f} px/s | "
            f"FPS: {fps:.1f}"
        )
        surf = self.font.render(text, True, (255, 255, 255))
        surface.blit(surf, (10, 10))
