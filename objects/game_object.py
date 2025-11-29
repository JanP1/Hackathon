import pygame
from abc import ABC, abstractmethod, abstractclassmethod

'''
Podstawowy game object po którym będzie dziedziczyło wszystko co może poruszać 
się po ekranie.
'''
class GameObject(ABC):
    def __init__(self, x_pos: int, y_pos:int, SCREEN_W: int, SCREEN_H: int, scale: float = 1, name: str = "object"):
        self.sprite = pygame.image.load('assets/pictures/default_sprite.png')
        
        # Scale the sprite
        original_width = self.sprite.get_width()
        original_height = self.sprite.get_height()
        new_width = int(original_width * scale)
        new_height = int(original_height * scale)
        
        self.sprite = pygame.transform.scale(self.sprite, (new_width, new_height))
        self.sprite_flipped = pygame.transform.flip(self.sprite, True, False);

        self.rect = self.sprite.get_rect() # !!! musimy ustalić jak robimy z hitboxem, czy zawsze wielkości spritea 
        
        self.speed = 1
        
        self.SCREEN_W = SCREEN_W
        self.SCREEN_H = SCREEN_H

        self.rect.x = x_pos
        self.rect.y = y_pos

        self.sounds = {}
        self.sprites = {}

        self.name = name

        self.facing_right = True

        self.is_active = False


    def init_sounds(self, sound_dict):
        for sound_name, sound_path in sound_dict.items():
            self.sounds[sound_name] = pygame.mixer.Sound(sound_path)


    def init_sprites(self, sprite_dict):
        for sprite_name, sprite_path in sprite_dict.items():
            self.sprites[sprite_name] = pygame.image.load(sprite_path)


    def play_sound(self, sound_name):
        if sound_name in self.sounds:
            self.sounds[sound_name].play()        


    def set_sprite(self, sprite_name):
        if sprite_name in self.sprites:
            self.sprite = self.sprites[sprite_name]
            self.sprite_flipped = pygame.transform.flip(self.sprite, True, False) 


    def draw(self, screen):
        current_sprite = self.sprite if self.facing_right else self.sprite_flipped
        screen.blit(current_sprite, self.rect)


    @abstractmethod
    def update(self):
        print(self.name + " update called")