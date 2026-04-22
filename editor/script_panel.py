import pygame
from editor.theme import Colors, Layout, font_title, font_section, font_body, font_small
from editor.ui_components import TextButton, Separator
from core.script_loader import list_available_scripts


class ScriptPanel:
    DROPDOWN_ITEM_H = 22
    INPUT_H = 24
    PROP_ROW_H = 22

    def __init__(self, editor):
        self.editor = editor
        self.rect = pygame.Rect(0, 0, Layout.RIGHT_PANEL_WIDTH, 0)

        self._dropdown_open = False
        self._dropdown_scripts = []

        self._prop_key_input = ""
        self._prop_val_input = ""
        self._prop_focus = None

        self._input_cursor_timer = 0
        self._cursor_visible = True

        self._selected_tile = None

    def recalculate(self, x, y, width):
        self.rect.x = x
        self.rect.y = y
        self.rect.width = width

    def _current_tile(self):
        if self.editor.selected_tile is not None:
            return self.editor.selected_tile
        pp = self.editor.properties_panel
        if pp.hovered_tile_info is None:
            return None
        col, row, li, tile = pp.hovered_tile_info
        if tile is None or li is None:
            return None
        return col, row, li, tile

    def _tile_data(self):
        ct = self._current_tile()
        if ct is None:
            return None
        col, row, li, tile = ct
        return tile

    def _ensure_fields(self, tile):
        tile.setdefault("scripts", [])
        tile.setdefault("properties", {})

    def handle_event(self, event):
        tile = self._tile_data()

        if event.type == pygame.KEYDOWN:
            if self._prop_focus == "key":
                self._handle_text_input(event, "_prop_key_input")
                return True
            if self._prop_focus == "val":
                self._handle_text_input(event, "_prop_val_input")
                return True

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            prev_dropdown_open = self._dropdown_open
            self._dropdown_open = False
            if tile is None:
                return False

            self._ensure_fields(tile)
            pos = event.pos
            pad = Layout.PANEL_PADDING
            x = self.rect.x + pad

            y = self.rect.y
            y += 24
            if self.editor.selected_tile is not None:
                y += 18

            dropdown_rect = pygame.Rect(x, y, self.rect.width - pad * 2, self.INPUT_H)
            if dropdown_rect.collidepoint(pos):
                self._dropdown_scripts = list_available_scripts()
                self._dropdown_open = True
                return True

            if prev_dropdown_open:
                for i, name in enumerate(self._dropdown_scripts):
                    item_rect = pygame.Rect(x, y + self.INPUT_H + i * self.DROPDOWN_ITEM_H,
                                           self.rect.width - pad * 2, self.DROPDOWN_ITEM_H)
                    if item_rect.collidepoint(pos):
                        if name not in tile["scripts"]:
                            tile["scripts"].append(name)
                        self._dropdown_open = False
                        return True

            script_remove_y = y + self.INPUT_H + 4
            for i, sname in enumerate(list(tile.get("scripts", []))):
                btn_x = x + (self.rect.width - pad * 2) - 18
                btn_rect = pygame.Rect(btn_x, script_remove_y + i * 20, 14, 14)
                if btn_rect.collidepoint(pos):
                    tile["scripts"].remove(sname)
                    return True

            y += self.INPUT_H + 4 + len(tile.get("scripts", [])) * 20 + 8
            y += 24 # Added separator offset to match draw (8 + 24)

            key_rect = pygame.Rect(x, y, (self.rect.width - pad * 2) // 2 - 2, self.INPUT_H)
            val_rect = pygame.Rect(key_rect.right + 4, y, (self.rect.width - pad * 2) // 2 - 2, self.INPUT_H)
            add_rect = pygame.Rect(x, y + self.INPUT_H + 4, self.rect.width - pad * 2, 20)

            if key_rect.collidepoint(pos):
                self._prop_focus = "key"
                return True
            if val_rect.collidepoint(pos):
                self._prop_focus = "val"
                return True
            if add_rect.collidepoint(pos):
                k = self._prop_key_input.strip()
                v = self._prop_val_input.strip()
                if k:
                    tile["properties"][k] = v
                    self._prop_key_input = ""
                    self._prop_val_input = ""
                    self._prop_focus = None
                return True

            prop_list_y = y + self.INPUT_H + 28
            for i, (k, v) in enumerate(list(tile.get("properties", {}).items())):
                del_rect = pygame.Rect(x + (self.rect.width - pad * 2) - 18,
                                       prop_list_y + i * self.PROP_ROW_H, 14, 14)
                if del_rect.collidepoint(pos):
                    del tile["properties"][k]
                    return True

            self._prop_focus = None
            return False

        return False

    def _handle_text_input(self, event, field):
        current = getattr(self, field)
        if event.key == pygame.K_BACKSPACE:
            setattr(self, field, current[:-1])
        elif event.key == pygame.K_TAB:
            self._prop_focus = "val" if self._prop_focus == "key" else "key"
        elif event.key == pygame.K_RETURN:
            tile = self._tile_data()
            if tile is not None:
                self._ensure_fields(tile)
                k = self._prop_key_input.strip()
                v = self._prop_val_input.strip()
                if k:
                    tile["properties"][k] = v
                    self._prop_key_input = ""
                    self._prop_val_input = ""
            self._prop_focus = None
        elif event.unicode and event.unicode.isprintable():
            setattr(self, field, current + event.unicode)

    def update(self, dt):
        self._input_cursor_timer += dt
        if self._input_cursor_timer >= 0.5:
            self._input_cursor_timer = 0
            self._cursor_visible = not self._cursor_visible

    def draw(self, surface):
        tile = self._tile_data()
        pad = Layout.PANEL_PADDING
        x = self.rect.x + pad
        panel_w = self.rect.width - pad * 2

        y = self.rect.y
        Separator.draw(surface, x, y, panel_w, "SCRIPTS")
        y += 24

        if tile is None:
            if self.editor.selected_tile is None:
                text = font_small().render("Select a tile (S key)", True, Colors.TEXT_MUTED)
            else:
                text = font_small().render("(empty cell selected)", True, Colors.TEXT_MUTED)
            surface.blit(text, (x, y))
            self._dropdown_open = False
            return

        ct = self._current_tile()
        if ct:
            c, r, li, _ = ct
            lm = self.editor.layer_manager
            layer_name = lm.layers[li].name if li is not None and li < len(lm.layers) else "?"
            is_selected = self.editor.selected_tile is not None
            pin_color = Colors.ACCENT if is_selected else Colors.TEXT_MUTED
            pin_icon = "[S]" if is_selected else "[~]"
            header = font_small().render(f"{pin_icon} ({c},{r}) Layer: {layer_name}", True, pin_color)
            surface.blit(header, (x, y))
            y += 18

        self._ensure_fields(tile)

        dropdown_rect = pygame.Rect(x, y, panel_w, self.INPUT_H)
        pygame.draw.rect(surface, Colors.SURFACE, dropdown_rect, border_radius=4)
        pygame.draw.rect(surface, Colors.BORDER, dropdown_rect, width=1, border_radius=4)
        label = font_small().render("+ Attach script...", True, Colors.TEXT_SECONDARY)
        surface.blit(label, (dropdown_rect.x + 6, dropdown_rect.y + 5))
        y += self.INPUT_H + 4

        for i, sname in enumerate(tile.get("scripts", [])):
            row_rect = pygame.Rect(x, y, panel_w, 18)
            pygame.draw.rect(surface, Colors.ACCENT_DIM, row_rect, border_radius=3)
            name_surf = font_small().render(sname, True, Colors.TEXT_PRIMARY)
            surface.blit(name_surf, (x + 4, y + 2))
            del_surf = font_small().render("x", True, Colors.DANGER)
            surface.blit(del_surf, (x + panel_w - 14, y + 2))
            y += 20

        y += 8
        Separator.draw(surface, x, y, panel_w, "PROPERTIES")
        y += 24

        key_w = panel_w // 2 - 2
        val_w = panel_w - key_w - 4

        key_rect = pygame.Rect(x, y, key_w, self.INPUT_H)
        val_rect = pygame.Rect(x + key_w + 4, y, val_w, self.INPUT_H)

        key_border = Colors.ACCENT if self._prop_focus == "key" else Colors.BORDER
        val_border = Colors.ACCENT if self._prop_focus == "val" else Colors.BORDER

        pygame.draw.rect(surface, Colors.SURFACE, key_rect, border_radius=4)
        pygame.draw.rect(surface, key_border, key_rect, width=1, border_radius=4)
        pygame.draw.rect(surface, Colors.SURFACE, val_rect, border_radius=4)
        pygame.draw.rect(surface, val_border, val_rect, width=1, border_radius=4)

        ph_key = Colors.TEXT_MUTED if not self._prop_key_input else Colors.TEXT_PRIMARY
        ph_val = Colors.TEXT_MUTED if not self._prop_val_input else Colors.TEXT_PRIMARY

        key_disp = self._prop_key_input or "key"
        val_disp = self._prop_val_input or "value"

        if self._prop_focus == "key" and self._cursor_visible:
            key_disp += "|"
        if self._prop_focus == "val" and self._cursor_visible:
            val_disp += "|"

        surface.blit(font_small().render(key_disp, True, ph_key), (key_rect.x + 4, key_rect.y + 5))
        surface.blit(font_small().render(val_disp, True, ph_val), (val_rect.x + 4, val_rect.y + 5))

        y += self.INPUT_H + 4

        add_rect = pygame.Rect(x, y, panel_w, 20)
        pygame.draw.rect(surface, Colors.SURFACE, add_rect, border_radius=3)
        add_surf = font_small().render("Add / Update property", True, Colors.TEXT_SECONDARY)
        surface.blit(add_surf, (x + (panel_w - add_surf.get_width()) // 2, y + 2))
        y += 24

        for i, (k, v) in enumerate(tile.get("properties", {}).items()):
            row_rect = pygame.Rect(x, y, panel_w, self.PROP_ROW_H - 2)
            pygame.draw.rect(surface, Colors.SURFACE, row_rect, border_radius=3)
            kv_text = f"{k}: {v}"
            kv_surf = font_small().render(kv_text, True, Colors.TEXT_SECONDARY)
            surface.blit(kv_surf, (x + 4, y + 3))
            del_surf = font_small().render("x", True, Colors.DANGER)
            surface.blit(del_surf, (x + panel_w - 14, y + 3))
            y += self.PROP_ROW_H

        if self._dropdown_open:
            header_offset = 18 if self.editor.selected_tile is not None else 0
            drop_y = self.rect.y + 24 + header_offset + self.INPUT_H
            scripts = self._dropdown_scripts
            total_h = len(scripts) * self.DROPDOWN_ITEM_H + 8
            drop_rect = pygame.Rect(x, drop_y, panel_w, total_h)
            pygame.draw.rect(surface, Colors.PANEL_HEADER, drop_rect, border_radius=4)
            pygame.draw.rect(surface, Colors.ACCENT, drop_rect, width=1, border_radius=4)
            for i, name in enumerate(scripts):
                item_rect = pygame.Rect(x + 2, drop_y + 4 + i * self.DROPDOWN_ITEM_H,
                                        panel_w - 4, self.DROPDOWN_ITEM_H)
                mouse = pygame.mouse.get_pos()
                if item_rect.collidepoint(mouse):
                    pygame.draw.rect(surface, Colors.ACCENT_DIM, item_rect, border_radius=3)
                active = name in tile.get("scripts", [])
                color = Colors.SUCCESS if active else Colors.TEXT_PRIMARY
                surf = font_small().render(name, True, color)
                surface.blit(surf, (item_rect.x + 4, item_rect.y + 3))
