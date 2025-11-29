import pygame
import math
from objects.game_object import GameObject

class BPMCounter(GameObject):
    def __init__(self, x_pos: int, y_pos: int, SCREEN_W: int, SCREEN_H: int, scale: float = 1, bpm: int = 120):
        """
        Simple BPM Counter with moving rectangle and static rectangle.
        
        Args:
            x_pos: X position on screen (center)
            y_pos: Y position on screen (bottom pivot point)
            SCREEN_W: Screen width
            SCREEN_H: Screen height
            bpm: Beats per minute
        """
        super().__init__(x_pos, y_pos, SCREEN_W, SCREEN_H, scale, "bpm_counter")
        
        self.bpm = bpm
        
        # Timing
        self.beat_duration = 60000 / bpm  # milliseconds per beat
        self.current_time = 0
        self.beat_progress = 0  # 0 to 1
        
        # Rectangle settings
        self.rect_width = 50
        self.rect_height = 200
        
        self.rect_moving_width = 20
        self.rect_moving_height = 200
        
        # Max angle for windshield wiper motion (in radians)
        self.max_angle = math.pi / 3  # 60 degrees total swing

        # Colors
        self.static_color = (100, 100, 255)  # Blue
        self.moving_color = (255, 100, 100)  # Red
        
        # Pulse effect
        self.pulse_scale = 1.0
        self.max_pulse_scale = 1.3

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
        
        # Pulse when beat hits (beat_progress near 0)
        center_tolerance = 0.25
        if self.beat_progress < center_tolerance:
            progress = self.beat_progress / center_tolerance
            self.pulse_scale = 1.0 + (self.max_pulse_scale - 1.0) * (1.0 - progress)
        else:
            self.pulse_scale = 1.0
    
    
    def draw(self, screen):
        """Draw the rectangles."""
        if not self.is_active:
            return
        
        # Apply pulse scale
        rect_width = int(self.rect_width * self.pulse_scale)
        rect_height = int(self.rect_height * self.pulse_scale)
        
        moving_width = int(self.rect_moving_width * self.pulse_scale)
        moving_height = int(self.rect_moving_height * self.pulse_scale)
        
        # Pivot point (bottom center)
        pivot_x = self.rect.x
        pivot_y = self.rect.y
        
        # Static rectangle (vertical, pivoting from bottom)
        static_points = [
            (pivot_x - rect_width // 2, pivot_y),  # Bottom left
            (pivot_x + rect_width // 2, pivot_y),  # Bottom right
            (pivot_x + rect_width // 2, pivot_y - rect_height),  # Top right
            (pivot_x - rect_width // 2, pivot_y - rect_height),  # Top left
        ]
        pygame.draw.polygon(screen, self.static_color, static_points)
        
        # Moving rectangle (windshield wiper motion)
        # Calculate angle based on beat progress (-max_angle to +max_angle)
        angle = math.sin(self.beat_progress * 2 * math.pi) * self.max_angle
        
        # Calculate the four corners of the rotated rectangle
        # Bottom corners stay at pivot
        bottom_left = (pivot_x - moving_width // 2, pivot_y)
        bottom_right = (pivot_x + moving_width // 2, pivot_y)
        
        # Top corners rotate around pivot
        # Start with vertical position, then rotate
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        
        # Left top corner
        local_x = -moving_width // 2
        local_y = -moving_height
        top_left_x = pivot_x + (local_x * cos_a - local_y * sin_a)
        top_left_y = pivot_y + (local_x * sin_a + local_y * cos_a)
        
        # Right top corner
        local_x = moving_width // 2
        local_y = -moving_height
        top_right_x = pivot_x + (local_x * cos_a - local_y * sin_a)
        top_right_y = pivot_y + (local_x * sin_a + local_y * cos_a)
        
        moving_points = [
            bottom_left,
            bottom_right,
            (top_right_x, top_right_y),
            (top_left_x, top_left_y)
        ]
        pygame.draw.polygon(screen, self.moving_color, moving_points)
    
    
    def is_on_beat(self, tolerance: float = 0.15) -> bool:
        """
        Check if current time is close to a beat.
        
        Args:
            tolerance: How close to beat (0.0 to 0.5)
        
        Returns:
            True if within tolerance of a beat
        """
        return self.beat_progress < tolerance or self.beat_progress > (1 - tolerance)
    
    
    def get_beat_number(self) -> int:
        """Get the current beat number."""
        return int(self.current_time / self.beat_duration)