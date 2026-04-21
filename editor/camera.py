from core.settings import TILE_SIZE, LEFT_UI_WIDTH

class Camera:
    def __init__(self):
        self.x = 0.0
        self.y = 0.0
        self.zoom = 1.0
        self.min_zoom = 0.25
        self.max_zoom = 4.0
        self.pan_speed = 6

    @property
    def tile_size(self):
        return int(TILE_SIZE * self.zoom)

    def pan(self, dx, dy):
        self.x -= dx / self.zoom
        self.y -= dy / self.zoom

    def zoom_at(self, mouse_pos, direction, canvas_x_offset=0):
        old_zoom = self.zoom
        factor = 1.15 if direction > 0 else 1.0 / 1.15
        self.zoom = max(self.min_zoom, min(self.max_zoom, self.zoom * factor))

        mx = mouse_pos[0] - canvas_x_offset
        my = mouse_pos[1]
        self.x += mx * (1.0 / old_zoom - 1.0 / self.zoom)
        self.y += my * (1.0 / old_zoom - 1.0 / self.zoom)

    def screen_to_world(self, screen_pos, canvas_x_offset=0):
        sx = screen_pos[0] - canvas_x_offset
        sy = screen_pos[1]
        wx = sx / self.zoom + self.x
        wy = sy / self.zoom + self.y
        return wx, wy

    def screen_to_grid(self, screen_pos, canvas_x_offset=0):
        wx, wy = self.screen_to_world(screen_pos, canvas_x_offset)
        col = int(wx // TILE_SIZE)
        row = int(wy // TILE_SIZE)
        return col, row

    def world_to_screen(self, world_x, world_y, canvas_x_offset=0):
        sx = (world_x - self.x) * self.zoom + canvas_x_offset
        sy = (world_y - self.y) * self.zoom
        return sx, sy

    def grid_to_screen(self, col, row, canvas_x_offset=0):
        wx = col * TILE_SIZE
        wy = row * TILE_SIZE
        return self.world_to_screen(wx, wy, canvas_x_offset)

    def update_keys(self, keys):
        import pygame
        if keys[pygame.K_LEFT]:
            self.x -= self.pan_speed / self.zoom
        if keys[pygame.K_RIGHT]:
            self.x += self.pan_speed / self.zoom
        if keys[pygame.K_UP]:
            self.y -= self.pan_speed / self.zoom
        if keys[pygame.K_DOWN]:
            self.y += self.pan_speed / self.zoom

    def get_zoom_percent(self):
        return int(self.zoom * 100)
