# Game/game.py

import sys
import pygame
from pygame.locals import *

# Importujemy klasę Game z level1 jako Level1Game
# from scenes.game_level7 import Game as Level1Game  <-- USUNIĘTE (przeniesione do Level1State)

try:
    from gl_postprocess import GLPostProcessor
except ImportError:
    print("Warning: Could not import GLPostProcessor. Running without effects.")
    GLPostProcessor = None

WIDTH = 1920
HEIGHT = 1080
FPS = 60


class Game:
    def __init__(self) -> None:
        pygame.init()
        
        # Initialize with OpenGL
        self.screen = pygame.display.set_mode(
            (WIDTH, HEIGHT), 
            pygame.OPENGL | pygame.DOUBLEBUF
        )
        pygame.display.set_caption("Main Game Hub")
        
        # Virtual screen for drawing (standard pygame surface)
        self.virtual_screen = pygame.Surface((WIDTH, HEIGHT)).convert()

        self.clock = pygame.time.Clock()
        
        # Post processor
        self.gl_post = None
        if GLPostProcessor:
            self.gl_post = GLPostProcessor(WIDTH, HEIGHT)

        self.game_state_manager = GameStateManager("start")  # początkowy stan

        # =============================================================
        # Ekrany / stany
        # Przekazujemy virtual_screen zamiast screen
        self.start = Start(self.virtual_screen, self.game_state_manager)
        self.level1 = Level1State(self.virtual_screen, self.clock, self.game_state_manager)

        self.states = {
            "start": self.start,
            "level1": self.level1,
        }
        # =============================================================

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
            
            # Run state logic (draws to virtual_screen)
            state.run(events, dt)

            # Render to screen using GLPostProcessor
            if self.gl_post and hasattr(state, 'get_postprocess_args'):
                args = state.get_postprocess_args()
                self.gl_post.render(self.virtual_screen, **args)
            else:
                # Fallback if no GL or no args (shouldn't happen if we implement correctly)
                pass

            pygame.display.flip()


class GameStateManager:
    def __init__(self, current_state) -> None:
        self.current_state = current_state

    def get_state(self):
        return self.current_state

    def set_state(self, current_state):
        print(f"[STATE] -> {current_state}")
        self.current_state = current_state


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

    def run(self, events, dt):
        self.display.fill("green")

        text_surface = self.font.render(
            "Naciśnij ENTER, aby uruchomić LEVEL 1", True, (0, 0, 0)
        )
        text_rect = text_surface.get_rect(
            center=(self.display.get_width() // 2, self.display.get_height() // 2)
        )
        self.display.blit(text_surface, text_rect)

        keys = pygame.key.get_pressed()
        if keys[pygame.K_RETURN]:
            if not self._enter_was_pressed:
                self._enter_was_pressed = True
                self.game_state_manager.set_state("level1")
        else:
            self._enter_was_pressed = False

    def get_postprocess_args(self):
        return {
            "current_time_ms": pygame.time.get_ticks(),
            "bullets": [],
            "waves": [],
            "invert": False,
            "distortion_strength": 0.0,
            "damage_tint": 0.0,
            "black_hole_pos": (0.0, 0.0),
            "black_hole_strength": 0.0
        }


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

        self.level_game = None # Type hint removed to avoid NameError if Level1Game is not imported yet

    def run(self, events, dt):
        # Lazy init – tworzymy level dopiero przy pierwszym wejściu
        if self.level_game is None:
            print("[INFO] Tworzenie Level1Game w Level1State")
            # Importujemy tutaj, aby uniknąć błędów przy starcie aplikacji (np. brakujące DLL)
            from scenes.game_level7 import Game as Level1Game
            
            self.level_game = Level1Game(
                screen=self.display,
                clock=self.clock,
                level_name="level1",
                player_speed=400.0,
                bg_color=(10, 40, 90),
            )

        # Jedna klatka levelu
        self.level_game.run_frame(dt, events)

        # Jeżeli level chce wyjść (ESC), wracamy do "start"
        if getattr(self.level_game, "want_quit", False):
            print("[INFO] Level1 chce wyjść, sprzątanie audio i powrót do 'start'")
            try:
                self.level_game.stop_audio()
            except AttributeError:
                pass

            self.level_game = None
            self.game_state_manager.set_state("start")

    def get_postprocess_args(self):
        if self.level_game is None:
             return {
                "current_time_ms": pygame.time.get_ticks(),
                "bullets": [],
                "waves": [],
                "invert": False,
                "distortion_strength": 0.0,
                "damage_tint": 0.0,
                "black_hole_pos": (0.0, 0.0),
                "black_hole_strength": 0.0
            }
        
        game = self.level_game
        
        # Logic from game_level7.py
        cam_x = game.camera.x if game.camera else 0
        cam_y = game.camera.y if game.camera else 0

        bullets_data = game.effects_manager.get_bullets_data()
        bullets_data_screen = [
            (x - cam_x, y - cam_y, vx, vy) for x, y, vx, vy in bullets_data
        ]

        waves_data = game.effects_manager.get_waves_data()
        waves_data_screen = [
            (cx - cam_x, cy - cam_y, start_time, thickness)
            for cx, cy, start_time, thickness in waves_data
        ]

        current_time_ms = game.effects_manager.current_time
        
        invert = game.slow_time_active
        distortion = 1.0 if game.slow_time_active else 0.0
        
        damage_tint = 0.0
        if game.player.damage_tint_timer > 0:
            damage_tint = min(1.0, game.player.damage_tint_timer / 200.0) * 0.6

        bh_active = game.effects_manager.black_hole_active
        bh_pos = (0.0, 0.0)
        bh_strength = 0.0
        
        if bh_active:
            bh_timer = game.effects_manager.black_hole_timer
            bh_duration = game.effects_manager.black_hole_duration
            bh_strength = bh_timer / bh_duration
            raw_pos = game.effects_manager.black_hole_pos
            bh_pos = (raw_pos[0] - cam_x, raw_pos[1] - cam_y)

        return {
            "current_time_ms": current_time_ms,
            "bullets": bullets_data_screen,
            "waves": waves_data_screen,
            "invert": invert,
            "distortion_strength": distortion,
            "damage_tint": damage_tint,
            "black_hole_pos": bh_pos,
            "black_hole_strength": bh_strength
        }


def main():
    try:
        game = Game()
        game.run()
    except Exception:
        import traceback
        traceback.print_exc()
        input("KRYTYCZNY BLAD W GAME.PY! Nacisnij ENTER aby zamknac...")

if __name__ == "__main__":
    main()
