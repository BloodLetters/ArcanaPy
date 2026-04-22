class Script:
    def on_start(self, obj):
        obj.setdefault("properties", {})
        obj["properties"].setdefault("speed", 2)
        obj["properties"].setdefault("direction", 1)
        obj["properties"]["_tick"] = 0

    def on_update(self, obj, dt):
        props = obj.get("properties", {})
        props["_tick"] = props.get("_tick", 0) + dt
        if props["_tick"] >= 1.0:
            props["_tick"] = 0
            props["direction"] = -props.get("direction", 1)

    def on_interact(self, obj, player):
        print(f"[npc_ai] Player interacted with NPC at {obj.get('col')},{obj.get('row')}")

    def on_collision(self, obj, other):
        print(f"[npc_ai] NPC collided with {other}")
