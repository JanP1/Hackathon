from __future__ import annotations

import pygame


class Level1DebugHUD:
    """
    Prosty HUD tekstowy z informacją o levelu, prędkości i FPS.
    """

    def __init__(self, level_name: str, font: pygame.font.Font) -> None:
        self.level_name = level_name
        self.font = font

    def draw(
        self,
        surface: pygame.Surface,
        player_speed: float,
        fps: float,
    ) -> None:
        debug_text = (
            f"Level: {self.level_name} | "
            f"speed: {player_speed:.1f} px/s | "
            f"FPS: {fps:.1f}"
        )
        text_surface = self.font.render(debug_text, True, (255, 255, 255))
        surface.blit(text_surface, (10, 10))
