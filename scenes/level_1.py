import random
import pygame
from scenes.base_level import BaseLevel
from objects.ranged_enemy import RangedEnemy


class Level_1(BaseLevel):
    def __init__(self, screen, game_state_manager, clock):
        # Initialize with custom BPM and background for Level 1
        super().__init__(
            screen, 
            game_state_manager, 
            clock, 
            bpm=120,  # Custom BPM for this level
            path_to_background="assets/pictures/backgrounds/level1_background.png"  # Custom background
        )
        
        self.name = "Level_1"
        
        # Level 1 specific settings
        self.spawn_interval = 3000  # Spawn every 3 seconds
        self.max_enemies = 10  # Maximum enemies on screen
        self.wave_number = 1
        self.enemies_spawned_this_wave = 0
        
        # Level completion tracking
        self.total_waves = 5  # Complete 5 waves to finish level
        self.enemies_killed = 0
        self.level_completed = False
        
        # First enemy flag
        self.first_enemy_spawned = False
        self.spawn_timer_active = False
        
        # Tutorial flags
        self.showed_attack_tutorial = False
        self.showed_dash_tutorial = False
        
        # Spawn the first enemy immediately
        self._spawn_first_enemy()
    
    
    def _spawn_first_enemy(self):
        """Spawn the very first enemy to start the level."""
        x = self.bg_width // 2
        y = -50  # Spawn from top center
        
        enemy = RangedEnemy(x, y, self.WIDTH, self.HEIGHT, 0.25, self.player)
        enemy.camera = self.camera
        enemy.map_width = self.bg_width
        enemy.map_height = self.bg_height
        
        self.enemies.append(enemy)
        self.first_enemy_spawned = True
        self.showed_attack_tutorial = True
        print("[LEVEL_1] First enemy spawned! Kill it to start the waves.")
    
    
    def get_enemies_per_wave(self):
        """Get number of enemies for current wave - increases each wave."""
        return self.wave_number  # Wave 1 = 1 enemy, Wave 2 = 2 enemies, etc.
    
    
    def spawnEnemies(self):
        """Custom spawn logic for Level 1 - spawns enemies in waves."""
        # Don't spawn until first enemy is dead
        if not self.spawn_timer_active:
            return
        
        # Don't spawn if level is completed
        if self.level_completed:
            return
        
        # Don't spawn if we reached max waves
        if self.wave_number > self.total_waves:
            return
        
        # Don't spawn if we have too many enemies
        if len(self.enemies) >= self.max_enemies:
            return
        
        # Get enemies per wave (progressive difficulty)
        enemies_needed = self.get_enemies_per_wave()
        
        # Check if wave is complete
        if self.enemies_spawned_this_wave >= enemies_needed:
            # Wait for all enemies to be cleared before next wave
            if len(self.enemies) == 0:
                self.wave_number += 1
                self.enemies_spawned_this_wave = 0
                
                if self.wave_number <= self.total_waves:
                    print(f"[LEVEL_1] Starting Wave {self.wave_number}/{self.total_waves} ({self.get_enemies_per_wave()} enemies)")
                else:
                    print(f"[LEVEL_1] All waves completed!")
                return
        
        # Spawn from specific sides based on wave number
        if self.wave_number % 2 == 0:
            # Even waves: spawn from left and right
            side = random.choice([1, 3])  # 1=right, 3=left
        else:
            # Odd waves: spawn from top and bottom
            side = random.choice([0, 2])  # 0=top, 2=bottom
        
        # Calculate spawn position
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
        
        # Create enemy with level-appropriate scaling
        enemy_scale = 0.25 - (self.wave_number * 0.01)
        enemy_scale = max(0.15, enemy_scale)
        
        enemy = RangedEnemy(x, y, self.WIDTH, self.HEIGHT, enemy_scale, self.player)
        enemy.camera = self.camera
        enemy.map_width = self.bg_width
        enemy.map_height = self.bg_height
        
        # Make enemies stronger each wave
        enemy.max_health = 60 + (self.wave_number * 10)
        enemy.current_health = enemy.max_health
        enemy.damage = 5 + (self.wave_number * 2)
        
        self.enemies.append(enemy)
        self.enemies_spawned_this_wave += 1
        
        print(f"[LEVEL_1] Spawned enemy {self.enemies_spawned_this_wave}/{self.get_enemies_per_wave()} (Wave {self.wave_number}/{self.total_waves})")
    
    
    def level_specific_functions(self):
        """Level 1 specific mechanics."""
        # Activate spawn timer after first enemy is killed
        if self.first_enemy_spawned and not self.spawn_timer_active and len(self.enemies) == 0:
            self.spawn_timer_active = True
            print("[LEVEL_1] First enemy defeated! Starting wave spawns...")
        
        # Show dash tutorial in wave 4 (last two waves)
        if self.wave_number >= 4 and not self.showed_dash_tutorial:
            self.showed_dash_tutorial = True
            print("[LEVEL_1] Dash tutorial activated!")
        
        # Check for level completion
        if not self.level_completed:
            if self.wave_number > self.total_waves and len(self.enemies) == 0:
                self.complete_level()
    
    
    def complete_level(self):
        """Handle level completion."""
        self.level_completed = True
        print(f"[LEVEL_1] LEVEL COMPLETED! Total enemies killed: {self.enemies_killed}")
        
        # Wait 3 seconds then switch to next level
        pygame.time.wait(3000)
        
        # Switch to next level (change "level_2" to your next level's state name)
        self.game_state_manager.set_state("level_2")
    
    
    def update(self):
        """Override update to track enemy deaths and control spawn timer."""
        # Store initial enemy count
        initial_count = len(self.enemies)
        
        # Only run spawn timer if activated
        if not self.spawn_timer_active:
            self.spawn_timer = 0  # Reset timer until activated
        
        # Call base update
        super().update()
        
        # Check if any enemies died
        enemies_died = initial_count - len(self.enemies)
        if enemies_died > 0:
            self.enemies_killed += enemies_died
            print(f"[LEVEL_1] Enemy killed! Total: {self.enemies_killed}")
    
    def draw(self):
        """Override draw to add level-specific UI."""
        # Call base draw
        super().draw()
        
        # Font setup
        font = pygame.font.Font(None, 36)
        tutorial_font = pygame.font.Font(None, 48)
        
        # Tutorial messages in corner
        tutorial_y = 130  # Start below the kills counter
        
        if not self.spawn_timer_active and self.showed_attack_tutorial:
            # Show attack tutorial
            tutorial_text = tutorial_font.render("[L_MYSZ] - GITARA", True, (255, 255, 0))
            self.screen.blit(tutorial_text, (10, tutorial_y))
        
        # Show dash tutorial in last two waves
        if self.showed_dash_tutorial and self.wave_number >= 4 and self.wave_number <= self.total_waves:
            dash_text = tutorial_font.render("[SHIFT] - DASH", True, (0, 255, 255))
            self.screen.blit(dash_text, (10, tutorial_y + 50))
        
        # Wave counter
        if self.spawn_timer_active:
            wave_text = font.render(f"Wave: {self.wave_number}/{self.total_waves}", True, (255, 255, 255))
            self.screen.blit(wave_text, (10, 10))
        
        # Enemy and kill counters
        enemies_text = font.render(f"Enemies: {len(self.enemies)}", True, (255, 255, 255))
        self.screen.blit(enemies_text, (10, 50))
        
        kills_text = font.render(f"Kills: {self.enemies_killed}", True, (255, 255, 255))
        self.screen.blit(kills_text, (10, 90))
        
        # Show completion message
        if self.level_completed:
            completion_font = pygame.font.Font(None, 72)
            completion_text = completion_font.render("LEVEL COMPLETE!", True, (0, 255, 0))
            text_rect = completion_text.get_rect(center=(self.WIDTH // 2, self.HEIGHT // 2))
            self.screen.blit(completion_text, text_rect) 