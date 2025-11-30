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
        - jeśli ktoś przez przypadek podał name jako 5. argument (stare wywołania),
          próbujemy to wykryć i potraktować jako name, a scale ustawiamy na 1.0.
        """

        # Mały hack kompatybilności:
        # Jeżeli wywołanie było GameObject(x, y, W, H, "player"),
        # to 'scale' będzie stringiem -> potraktuj to jako name.
        if isinstance(scale, str) and name == "object":
            name = scale
            scale = 1.0

        self.SCREEN_W = SCREEN_W
        self.SCREEN_H = SCREEN_H

        self.scale = float(scale)
        self.name = name

        # Wczytanie domyślnego sprite'a
        # (convert_alpha dla lepszej wydajności przy przezroczystości)
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
        # (!!! nadal trzeba zdecydować globalnie, czy hitbox == sprite)
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

        # Referencja do kamery (wstrzykiwana z zewnątrz)
        self.camera = None

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
    # Rysowanie
    # ======================================================================

    def draw(self, screen: pygame.Surface) -> None:
        # Pobierz przesunięcie kamery, jeśli istnieje
        cam_x, cam_y = 0, 0
        if self.camera is not None:
            cam_x = self.camera.x
            cam_y = self.camera.y

        # Rysuj sprite z uwzględnieniem kamery
        current_sprite = self.sprite if self.facing_right else self.sprite_flipped
        screen.blit(current_sprite, (self.rect.x - cam_x, self.rect.y - cam_y))

    # ======================================================================
    # Update – abstrakcyjny
    # ======================================================================

    @abstractmethod
    def update(self) -> None:
        print(self.name + " update called")
