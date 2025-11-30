class Camera:
    def __init__(self, map_width, map_height, screen_width, screen_height, box_w=800, box_h=600):
        self.map_width = map_width
        self.map_height = map_height
        self.screen_width = screen_width
        self.screen_height = screen_height

        # camera dead-zone (smaller box)
        self.box_w = box_w
        self.box_h = box_h
        self.box_x = (screen_width - box_w) // 2
        self.box_y = (screen_height - box_h) // 2

        # camera top-left in world coordinates
        self.x = 0
        self.y = 0

    def update(self, player):
        """Keep camera always centered on the player, clamped to map edges"""
        # target camera position so that player is centered
        self.x = player.rect.centerx - self.screen_width // 2
        self.y = player.rect.centery - self.screen_height // 2

        # clamp to map boundaries
        self.x = max(0, min(self.x, self.map_width - self.screen_width))
        self.y = max(0, min(self.y, self.map_height - self.screen_height))

    def apply(self, rect):
        """Return rect relative to camera for drawing"""
        return rect.move(-self.x, -self.y)