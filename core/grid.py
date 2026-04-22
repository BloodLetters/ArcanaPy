import pygame
from .settings import TILE_SIZE, GRID_COLOR

def draw_grid(surface, camera_x=0, camera_y=0, window_width=None, window_height=None):
    """Draws a grid on the given surface, accounting for camera offset."""
    if window_width is None:
        window_width = surface.get_width()
    if window_height is None:
        window_height = surface.get_height()
        
    start_x = -(int(camera_x) % TILE_SIZE)
    for x in range(start_x, window_width + 1, TILE_SIZE):
        pygame.draw.line(surface, GRID_COLOR, (x, 0), (x, window_height))
            
    start_y = -(int(camera_y) % TILE_SIZE)
    for y in range(start_y, window_height + 1, TILE_SIZE):
        pygame.draw.line(surface, GRID_COLOR, (0, y), (window_width, y))

def get_grid_pos(mouse_pos, camera_x=0, camera_y=0):
    """Converts a screen pixel position to a world grid coordinate (col, row), accounting for camera offset."""
    x, y = mouse_pos
    col = int(x + camera_x) // TILE_SIZE
    row = int(y + camera_y) // TILE_SIZE
    return col, row

def get_pixel_pos(grid_pos):
    """Converts a world grid coordinate (col, row) to a top-left world pixel position."""
    col, row = grid_pos
    x = col * TILE_SIZE
    y = row * TILE_SIZE
    return x, y
