"""
Map data for game runtime.
Supports both old flat format and new layered format (via LayerManager).
For game runtime, loads all layers and merges them for rendering/collision.
"""
import pygame
import json
import os
from core.settings import TILE_SIZE, WALL_COLOR
from core.grid import get_pixel_pos
from core.script_manager import ScriptRuntime


class MapData:
    """Game-compatible map data. Loads layered or legacy formats into a flat tile dict."""

    def __init__(self):
        self.tiles = {}  # {(col, row): {"asset": str, "walkable": bool, "scripts": list, "properties": dict}}
        self.image_cache = {}
        self.script_runtime = ScriptRuntime()

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

    def add_wall(self, col, row, asset_path=None, walkable=False, scripts=None, properties=None):
        self.tiles[(col, row)] = {
            "asset": asset_path if asset_path else "COLOR",
            "walkable": walkable,
            "scripts": scripts or [],
            "properties": properties or {},
        }

    def remove_wall(self, col, row):
        if (col, row) in self.tiles:
            del self.tiles[(col, row)]

    def is_wall(self, col, row):
        if (col, row) in self.tiles:
            return not self.tiles[(col, row)]["walkable"]
        return False

    def draw(self, surface, camera_x=0, camera_y=0, window_width=None, window_height=None):
        if window_width is None:
            window_width = surface.get_width()
        if window_height is None:
            window_height = surface.get_height()

        for (col, row), data in self.tiles.items():
            world_x, world_y = get_pixel_pos((col, row))
            screen_x = world_x - camera_x
            screen_y = world_y - camera_y

            # Optimization: only draw if visible on screen
            if -TILE_SIZE < screen_x < window_width and -TILE_SIZE < screen_y < window_height:
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
        tiles_list = [{"col": k[0], "row": k[1], "asset": v["asset"], "walkable": v["walkable"]}
                      for k, v in self.tiles.items()]
        with open(filepath, 'w') as f:
            json.dump({'tiles': tiles_list}, f)
        print(f"Map saved to {filepath}")

    def load(self, filepath):
        """Load map file. Supports old flat format and new layered format."""
        self.tiles.clear()
        if not os.path.exists(filepath):
            print(f"Map file {filepath} not found, starting with empty map.")
            return

        with open(filepath, 'r') as f:
            data = json.load(f)

        # New layered format (version 2) — flatten all layers for game
        if "version" in data and data["version"] >= 2:
            for layer_data in data.get("layers", []):
                if not layer_data.get("visible", True):
                    continue
                for t in layer_data.get("tiles", []):
                    walkable = t.get("walkable", False)
                    self.tiles[(t['col'], t['row'])] = {
                        "asset": t['asset'],
                        "walkable": walkable,
                        "scripts": t.get("scripts", []),
                        "properties": t.get("properties", {}),
                    }
            self.script_runtime.load_from_map(self.tiles)
            print(f"Layered map loaded from {filepath} (flattened for game)")
            return

        # Legacy formats
        if 'walls' in data:
            for w in data['walls']:
                self.tiles[(w[0], w[1])] = {"asset": "COLOR", "walkable": False}
        elif 'tiles' in data:
            for t in data['tiles']:
                walkable = t.get("walkable", False)
                self.tiles[(t['col'], t['row'])] = {"asset": t['asset'], "walkable": walkable}
        print(f"Map loaded from {filepath}")
