import sys
import pygame
from core.settings import WINDOW_WIDTH, WINDOW_HEIGHT, FPS, BG_COLOR, TILE_SIZE, MAP_FILE
from core.grid import draw_grid, get_grid_pos
from core.map import MapData
from entities.player import Player

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("ArcanaPy")
        self.clock = pygame.time.Clock()
        self.running = True

        self.icon = pygame.image.load("preview/images/icon-379x300.png")
        pygame.display.set_icon(self.icon)
        
        self.map_data = MapData()
        self.map_data.load(MAP_FILE)
    
        start_col = (WINDOW_WIDTH // 2) // TILE_SIZE
        start_row = (WINDOW_HEIGHT // 2) // TILE_SIZE
        self.player = Player(start_col, start_row, self.map_data)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    mouse_pos = pygame.mouse.get_pos()
                    col, row = get_grid_pos(mouse_pos)
                    if not self.map_data.is_wall(col, row):
                        self.player.set_target(col, row)

    def update(self, dt):
        self.player.update(dt)
        self.map_data.script_runtime.update(dt)

    def draw(self):
        self.screen.fill(BG_COLOR)
        self.map_data.draw(self.screen)
        draw_grid(self.screen)
        self.player.draw(self.screen)
        pygame.display.flip()

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0  # Delta time in seconds
            self.handle_events()
            self.update(dt)
            self.draw()
            
        pygame.quit()
        sys.exit()
