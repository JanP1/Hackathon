import sys
import os
import json
import pygame
from pathlib import Path

# Setup paths
CURRENT_DIR = Path(__file__).resolve().parent
BASE_DIR = CURRENT_DIR.parent
ASSETS_DIR = BASE_DIR / "assets"
LEVELS_DIR = ASSETS_DIR / "levels"
PICTURES_DIR = ASSETS_DIR / "pictures"
BUILDINGS_DIR = PICTURES_DIR / "buildings"

# Constants
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
MAP_WIDTH = 4096
MAP_HEIGHT = 4096
SCROLL_SPEED = 15

# Colors
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Level Editor - WASD: Move, Click: Place, R-Click: Remove, S: Save")
    clock = pygame.time.Clock()

    # Load Background
    bg_path = PICTURES_DIR / "main_background.png"
    try:
        bg_img = pygame.image.load(str(bg_path)).convert()
        bg_img = pygame.transform.scale(bg_img, (MAP_WIDTH, MAP_HEIGHT))
    except Exception as e:
        print(f"Error loading background: {e}")
        bg_img = pygame.Surface((MAP_WIDTH, MAP_HEIGHT))
        bg_img.fill((50, 100, 50))

    # Load Building Sprite
    house_path = BUILDINGS_DIR / "house.png"
    try:
        house_img = pygame.image.load(str(house_path)).convert_alpha()
    except Exception as e:
        print(f"Error loading house: {e}")
        house_img = pygame.Surface((100, 100))
        house_img.fill(RED)

    # Camera
    cam_x = 0
    cam_y = 0

    # Buildings list: [{"x": x, "y": y}]
    buildings = []

    # Load existing
    json_path = LEVELS_DIR / "level7_buildings.json"
    if json_path.exists():
        try:
            with open(json_path, "r") as f:
                buildings = json.load(f)
            print(f"Loaded {len(buildings)} buildings.")
        except Exception as e:
            print(f"Error loading JSON: {e}")

    running = True
    while running:
        dt = clock.tick(60)

        # Events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                world_x = mx + cam_x
                world_y = my + cam_y
                
                if event.button == 1: # Left Click - Place
                    # Center the building on click? Or top-left?
                    # Game uses topleft in Building.__init__ (x_pos, y_pos)
                    # Let's place top-left for consistency with game logic
                    # Or center it for better UX?
                    # If I center it, I need to adjust x,y before saving.
                    # Let's place top-left to be simple and exact.
                    buildings.append({"x": int(world_x), "y": int(world_y)})
                    
                elif event.button == 3: # Right Click - Remove
                    # Find closest building
                    to_remove = None
                    min_dist = 10000
                    for b in buildings:
                        bx = b["x"] + house_img.get_width() // 2
                        by = b["y"] + house_img.get_height() // 2
                        dist = ((bx - world_x)**2 + (by - world_y)**2)**0.5
                        if dist < 100 and dist < min_dist: # Threshold
                            min_dist = dist
                            to_remove = b
                    
                    if to_remove:
                        buildings.remove(to_remove)

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_s:
                    # Save
                    if not LEVELS_DIR.exists():
                        LEVELS_DIR.mkdir(parents=True)
                    with open(json_path, "w") as f:
                        json.dump(buildings, f, indent=4)
                    print("Saved buildings to JSON.")

        # Camera Movement
        keys = pygame.key.get_pressed()
        if keys[pygame.K_w]: cam_y -= SCROLL_SPEED
        if keys[pygame.K_s]: cam_y += SCROLL_SPEED
        if keys[pygame.K_a]: cam_x -= SCROLL_SPEED
        if keys[pygame.K_d]: cam_x += SCROLL_SPEED

        # Clamp Camera
        cam_x = max(0, min(cam_x, MAP_WIDTH - SCREEN_WIDTH))
        cam_y = max(0, min(cam_y, MAP_HEIGHT - SCREEN_HEIGHT))

        # Draw
        screen.fill((0, 0, 0))
        
        # Draw BG
        screen.blit(bg_img, (-cam_x, -cam_y))

        # Draw Buildings
        for b in buildings:
            screen.blit(house_img, (b["x"] - cam_x, b["y"] - cam_y))

        # Draw HUD
        font = pygame.font.SysFont("arial", 20)
        txt = font.render(f"Buildings: {len(buildings)} | Pos: {cam_x},{cam_y}", True, WHITE)
        screen.blit(txt, (10, 10))

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
