import random
import pygame
from scenes.base_level import BaseLevel
from objects.ranged_enemy import RangedEnemy
from objects.enemy_close import CloseEnemy


class Level_2(BaseLevel):
    def __init__(self, screen, game_state_manager, clock):
        # Initialize with custom BPM and background for Level 2
        super().__init__(
            screen, 
            game_state_manager, 
            clock, 
            bpm=140,  # Faster BPM than Level 1
            path_to_background="assets/pictures/backgrounds/level2_background.png"
        )
        
        self.name = "Level_2"
        
        # Level 2 specific settings
        self.spawn_interval = 2500  # Faster spawning
        self.max_enemies = 8
        self.current_wave = 1
        self.total_waves = 5
        
        # Wave configuration: {wave_number: {'ranged': count, 'close': count}}
        self.wave_config = {
            1: {'ranged': 2, 'close': 0},   # Wave 1: 2 ranged
            2: {'ranged': 2, 'close': 1},   # Wave 2: 2 ranged + 1 close
            3: {'ranged': 3, 'close': 1},   # Wave 3: 3 ranged + 1 close
            4: {'ranged': 3, 'close': 2},   # Wave 4: 3 ranged + 2 close
            5: {'ranged': 4, 'close': 2},   # Wave 5: 4 ranged + 2 close
        }
        
        # Tracking
        self.enemies_killed = 0
        self.total_enemies_to_kill = self._calculate_total_enemies()
        self.enemies_spawned_this_wave = 0
        self.wave_complete = False
        self.level_completed = False
        
        # Start first wave automatically
        self.spawn_timer_active = True
    
    
    def _calculate_total_enemies(self):
        """Calculate total enemies across all waves."""
        total = 0
        for wave_num in range(1, self.total_waves + 1):
            config = self.wave_config[wave_num]
            total += config['ranged'] + config['close']
        return total
    
    
    def get_enemies_for_wave(self, wave_num):
        """Get enemy configuration for given wave."""
        return self.wave_config.get(wave_num, {'ranged': 0, 'close': 0})
    
    
    def skip_wave(self):
        """Skip current wave (cheat for testing)."""
        if self.current_wave > self.total_waves:
            return
        
        # Kill all enemies
        for enemy in self.enemies[:]:
            enemy.is_alive = False
            enemy.is_active = False
        self.enemies.clear()
        
        # Advance to next wave
        self.current_wave += 1
        self.enemies_spawned_this_wave = 0
        self.wave_complete = False
        
        if self.current_wave <= self.total_waves:
            print(f"[LEVEL_2] Skipped to Wave {self.current_wave}/{self.total_waves}")
        else:
            print(f"[LEVEL_2] Skipped to completion!")
    
    
    def spawnEnemies(self):
        """Custom spawn logic for Level 2 - mixed enemy types."""
        # Don't spawn if level completed
        if self.level_completed:
            return
        
        # Don't spawn if wave completed
        if self.current_wave > self.total_waves:
            return
        
        # Don't spawn if too many enemies
        if len(self.enemies) >= self.max_enemies:
            return
        
        # Get current wave config
        wave_enemies = self.get_enemies_for_wave(self.current_wave)
        total_wave_enemies = wave_enemies['ranged'] + wave_enemies['close']
        
        # Check if all enemies for this wave are spawned
        if self.enemies_spawned_this_wave >= total_wave_enemies:
            # Wait for wave to clear
            if len(self.enemies) == 0 and not self.wave_complete:
                self.wave_complete = True
                self.current_wave += 1
                self.enemies_spawned_this_wave = 0
                self.wave_complete = False
                
                if self.current_wave <= self.total_waves:
                    print(f"[LEVEL_2] Starting Wave {self.current_wave}/{self.total_waves}")
                else:
                    print(f"[LEVEL_2] All waves completed!")
            return
        
        # Determine which type to spawn based on wave config
        ranged_spawned = sum(1 for e in self.enemies if isinstance(e, RangedEnemy))
        close_spawned = sum(1 for e in self.enemies if isinstance(e, CloseEnemy))
        
        spawn_ranged = ranged_spawned < wave_enemies['ranged']
        spawn_close = close_spawned < wave_enemies['close']
        
        # Prioritize spawning close enemies first (more dangerous)
        if spawn_close and wave_enemies['close'] > 0:
            enemy_type = 'close'
        elif spawn_ranged and wave_enemies['ranged'] > 0:
            enemy_type = 'ranged'
        else:
            return  # Nothing to spawn
        
        # Calculate spawn position
        side = random.randint(0, 3)
        
        if side == 0:  # Top
            x = random.randint(100, self.bg_width - 100)
            y = -50
        elif side == 1:  # Right
            x = self.bg_width + 50
            y = random.randint(100, self.bg_height - 100)
        elif side == 2:  # Bottom
            x = random.randint(100, self.bg_width - 100)
            y = self.bg_height + 50
        else:  # Left
            x = -50
            y = random.randint(100, self.bg_height - 100)
        
        # Create enemy based on type
        if enemy_type == 'ranged':
            enemy = RangedEnemy(x, y, self.WIDTH, self.HEIGHT, 0.25, self.player)
            enemy.max_health = 60 + (self.current_wave * 10)
            enemy.current_health = enemy.max_health
            enemy.damage = 5 + (self.current_wave * 2)
        else:  # close
            enemy = CloseEnemy(x, y, self.WIDTH, self.HEIGHT, 0.3, self.player)
            enemy.max_health = 40 + (self.current_wave * 5)
            enemy.current_health = enemy.max_health
            enemy.damage = 20 + (self.current_wave * 3)
        
        # Set common properties
        enemy.camera = self.camera
        enemy.map_width = self.bg_width
        enemy.map_height = self.bg_height
        
        self.enemies.append(enemy)
        self.enemies_spawned_this_wave += 1
        
        print(f"[LEVEL_2] Spawned {enemy_type} enemy ({self.enemies_spawned_this_wave}/{total_wave_enemies}) Wave {self.current_wave}")
    
    
    def level_specific_functions(self):
        """Level 2 specific mechanics."""
        # Check for right mouse click to skip wave
        mouse_buttons = pygame.mouse.get_pressed()
        if mouse_buttons[2]:  # Right click (index 2)
            self.skip_wave()
        
        # Check for level completion
        if not self.level_completed:
            if self.current_wave > self.total_waves and len(self.enemies) == 0:
                self.complete_level()
    
    
    def complete_level(self):
        """Handle level completion."""
        self.level_completed = True
        print(f"[LEVEL_2] LEVEL COMPLETED! Total enemies killed: {self.enemies_killed}/{self.total_enemies_to_kill}")
        
        # Wait 3 seconds then switch to next level
        pygame.time.wait(3000)
        
        # Switch to next level or back to menu
        self.game_state_manager.set_state("level_3")  # Change to your next level
    
    
    def update(self):
        """Override update to track enemy deaths."""
        # Store initial enemy count
        initial_count = len(self.enemies)
        
        # Call base update
        super().update()
        
        # Check if any enemies died
        enemies_died = initial_count - len(self.enemies)
        if enemies_died > 0:
            self.enemies_killed += enemies_died
            print(f"[LEVEL_2] Enemy killed! Total: {self.enemies_killed}/{self.total_enemies_to_kill}")
    
    
    def draw(self):
        """Override draw to add level-specific UI."""
        # Call base draw
        super().draw()
        
        # Font setup
        font = pygame.font.Font(None, 36)
        
        # Wave counter
        wave_text = font.render(f"Wave: {self.current_wave}/{self.total_waves}", True, (255, 255, 255))
        self.screen.blit(wave_text, (10, 10))
        
        # Kill counter
        kills_text = font.render(f"Killed: {self.enemies_killed}/{self.total_enemies_to_kill}", True, (255, 255, 255))
        self.screen.blit(kills_text, (10, 50))
        
        # Debug hint
        debug_text = font.render("[Right Click] Skip Wave", True, (128, 128, 128))
        self.screen.blit(debug_text, (10, 90))
        
        # Show completion message
        if self.level_completed:
            completion_font = pygame.font.Font(None, 72)
            completion_text = completion_font.render("LEVEL COMPLETE!", True, (0, 255, 0))
            text_rect = completion_text.get_rect(center=(self.WIDTH // 2, self.HEIGHT // 2))
            self.screen.blit(completion_text, text_rect)