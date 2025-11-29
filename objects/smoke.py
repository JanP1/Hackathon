# smoke.py

import pygame
import random
import math

class SmokeParticle(pygame.sprite.Sprite):
    def __init__(self, x, y, angle, speed, color, size, lifespan, border=0):
        super().__init__()
        self.x = x
        self.y = y
        self.angle = angle
        self.speed = speed
        self.color = color
        self.size = size
        self.lifespan = lifespan
        self.age = 0
        self.border = border

    def update(self):
        self.x += math.cos(self.angle) * self.speed
        self.y += math.sin(self.angle) * self.speed
        self.age += 1

    def draw(self, surface):
        if self.age > self.lifespan:
            return

        # Create a subsurface for the particle
        particle_rect = pygame.Rect(self.x - self.size, self.y - self.size, self.size * 2, self.size * 2)
        
        # Ensure the particle is within the screen boundaries
        particle_rect = particle_rect.clamp(surface.get_rect())
        if particle_rect.width == 0 or particle_rect.height == 0:
            return

        try:
            sub_surface = surface.subsurface(particle_rect).copy()
        except ValueError:
            # This can happen if the particle is outside the screen
            return

        # Create a distortion effect (e.g., a ripple)
        temp_surface = sub_surface.copy()
        for x in range(sub_surface.get_width()):
            for y in range(sub_surface.get_height()):
                # Calculate the distance from the center of the particle
                dx = x - self.size
                dy = y - self.size
                dist = math.sqrt(dx*dx + dy*dy)

                # Create a ripple effect
                if dist < self.size:
                    new_x = x + int(math.sin(dist * 0.5 + self.age * 0.5) * 2)
                    new_y = y + int(math.cos(dist * 0.5 + self.age * 0.5) * 2)

                    if 0 <= new_x < sub_surface.get_width() and 0 <= new_y < sub_surface.get_height():
                        color = temp_surface.get_at((new_x, new_y))
                        sub_surface.set_at((x, y), color)

        # Blend the distorted surface back onto the main surface
        surface.blit(sub_surface, particle_rect)

        # Draw the border on top
        if self.border == 1:
            alpha = 255 * (1 - self.age / self.lifespan)
            pygame.draw.circle(surface, (255, 255, 255, alpha), (int(self.x), int(self.y)), int(self.size), 1)


class SmokeTrail:
    def __init__(self, border=0):
        self.particles = []
        self.border = border

    def add_particle(self, x, y, dx, dy):
        if dx == 0 and dy == 0:
            return
        angle = math.atan2(dy, dx) + math.pi
        for _ in range(5):
            speed = random.uniform(0.5, 2)
            size = random.uniform(2, 6)
            lifespan = random.randint(20, 50)
            p_angle = angle + random.uniform(-0.5, 0.5)
            particle = SmokeParticle(x, y, p_angle, speed, (200, 200, 200), size, lifespan, self.border)
            self.particles.append(particle)

    def update(self):
        for particle in self.particles:
            particle.update()
        self.particles = [p for p in self.particles if p.age <= p.lifespan]

    def draw(self, surface):
        for particle in self.particles:
            particle.draw(surface)
