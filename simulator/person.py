"""Moving agents; no graphics or global simulation state."""
import math
import random

class Person:
    def __init__(self, center, factors, rng=random):
        self.x, self.y = center
        angle = rng.uniform(0, math.tau)
        self.dx, self.dy = math.cos(angle), math.sin(angle)
        self.stationary = rng.randrange(100) < factors[2]
        self.state = "sick" if rng.randrange(100) < factors[6] else "healthy"
        self.start_day = 0

    def move(self):
        if self.stationary:
            return
        self.x += self.dx
        self.y += self.dy
        if self.x < 24 or self.x > 776:
            self.x = min(776, max(24, self.x))
            self.dx *= -1
        if self.y < 104 or self.y > 576:
            self.y = min(576, max(104, self.y))
            self.dy *= -1

