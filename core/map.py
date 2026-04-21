import pygame
import json
import os
from core.settings import TILE_SIZE, WALL_COLOR, MAP_WIDTH, WINDOW_HEIGHT, LEFT_UI_WIDTH
from core.grid import get_pixel_pos

class MapData:
    def __init__(self):
        self.tiles = {} # {(col, row): {"asset": asset_path, "walkable": bool}}
        self.image_cache = {}

    def get_image(self, asset_path):
        if asset_path not in self.image_cache:
            try:
                img = pygame.image.load(asset_path).convert_alpha()
                img = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
                self.image_cache[asset_path] = img
            except Exception as e:
                print(f"Failed to load {asset_path}: {e}")
                self.image_cache[asset_path] = None
        return self.image_cache[asset_path]

    def add_wall(self, col, row, asset_path=None, walkable=False):
        self.tiles[(col, row)] = {
            "asset": asset_path if asset_path else "COLOR",
            "walkable": walkable
        }

    def remove_wall(self, col, row):
        if (col, row) in self.tiles:
            del self.tiles[(col, row)]

    def is_wall(self, col, row):
        if (col, row) in self.tiles:
            return not self.tiles[(col, row)]["walkable"]
        return False

    def draw(self, surface, camera_x=0, camera_y=0, map_width=None, window_height=None):
        mw = map_width if map_width is not None else MAP_WIDTH
        wh = window_height if window_height is not None else WINDOW_HEIGHT
        
        for (col, row), data in self.tiles.items():
            world_x, world_y = get_pixel_pos((col, row))
            screen_x = world_x - camera_x + LEFT_UI_WIDTH
            screen_y = world_y - camera_y
            
            # Optimization: only draw if visible on screen
            if LEFT_UI_WIDTH - TILE_SIZE < screen_x < LEFT_UI_WIDTH + mw and -TILE_SIZE < screen_y < wh:
                asset_path = data["asset"]
                if asset_path == "COLOR":
                    wall_rect = pygame.Rect(screen_x, screen_y, TILE_SIZE, TILE_SIZE)
                    pygame.draw.rect(surface, WALL_COLOR, wall_rect)
                else:
                    img = self.get_image(asset_path)
                    if img:
                        surface.blit(img, (screen_x, screen_y))
                    else:
                        wall_rect = pygame.Rect(screen_x, screen_y, TILE_SIZE, TILE_SIZE)
                        pygame.draw.rect(surface, WALL_COLOR, wall_rect)

    def save(self, filepath):
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        tiles_list = [{"col": k[0], "row": k[1], "asset": v["asset"], "walkable": v["walkable"]} for k, v in self.tiles.items()]
        with open(filepath, 'w') as f:
            json.dump({'tiles': tiles_list}, f)
        print(f"Map saved to {filepath}")

    def load(self, filepath):
        self.tiles.clear()
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                data = json.load(f)
                if 'walls' in data:
                    for w in data['walls']:
                        self.tiles[(w[0], w[1])] = {"asset": "COLOR", "walkable": False}
                elif 'tiles' in data:
                    for t in data['tiles']:
                        # Backward compatibility for old format missing "walkable"
                        walkable = t.get("walkable", False)
                        self.tiles[(t['col'], t['row'])] = {"asset": t['asset'], "walkable": walkable}
            print(f"Map loaded from {filepath}")
        else:
            print(f"Map file {filepath} not found, starting with empty map.")
