import json
import os


class Layer:
    LAYER_COLORS = {
        "Background": (60, 140, 90),
        "Objects": (140, 100, 60),
        "Collision": (180, 60, 60),
        "Decoration": (60, 120, 180),
    }

    def __init__(self, name, visible=True, locked=False):
        self.name = name
        self.tiles = {}  # {(col, row): {"asset": str, "walkable": bool}}
        self.visible = visible
        self.locked = locked

    @property
    def color(self):
        return self.LAYER_COLORS.get(self.name, (120, 120, 140))

    def set_tile(self, col, row, asset_path, walkable=False, scripts=None, properties=None):
        existing = self.tiles.get((col, row), {})
        self.tiles[(col, row)] = {
            "asset": asset_path,
            "walkable": walkable,
            "scripts": scripts if scripts is not None else existing.get("scripts", []),
            "properties": properties if properties is not None else existing.get("properties", {}),
        }

    def remove_tile(self, col, row):
        if (col, row) in self.tiles:
            del self.tiles[(col, row)]
            return True
        return False

    def get_tile(self, col, row):
        return self.tiles.get((col, row))

    def clear(self):
        self.tiles.clear()

    def to_dict(self):
        tiles_list = []
        for (col, row), data in self.tiles.items():
            entry = {
                "col": col, "row": row,
                "asset": data["asset"],
                "walkable": data["walkable"],
            }
            if data.get("scripts"):
                entry["scripts"] = data["scripts"]
            if data.get("properties"):
                entry["properties"] = data["properties"]
            tiles_list.append(entry)
        return {
            "name": self.name,
            "visible": self.visible,
            "locked": self.locked,
            "tiles": tiles_list
        }

    @classmethod
    def from_dict(cls, data):
        layer = cls(data["name"], data.get("visible", True), data.get("locked", False))
        for t in data.get("tiles", []):
            layer.tiles[(t["col"], t["row"])] = {
                "asset": t["asset"],
                "walkable": t.get("walkable", False),
                "scripts": t.get("scripts", []),
                "properties": t.get("properties", {}),
            }
        return layer


class LayerManager:
    DEFAULT_LAYERS = ["Background", "Objects", "Collision", "Decoration"]

    def __init__(self):
        self.layers = []
        self.active_index = 0
        self._init_defaults()

    def _init_defaults(self):
        for name in self.DEFAULT_LAYERS:
            self.layers.append(Layer(name))

    @property
    def active_layer(self):
        if 0 <= self.active_index < len(self.layers):
            return self.layers[self.active_index]
        return None

    def set_active(self, index):
        if 0 <= index < len(self.layers):
            self.active_index = index

    def add_layer(self, name=None):
        if name is None:
            name = f"Layer {len(self.layers) + 1}"
        layer = Layer(name)
        self.layers.append(layer)
        return layer

    def remove_layer(self, index):
        if len(self.layers) <= 1:
            return False
        if 0 <= index < len(self.layers):
            self.layers.pop(index)
            if self.active_index >= len(self.layers):
                self.active_index = len(self.layers) - 1
            return True
        return False

    def move_layer_up(self, index):
        if index > 0:
            self.layers[index], self.layers[index - 1] = self.layers[index - 1], self.layers[index]
            if self.active_index == index:
                self.active_index -= 1
            elif self.active_index == index - 1:
                self.active_index += 1
            return True
        return False

    def move_layer_down(self, index):
        if index < len(self.layers) - 1:
            self.layers[index], self.layers[index + 1] = self.layers[index + 1], self.layers[index]
            if self.active_index == index:
                self.active_index += 1
            elif self.active_index == index + 1:
                self.active_index -= 1
            return True
        return False

    def set_tile(self, col, row, asset_path, walkable=False):
        layer = self.active_layer
        if layer and not layer.locked:
            layer.set_tile(col, row, asset_path, walkable)

    def remove_tile(self, col, row):
        layer = self.active_layer
        if layer and not layer.locked:
            return layer.remove_tile(col, row)
        return False

    def get_tile_at(self, col, row, layer_index=None):
        idx = layer_index if layer_index is not None else self.active_index
        if 0 <= idx < len(self.layers):
            return self.layers[idx].get_tile(col, row)
        return None

    def get_all_tiles_at(self, col, row):
        result = []
        for i, layer in enumerate(self.layers):
            tile = layer.get_tile(col, row)
            if tile:
                result.append((i, layer.name, tile))
        return result

    def is_wall(self, col, row):
        for layer in self.layers:
            tile = layer.get_tile(col, row)
            if tile and not tile["walkable"]:
                return True
        return False

    def get_flat_tiles(self):
        merged = {}
        for layer in self.layers:
            if layer.visible:
                for pos, data in layer.tiles.items():
                    merged[pos] = data
        return merged

    def clear_all(self):
        for layer in self.layers:
            layer.clear()

    def save(self, filepath):
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        data = {
            "version": 2,
            "layers": [layer.to_dict() for layer in self.layers]
        }
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"Map saved to {filepath}")

    def load(self, filepath):
        if not os.path.exists(filepath):
            print(f"Map file {filepath} not found, starting with empty map.")
            return

        with open(filepath, 'r') as f:
            data = json.load(f)

        if "version" in data and data["version"] >= 2:
            self.layers.clear()
            for layer_data in data["layers"]:
                self.layers.append(Layer.from_dict(layer_data))
            if not self.layers:
                self._init_defaults()
            self.active_index = 0
            print(f"Map loaded from {filepath} ({len(self.layers)} layers)")
            return

        self.layers.clear()
        self._init_defaults()
        bg = self.layers[0]

        if 'tiles' in data:
            for t in data['tiles']:
                walkable = t.get("walkable", False)
                bg.tiles[(t['col'], t['row'])] = {"asset": t['asset'], "walkable": walkable}
        elif 'walls' in data:
            for w in data['walls']:
                bg.tiles[(w[0], w[1])] = {"asset": "COLOR", "walkable": False}

        self.active_index = 0
        print(f"Legacy map loaded from {filepath} into Background layer")
