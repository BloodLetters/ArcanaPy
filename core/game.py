import sys
import pygame
from core.settings import EDITOR_WIDTH, EDITOR_HEIGHT, FPS, BG_COLOR, TILE_SIZE, MAP_FILE, ENEMY_SPAWN_DISTANCE
from core.grid import draw_grid, get_grid_pos
from core.map import MapData
from entities.player import Player
from entities.enemy import Enemy
import random

class Game:
    def __init__(self):
        pygame.init()
        self.window_width = EDITOR_WIDTH
        self.window_height = EDITOR_HEIGHT
        self.screen = pygame.display.set_mode((self.window_width, self.window_height), pygame.RESIZABLE)
        pygame.display.set_caption("ArcanaPy")
        self.clock = pygame.time.Clock()
        self.running = True
        self.camera_x = 0
        self.camera_y = 0

        self.icon = pygame.image.load("preview/images/icon-379x300.png")
        pygame.display.set_icon(self.icon)
        
        self.map_data = MapData()
        self.map_data.load(MAP_FILE)
    
        start_col, start_row = 0, 0
        for (col, row), data in self.map_data.tiles.items():
            if data.get("walkable", False):
                start_col, start_row = col, row
                break
                
        self.player = Player(start_col, start_row, self.map_data)
        self.player.on_step_callback = self._on_player_step
        self.player.is_occupied_callback = self._is_occupied
        
        self.enemies = []
        self.spawn_enemy()

    def _is_occupied(self, col, row):
        return any(e.grid_pos == (col, row) or e.target_grid_pos == (col, row) for e in self.enemies)

    def _on_player_step(self):
        for enemy in self.enemies:
            enemy.take_turn(self.player.grid_pos)

    def spawn_enemy(self):
        # Find a valid spawn location
        valid_spots = []
        p_col, p_row = self.player.grid_pos
        for dx in range(-ENEMY_SPAWN_DISTANCE, ENEMY_SPAWN_DISTANCE + 1):
            dy = ENEMY_SPAWN_DISTANCE - abs(dx)
            for y_offset in set([dy, -dy]):
                c = p_col + dx
                r = p_row + y_offset
                if not self.map_data.is_wall(c, r):
                    valid_spots.append((c, r))
                    
        if valid_spots:
            spawn_col, spawn_row = random.choice(valid_spots)
            self.enemies.append(Enemy("enemy_1", spawn_col, spawn_row, self.map_data))
        else:
            print("Warning: Could not find a valid spawn location for the enemy.")

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.VIDEORESIZE:
                self.window_width = event.w
                self.window_height = event.h
                self.screen = pygame.display.set_mode((self.window_width, self.window_height), pygame.RESIZABLE)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    mouse_pos = pygame.mouse.get_pos()
                    col, row = get_grid_pos(mouse_pos, self.camera_x, self.camera_y)
                    if not self.map_data.is_wall(col, row):
                        self.player.set_target(col, row)

    def update(self, dt):
        self.player.update(dt)
        for enemy in self.enemies:
            enemy.update(dt)
            
        self.map_data.script_runtime.update(dt)
        
        # Make camera follow player
        self.camera_x = self.player.pixel_pos[0] - self.window_width / 2 + TILE_SIZE / 2
        self.camera_y = self.player.pixel_pos[1] - self.window_height / 2 + TILE_SIZE / 2

    def draw(self):
        self.screen.fill(BG_COLOR)
        self.map_data.draw(self.screen, self.camera_x, self.camera_y, self.window_width, self.window_height)
        draw_grid(self.screen, self.camera_x, self.camera_y, self.window_width, self.window_height)
        for enemy in self.enemies:
            enemy.draw(self.screen, self.camera_x, self.camera_y)
        self.player.draw(self.screen, self.camera_x, self.camera_y)
        pygame.display.flip()

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0  # Delta time in seconds
            self.handle_events()
            self.update(dt)
            self.draw()
            
        pygame.quit()
        sys.exit()
