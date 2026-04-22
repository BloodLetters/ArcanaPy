import logging
from core.script_loader import instantiate_script, reload_and_instantiate

logger = logging.getLogger(__name__)


class ScriptRuntime:
    def __init__(self):
        self._attached = {}

    def attach(self, obj_id, obj, script_names):
        instances = []
        for name in script_names:
            inst = instantiate_script(name)
            if inst is not None:
                instances.append((name, inst))
                try:
                    inst.on_start(obj)
                    logger.debug(f"[ScriptRuntime] on_start: {name} -> obj {obj_id}")
                except Exception as e:
                    logger.error(f"[ScriptRuntime] on_start error in '{name}': {e}")
        self._attached[obj_id] = (obj, instances)

    def update(self, dt):
        for obj_id, (obj, instances) in self._attached.items():
            for name, inst in instances:
                try:
                    inst.on_update(obj, dt)
                except Exception as e:
                    logger.error(f"[ScriptRuntime] on_update error in '{name}' for obj {obj_id}: {e}")

    def trigger_interact(self, obj_id, player):
        entry = self._attached.get(obj_id)
        if entry is None:
            return
        obj, instances = entry
        for name, inst in instances:
            try:
                inst.on_interact(obj, player)
            except Exception as e:
                logger.error(f"[ScriptRuntime] on_interact error in '{name}' for obj {obj_id}: {e}")

    def trigger_collision(self, obj_id, other):
        entry = self._attached.get(obj_id)
        if entry is None:
            return
        obj, instances = entry
        for name, inst in instances:
            try:
                inst.on_collision(obj, other)
            except Exception as e:
                logger.error(f"[ScriptRuntime] on_collision error in '{name}' for obj {obj_id}: {e}")

    def hot_reload(self, obj_id, script_name):
        entry = self._attached.get(obj_id)
        if entry is None:
            return
        obj, instances = entry
        new_instances = []
        for name, inst in instances:
            if name == script_name:
                new_inst = reload_and_instantiate(name)
                if new_inst is not None:
                    try:
                        new_inst.on_start(obj)
                    except Exception as e:
                        logger.error(f"[ScriptRuntime] on_start after reload error in '{name}': {e}")
                    new_instances.append((name, new_inst))
                    logger.info(f"[ScriptRuntime] Hot-reloaded script '{name}' for obj {obj_id}")
                else:
                    new_instances.append((name, inst))
            else:
                new_instances.append((name, inst))
        self._attached[obj_id] = (obj, new_instances)

    def detach(self, obj_id):
        if obj_id in self._attached:
            del self._attached[obj_id]

    def clear(self):
        self._attached.clear()

    def load_from_map(self, tiles):
        self.clear()
        for pos, data in tiles.items():
            scripts = data.get("scripts", [])
            if scripts:
                self.attach(pos, data, scripts)
