# Game/game.py

import sys
import pygame

# Importujemy klasę Game z level1 jako Level1Game
from scenes.game_level7 import Game as Level1Game

WIDTH = 1920
HEIGHT = 1080
FPS = 60


class Game:
    def __init__(self) -> None:

        pygame.init()
        info = pygame.display.Info()
        self.screen = pygame.display.set_mode((info.current_w, info.current_h), pygame.FULLSCREEN | pygame.SCALED)
        pygame.display.set_caption("Main Game Hub")

        self.clock = pygame.time.Clock()
        self.game_state_manager = GameStateManager("start")  # początkowy stan

        # =============================================================
        # Ekrany / stany
        self.states = {}
        self.game_state_manager = GameStateManager("start")

        # create first state
        self.states["start"] = self.create_state("start")
        # =============================================================

    def create_state(self, name):
        if name == "start":
            return Start(self.screen, self.game_state_manager)
        if name == "level1":
            return Level1State(self.screen, self.clock, self.game_state_manager)
        if name == "end":
            return End(self.screen, self.game_state_manager)

    def run(self):
        while True:
            dt = self.clock.tick(FPS) / 1000.0

            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

            current_state_name = self.game_state_manager.get_state()
            state = self.states[current_state_name]
            state.run(events, dt)

            pygame.display.update()


class GameStateManager:
    def __init__(self, current_state) -> None:
        self.current_state = current_state

    def get_state(self):
        return self.current_state

    def set_state(self, current_state):
        print(f"[STATE] -> {current_state}")

        # Usuń poprzednią instancję
        if current_state in game.states:
            del game.states[current_state]

        # Utwórz nowy stan
        game.states[current_state] = game.create_state(current_state)
        
        # Reset enter press w nowym stanie (jeżeli istnieje)
        state = game.states[current_state]
        if hasattr(state, "_enter_was_pressed"):
            state._enter_was_pressed = True  # traktujemy jak ENTER już wciśnięty

        self.current_state = current_state
    # def set_state(self, current_state):
    #     print(f"[STATE] -> {current_state}")
    #     self.current_state = current_state

class End:
    """
        Koncowy ekran

    """

    def __init__(self, display, game_state_manager) -> None:
        self.display = display
        self.game_state_manager = game_state_manager

        self.font = pygame.font.SysFont("consolas", 40)
        self._enter_was_pressed = False

        # grafika
        self.image = pygame.image.load("assets/pictures/skull-head.png").convert_alpha()
        self.image_rect = self.image.get_rect(center=(self.display.get_width() // 2, 300))

    def run(self, events, dt):
        self.display.fill("red")

        self.display.blit(self.image, self.image_rect)

        text_surface = self.font.render(
            "Naciśnij ENTER, aby powrócić", True, (255, 255, 255)
        )
        text_rect = text_surface.get_rect(
            center=(self.display.get_width() // 2, self.display.get_height() // 2)
        )
        self.display.blit(text_surface, text_rect)

        keys = pygame.key.get_pressed()
        if keys[pygame.K_RETURN]:
            if not self._enter_was_pressed:
                self._enter_was_pressed = True
                self.game_state_manager.set_state("start")
        else:
            self._enter_was_pressed = False

class Start:
    """
    Ekran startowy:
    - zielone tło
    - po wciśnięciu ENTER przechodzimy do stanu "level1"
    """

    def __init__(self, display, game_state_manager) -> None:
        self.display = display
        self.game_state_manager = game_state_manager

        self.font = pygame.font.SysFont("consolas", 40)
        self._enter_was_pressed = False

        # grafika
        self.image = pygame.image.load("assets/pictures/start_screen.png").convert_alpha()
        self.image_rect = self.image.get_rect(center=(self.display.get_width() // 2, self.display.get_height() // 2))

    def run(self, events, dt):
        self.display.fill("green")

        self.display.blit(self.image, self.image_rect)

        text_surface = self.font.render(
            "Naciśnij ENTER, aby uruchomić LEVEL 1", True, (255, 255, 255)
        )
        text_rect = text_surface.get_rect(
            center=(self.display.get_width() // 2, self.display.get_height() // 2 + 200)
        )
        self.display.blit(text_surface, text_rect)

        keys = pygame.key.get_pressed()
        if keys[pygame.K_RETURN]:
            if not self._enter_was_pressed:
                self._enter_was_pressed = True
                self.game_state_manager.set_state("level1")
        else:
            self._enter_was_pressed = False


class Level1State:
    """
    Stan opakowujący Level1Game z Game/Level_level1/game_level1.py.

    - Tworzy Level1Game dopiero przy pierwszym wejściu w stan.
    - Każdą klatkę wywołuje level_game.run_frame(dt, events).
    - Jeśli level zgłosi want_quit=True (ESC), wracamy do "start".
    """

    def __init__(self, display, clock, game_state_manager) -> None:
        self.display = display
        self.clock = clock
        self.game_state_manager = game_state_manager

        self.level_game: Level1Game | None = None

    def run(self, events, dt):
        # Lazy init – tworzymy level dopiero przy pierwszym wejściu
        if self.level_game is None:
            print("[INFO] Tworzenie Level1Game w Level1State")
            self.level_game = Level1Game(
                screen=self.display,
                clock=self.clock,
                level_name="level1",
                player_speed=400.0,
                bg_color=(10, 40, 90),
            )

        # Jedna klatka levelu
        self.level_game.run_frame(dt, events)

        # jezeli zginie - ekran koncowy
        if self.level_game and not self.level_game.player.is_alive:
            self.game_state_manager.set_state("end")
            try:
                self.level_game.stop_audio()
            except AttributeError:
                pass
            self.level_game = None


        # Jeżeli level chce wyjść (ESC), wracamy do "start"
        if getattr(self.level_game, "want_quit", False):
            print("[INFO] Level1 chce wyjść, sprzątanie audio i powrót do 'start'")
            try:
                self.level_game.stop_audio()
            except AttributeError:
                pass

            self.level_game = None
            self.game_state_manager.set_state("start")


if __name__ == "__main__":
    game = Game()
    game.run()
