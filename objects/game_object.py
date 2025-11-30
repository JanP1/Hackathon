import pygame
from abc import ABC, abstractmethod

"""
Podstawowy game object po którym będzie dziedziczyło wszystko,
co może poruszać się po ekranie.
"""

class GameObject(ABC):
    def __init__(
        self,
        x_pos: int,
        y_pos: int,
        SCREEN_W: int,
        SCREEN_H: int,
        scale: float = 1.0,
        name: str = "object",
    ):
        """
        Scalona wersja:
        - obsługuje skalę sprite’a (scale),
        - zachowuje poprzednie API (name na końcu),
        - posiada referencję do kamery (self.camera),
        - draw() umie rysować z przesunięciem kamery.

        Hack kompatybilności:
        Jeżeli wywołanie było GameObject(x, y, W, H, "player"),
        to 'scale' będzie stringiem -> potraktuj to jako name, scale = 1.0.
        """

        # Kompatybilność ze starymi wywołaniami
        if isinstance(scale, str) and name == "object":
            name = scale
            scale = 1.0

        self.SCREEN_W = SCREEN_W
        self.SCREEN_H = SCREEN_H

        self.scale = float(scale)
        self.name = name

        # --- KAMERA ---
        # Może być np. instancją klasy Camera z metodą apply(rect)
        # lub mieć pola x, y. Domyślnie brak kamery.
        self.camera = None

        # Wczytanie domyślnego sprite'a
        self.sprite = pygame.image.load("assets/pictures/default_sprite.png").convert_alpha()

        # Zastosuj skalowanie do sprite’a
        if self.scale != 1.0:
            original_width = self.sprite.get_width()
            original_height = self.sprite.get_height()
            new_width = max(1, int(original_width * self.scale))
            new_height = max(1, int(original_height * self.scale))
            self.sprite = pygame.transform.scale(self.sprite, (new_width, new_height))

        # wersja odwrócona (do patrzenia w prawo/lewo)
        self.sprite_flipped = pygame.transform.flip(self.sprite, True, False)

        # Rect bazuje na aktualnym sprite
        self.rect = self.sprite.get_rect()

        # Ustaw pozycję (topleft)
        self.rect.x = x_pos
        self.rect.y = y_pos

        # Inne pola wspólne
        self.speed = 1

        self.sounds: dict[str, pygame.mixer.Sound] = {}
        self.sprites: dict[str, pygame.Surface] = {}

        self.facing_right = True
        self.is_active = False

    # ======================================================================
    # KAMERA
    # ======================================================================

    def set_camera(self, camera) -> None:
        """
        Podpina kamerę do obiektu.
        'camera' powinna mieć:
        - metodę apply(rect) -> rect przesunięty,
        - lub pola x, y (top-left kamery w world coords).
        """
        self.camera = camera

    # ======================================================================
    # Inicjalizacja zasobów
    # ======================================================================

    def init_sounds(self, sound_dict: dict[str, str]) -> None:
        for sound_name, sound_path in sound_dict.items():
            self.sounds[sound_name] = pygame.mixer.Sound(sound_path)

    def init_sprites(self, sprite_dict: dict[str, str]) -> None:
        """
        Ładuje dodatkowe sprite'y do słownika self.sprites.
        Nie zmienia aktualnego sprite'a – do tego służy set_sprite().
        """
        for sprite_name, sprite_path in sprite_dict.items():
            self.sprites[sprite_name] = pygame.image.load(sprite_path).convert_alpha()

    def play_sound(self, sound_name: str) -> None:
        if sound_name in self.sounds:
            self.sounds[sound_name].play()

    def set_sprite(self, sprite_name: str) -> None:
        """
        Ustawia nowy sprite po nazwie z self.sprites
        i stosuje na nim tę samą skalę co bazowo.
        Zmiana sprite’a zachowuje aktualne center recta.
        """
        if sprite_name in self.sprites:
            old_center = self.rect.center

            self.sprite = self.sprites[sprite_name]

            # przeskaluj nowy sprite zgodnie z self.scale
            if self.scale != 1.0:
                original_width = self.sprite.get_width()
                original_height = self.sprite.get_height()
                new_width = max(1, int(original_width * self.scale))
                new_height = max(1, int(original_height * self.scale))
                self.sprite = pygame.transform.scale(self.sprite, (new_width, new_height))

            self.sprite_flipped = pygame.transform.flip(self.sprite, True, False)

            # nadpisujemy rect na bazie nowego sprite, ale zachowujemy center
            self.rect = self.sprite.get_rect()
            self.rect.center = old_center

    # ======================================================================
    # Rysowanie (z kamerą)
    # ======================================================================

    def draw(self, screen: pygame.Surface) -> None:
        current_sprite = self.sprite if self.facing_right else self.sprite_flipped

        # Domyślnie rysujemy w self.rect
        draw_rect = self.rect

        # Jeśli jest kamera, spróbuj użyć apply(rect),
        # a jeśli jej nie ma, użyj x/y kamery.
        if self.camera is not None:
            if hasattr(self.camera, "apply"):
                try:
                    draw_rect = self.camera.apply(self.rect)
                except Exception:
                    # fallback na x/y
                    cam_x = getattr(self.camera, "x", 0)
                    cam_y = getattr(self.camera, "y", 0)
                    draw_rect = self.rect.move(-cam_x, -cam_y)
            else:
                cam_x = getattr(self.camera, "x", 0)
                cam_y = getattr(self.camera, "y", 0)
                draw_rect = self.rect.move(-cam_x, -cam_y)

        screen.blit(current_sprite, draw_rect)

    # ======================================================================
    # Update – abstrakcyjny
    # ======================================================================

    @abstractmethod
    def update(self) -> None:
        print(self.name + " update called")
