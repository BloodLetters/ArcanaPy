import pygame
from .settings import MAP_WIDTH, WINDOW_HEIGHT, TILE_SIZE, GRID_COLOR, LEFT_UI_WIDTH

def draw_grid(surface, camera_x=0, camera_y=0, map_width=None, window_height=None):
    """Draws a grid on the given surface, accounting for camera offset and left panel."""
    mw = map_width if map_width is not None else MAP_WIDTH
    wh = window_height if window_height is not None else WINDOW_HEIGHT
    
    start_x = -(camera_x % TILE_SIZE)
    for x in range(start_x, mw + 1, TILE_SIZE):
        screen_x = x + LEFT_UI_WIDTH
        if LEFT_UI_WIDTH <= screen_x <= LEFT_UI_WIDTH + mw:
            pygame.draw.line(surface, GRID_COLOR, (screen_x, 0), (screen_x, wh))
            
    start_y = -(camera_y % TILE_SIZE)
    for y in range(start_y, wh + 1, TILE_SIZE):
        if y >= 0:
            pygame.draw.line(surface, GRID_COLOR, (LEFT_UI_WIDTH, y), (LEFT_UI_WIDTH + mw, y))

def get_grid_pos(mouse_pos, camera_x=0, camera_y=0):
    """Converts a pixel position to a grid coordinate (col, row), accounting for camera offset and left panel."""
    x, y = mouse_pos
    col = (x - LEFT_UI_WIDTH + camera_x) // TILE_SIZE
    row = (y + camera_y) // TILE_SIZE
    return col, row

def get_pixel_pos(grid_pos):
    """Converts a grid coordinate (col, row) to a top-left pixel position."""
    col, row = grid_pos
    x = col * TILE_SIZE
    y = row * TILE_SIZE
    return x, y
