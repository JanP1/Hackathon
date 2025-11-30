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
BACKGROUNDS_DIR = PICTURES_DIR / "backgrounds"

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
    pygame.display.set_caption("Level Editor - WASD: Move, Click: Place, R-Click: Remove, S: Save, Ctrl+S: Save New, Arrows: BG")
    clock = pygame.time.Clock()

    # Load Backgrounds
    bg_images = []
    bg_names = []
    
    # Add default main_background.png first
    default_bg_path = PICTURES_DIR / "main_background.png"
    if default_bg_path.exists():
        try:
            img = pygame.image.load(str(default_bg_path)).convert()
            img = pygame.transform.scale(img, (MAP_WIDTH, MAP_HEIGHT))
            bg_images.append(img)
            bg_names.append("main_background.png")
        except Exception as e:
            print(f"Error loading default bg: {e}")

    # Load from backgrounds folder
    if BACKGROUNDS_DIR.exists():
        for f in BACKGROUNDS_DIR.iterdir():
            if f.is_file() and f.suffix.lower() in [".png", ".jpg", ".jpeg"]:
                try:
                    img = pygame.image.load(str(f)).convert()
                    img = pygame.transform.scale(img, (MAP_WIDTH, MAP_HEIGHT))
                    bg_images.append(img)
                    bg_names.append(f.name)
                except Exception as e:
                    print(f"Error loading bg {f.name}: {e}")
    
    if not bg_images:
        # Fallback
        surf = pygame.Surface((MAP_WIDTH, MAP_HEIGHT))
        surf.fill((50, 100, 50))
        bg_images.append(surf)
        bg_names.append("default_color")
        
    current_bg_idx = 0

    # Load Building Images
    building_images = {}
    building_names = []
    
    if BUILDINGS_DIR.exists():
        for f in BUILDINGS_DIR.iterdir():
            if f.is_file() and f.suffix.lower() in [".png", ".jpg", ".jpeg"]:
                try:
                    img = pygame.image.load(str(f)).convert_alpha()
                    building_images[f.name] = img
                    building_names.append(f.name)
                except Exception as e:
                    print(f"Error loading {f.name}: {e}")
    
    if not building_names:
        # Fallback
        default_name = "default"
        surf = pygame.Surface((100, 100))
        surf.fill(RED)
        building_images[default_name] = surf
        building_names.append(default_name)
        
    current_idx = 0

    # Camera
    cam_x = 0
    cam_y = 0

    # Buildings list: [{"x": x, "y": y, "type": "..."}]
    buildings = []
    
    # Current level file
    current_level_file = LEVELS_DIR / "level7_buildings.json"

    # Load existing
    if current_level_file.exists():
        try:
            with open(current_level_file, "r") as f:
                data = json.load(f)
                # Handle old format (list of dicts) vs new format (dict with metadata)
                if isinstance(data, list):
                    buildings = data
                elif isinstance(data, dict):
                    buildings = data.get("buildings", [])
                    bg_name = data.get("background", "main_background.png")
                    # Try to find bg index
                    if bg_name in bg_names:
                        current_bg_idx = bg_names.index(bg_name)
            print(f"Loaded {len(buildings)} buildings from {current_level_file.name}.")
        except Exception as e:
            print(f"Error loading JSON: {e}")

    running = True
    while running:
        dt = clock.tick(60)

        # Events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            elif event.type == pygame.MOUSEWHEEL:
                if event.y > 0:
                    current_idx = (current_idx - 1) % len(building_names)
                elif event.y < 0:
                    current_idx = (current_idx + 1) % len(building_names)

            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                world_x = mx + cam_x
                world_y = my + cam_y
                
                if event.button == 1: # Left Click - Place
                    buildings.append({
                        "x": int(world_x), 
                        "y": int(world_y),
                        "type": building_names[current_idx]
                    })
                    
                elif event.button == 3: # Right Click - Remove
                    # Find closest building
                    to_remove = None
                    min_dist = 10000
                    for b in buildings:
                        b_type = b.get("type", "house.png")
                        img = building_images.get(b_type)
                        if not img:
                            img = list(building_images.values())[0]
                            
                        bx = b["x"] + img.get_width() // 2
                        by = b["y"] + img.get_height() // 2
                        dist = ((bx - world_x)**2 + (by - world_y)**2)**0.5
                        if dist < 100 and dist < min_dist: # Threshold
                            min_dist = dist
                            to_remove = b
                    
                    if to_remove:
                        buildings.remove(to_remove)

            elif event.type == pygame.KEYDOWN:
                # Background switching
                if event.key == pygame.K_RIGHT:
                    current_bg_idx = (current_bg_idx + 1) % len(bg_names)
                elif event.key == pygame.K_LEFT:
                    current_bg_idx = (current_bg_idx - 1) % len(bg_names)
                
                # Saving
                elif event.key == pygame.K_s:
                    mods = pygame.key.get_mods()
                    if mods & pygame.KMOD_CTRL:
                        # Save As New
                        # Find next available level_X.json
                        i = 1
                        while True:
                            new_path = LEVELS_DIR / f"level_{i}.json"
                            if not new_path.exists():
                                current_level_file = new_path
                                break
                            i += 1
                        print(f"Saving to NEW file: {current_level_file.name}")
                    
                    # Save to current_level_file
                    if not LEVELS_DIR.exists():
                        LEVELS_DIR.mkdir(parents=True)
                        
                    save_data = {
                        "background": bg_names[current_bg_idx],
                        "buildings": buildings
                    }
                    
                    with open(current_level_file, "w") as f:
                        json.dump(save_data, f, indent=4)
                    print(f"Saved to {current_level_file.name}")

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
        if bg_images:
            screen.blit(bg_images[current_bg_idx], (-cam_x, -cam_y))
        else:
            screen.fill((30, 30, 30))

        # Draw Buildings
        for b in buildings:
            b_type = b.get("type", "house.png")
            img = building_images.get(b_type)
            if not img:
                # Fallback to first available or house.png
                img = building_images.get("house.png", list(building_images.values())[0])
            screen.blit(img, (b["x"] - cam_x, b["y"] - cam_y))

        # Draw HUD
        font = pygame.font.SysFont("arial", 20)
        txt = font.render(f"Buildings: {len(buildings)} | Pos: {cam_x},{cam_y}", True, WHITE)
        screen.blit(txt, (10, 10))
        
        # Draw Preview (Top Right)
        curr_name = building_names[current_idx]
        curr_img = building_images[curr_name]
        
        # Draw a background for preview
        prev_rect = curr_img.get_rect()
        # Scale down if too big
        preview_scale = 1.0
        if prev_rect.width > 150 or prev_rect.height > 150:
            preview_scale = 150 / max(prev_rect.width, prev_rect.height)
            
        if preview_scale != 1.0:
            preview_surf = pygame.transform.scale(curr_img, (int(prev_rect.width * preview_scale), int(prev_rect.height * preview_scale)))
        else:
            preview_surf = curr_img
            
        prev_rect = preview_surf.get_rect()
        prev_rect.topright = (SCREEN_WIDTH - 10, 10)
        
        # Background box
        bg_rect = prev_rect.inflate(10, 30)
        bg_rect.topright = (SCREEN_WIDTH - 5, 5)
        pygame.draw.rect(screen, (50, 50, 50), bg_rect)
        pygame.draw.rect(screen, WHITE, bg_rect, 2)
        
        screen.blit(preview_surf, prev_rect)
        
        # Draw name
        name_surf = font.render(curr_name, True, WHITE)
        screen.blit(name_surf, (bg_rect.centerx - name_surf.get_width()//2, prev_rect.bottom + 5))

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
