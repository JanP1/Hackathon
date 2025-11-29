import pygame
from objects.game_object import GameObject

class BPMCounter(GameObject):
    def __init__(self, x_pos: int, y_pos: int, SCREEN_W: int, SCREEN_H: int, bpm: int = 120, bar_count: int = 8):
        """
        BPM Counter with VERTICAL bars and pulsating center sprite.
        
        Args:
            x_pos: X position on screen
            y_pos: Y position on screen (center)
            SCREEN_W: Screen width
            SCREEN_H: Screen height
            bpm: Beats per minute
            bar_count: Number of bars on each side of center
        """
        super().__init__(x_pos, y_pos, SCREEN_W, SCREEN_H, "bpm_counter")
        
        self.bpm = bpm
        self.bar_count = bar_count
        
        # Timing
        self.beat_duration = 60000 / bpm  # milliseconds per beat
        self.current_time = 0
        self.beat_progress = 0  # 0 to 1
        
        # Bar settings (VERTICAL)
        self.bar_width = 150
        self.bar_height = 20
        self.bar_spacing = 120  # 3x the original 40
        
        # Colors
        self.bar_color = (255, 255, 255)
        self.active_bar_color = (255, 215, 0)  # Gold
        self.center_color = (255, 50, 50)
        
        # Center rectangle
        self.center_size = 50
        self.pulse_scale = 1.0
        self.max_pulse_scale = 1.5

        self.is_active = True
    
    
    def set_bpm(self, bpm: int):
        """Change the BPM."""
        self.bpm = bpm
        self.beat_duration = 60000 / bpm
    
    
    def update(self, delta_time: float):
        """
        Update the counter.
        
        Args:
            delta_time: Time passed since last frame in milliseconds
        """
        self.current_time += delta_time
        self.beat_progress = (self.current_time % self.beat_duration) / self.beat_duration
        
        # Pulse animation (peaks at beat)
        if self.beat_progress < 0.2:  # Pulse at start of beat
            self.pulse_scale = 1 + (self.max_pulse_scale - 1) * (1 - self.beat_progress / 0.2)
        else:
            self.pulse_scale = 1.0
    
    
    def draw(self, screen):
        """Draw the BPM counter VERTICALLY."""
        if not self.is_active:
            return
            
        # Draw bars moving towards center from TOP and BOTTOM
        for i in range(self.bar_count):
            # Calculate distance from center (inverted so bars move TOWARDS center)
            bar_distance = (self.bar_count - i - 1 + (1 - self.beat_progress)) * self.bar_spacing
            
            # Top bars (moving down towards center)
            bar_y_top = self.rect.y - bar_distance
            
            # Bottom bars (moving up towards center)
            bar_y_bottom = self.rect.y + bar_distance
            
            # Determine if this is the active bar (closest to center)
            is_active = i == (self.bar_count - 1) and self.beat_progress > 0.8
            color = self.active_bar_color if is_active else self.bar_color
            
            # Draw top bar
            bar_rect_top = pygame.Rect(
                int(self.rect.x - self.bar_width // 2),
                int(bar_y_top - self.bar_height // 2),
                self.bar_width,
                self.bar_height
            )
            pygame.draw.rect(screen, color, bar_rect_top)
            
            # Draw bottom bar
            bar_rect_bottom = pygame.Rect(
                int(self.rect.x - self.bar_width // 2),
                int(bar_y_bottom - self.bar_height // 2),
                self.bar_width,
                self.bar_height
            )
            pygame.draw.rect(screen, color, bar_rect_bottom)
        
        # Draw pulsating center rectangle
        scaled_size = int(self.center_size * self.pulse_scale)
        center_rect = pygame.Rect(
            int(self.rect.x - scaled_size // 2),
            int(self.rect.y - scaled_size // 2),
            scaled_size,
            scaled_size
        )
        pygame.draw.rect(screen, self.center_color, center_rect)
    
    
    def is_on_beat(self, tolerance: float = 0.15) -> bool:
        """
        Check if current time is close to a beat.
        
        Args:
            tolerance: How close to beat (0.0 to 0.5, where 0.15 = 15% of beat duration)
        
        Returns:
            True if within tolerance of a beat
        """
        return self.beat_progress < tolerance or self.beat_progress > (1 - tolerance)
    
    
    def get_beat_number(self) -> int:
        """Get the current beat number."""
        return int(self.current_time / self.beat_duration)