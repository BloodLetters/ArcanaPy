class Script:
    def on_start(self, obj):
        obj.setdefault("properties", {})
        obj["properties"].setdefault("trigger_radius", 3)
        obj["properties"]["_triggered"] = False

    def on_update(self, obj, dt):
        pass

    def on_interact(self, obj, player):
        props = obj.get("properties", {})
        if not props.get("_triggered", False):
            props["_triggered"] = True
            print(f"[door_trigger] Door triggered at {obj.get('col')},{obj.get('row')}")

    def on_collision(self, obj, other):
        self.on_interact(obj, other)
