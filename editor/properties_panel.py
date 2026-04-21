import pygame
from editor.theme import Colors, Layout, Icons, font_title, font_section, font_body, font_small
from editor.ui_components import IconButton, TextButton, Separator, ScrollArea


class PropertiesPanel:
    def __init__(self, editor):
        self.editor = editor
        self.rect = pygame.Rect(0, Layout.TOOLBAR_HEIGHT, Layout.RIGHT_PANEL_WIDTH, 600)
        self.layer_buttons = []
        self.layer_action_btns = []
        self.hovered_tile_info = None  # (col, row, layer_idx, tile_data)

    def recalculate(self, window_width, window_height):
        self.rect.x = window_width - Layout.RIGHT_PANEL_WIDTH
        self.rect.y = Layout.TOOLBAR_HEIGHT
        self.rect.height = window_height - Layout.TOOLBAR_HEIGHT
        self._rebuild_layer_buttons()

    def _rebuild_layer_buttons(self):
        self.layer_action_btns.clear()
        pad = Layout.PANEL_PADDING
        x = self.rect.x + pad
        btn_w = self.rect.width - pad * 2

        y = self.rect.y + 44
        half_w = (btn_w - 4) // 2

        self.layer_action_btns = [
            TextButton(x, y, half_w, 26, "+ Add Layer", self._add_layer),
            TextButton(x + half_w + 4, y, half_w, 26, "- Remove", self._remove_layer, danger=True),
        ]

    def _add_layer(self):
        self.editor.layer_manager.add_layer()

    def _remove_layer(self):
        self.editor.layer_manager.remove_layer(self.editor.layer_manager.active_index)

    def update_hovered_tile(self, col, row):
        lm = self.editor.layer_manager
        tile = lm.get_tile_at(col, row)
        if tile:
            self.hovered_tile_info = (col, row, lm.active_index, tile)
        else:
            all_tiles = lm.get_all_tiles_at(col, row)
            if all_tiles:
                li, ln, td = all_tiles[-1]  # topmost
                self.hovered_tile_info = (col, row, li, td)
            else:
                self.hovered_tile_info = (col, row, None, None)

    def handle_event(self, event):
        for btn in self.layer_action_btns:
            if btn.handle_event(event):
                return True

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                lm = self.editor.layer_manager
                layer_y_start = self.rect.y + 80
                for i, layer in enumerate(lm.layers):
                    ly = layer_y_start + i * 36
                    layer_rect = pygame.Rect(self.rect.x + Layout.PANEL_PADDING, ly,
                                             self.rect.width - Layout.PANEL_PADDING * 2, 32)
                    if layer_rect.collidepoint(event.pos):
                        rx = event.pos[0] - layer_rect.x

                        if rx < 24:
                            layer.visible = not layer.visible
                        elif rx < 48:
                            layer.locked = not layer.locked
                        elif rx > layer_rect.width - 48 and rx <= layer_rect.width - 24:
                            lm.move_layer_up(i)
                        elif rx > layer_rect.width - 24:
                            lm.move_layer_down(i)
                        else:
                            lm.set_active(i)
                        return True
                return True
        elif event.type == pygame.MOUSEMOTION:
            for btn in self.layer_action_btns:
                btn.handle_event(event)
        return False

    def draw(self, surface):
        pygame.draw.rect(surface, Colors.PANEL_BG, self.rect)
        pygame.draw.line(surface, Colors.BORDER,
                         (self.rect.x, self.rect.y),
                         (self.rect.x, self.rect.bottom), 2)

        pad = Layout.PANEL_PADDING
        x = self.rect.x + pad
        panel_w = self.rect.width - pad * 2

        title = font_title().render("LAYERS", True, Colors.ACCENT)
        surface.blit(title, (x, self.rect.y + 14))

        for btn in self.layer_action_btns:
            btn.draw(surface)

        lm = self.editor.layer_manager
        layer_y = self.rect.y + 80
        mouse_pos = pygame.mouse.get_pos()

        for i, layer in enumerate(lm.layers):
            ly = layer_y + i * 36
            row_rect = pygame.Rect(x, ly, panel_w, 32)
            is_active = (i == lm.active_index)
            is_hovered = row_rect.collidepoint(mouse_pos)

            if is_active:
                pygame.draw.rect(surface, Colors.ACCENT_DIM, row_rect, border_radius=4)
            elif is_hovered:
                pygame.draw.rect(surface, Colors.SURFACE, row_rect, border_radius=4)

            if is_active:
                pygame.draw.rect(surface, Colors.ACCENT, row_rect, width=1, border_radius=4)

            vis_icon = Icons.EYE_OPEN if layer.visible else Icons.EYE_CLOSED
            vis_color = Colors.TEXT_PRIMARY if layer.visible else Colors.TEXT_MUTED
            vis_surf = font_body().render(vis_icon, True, vis_color)
            surface.blit(vis_surf, (x + 4, ly + 8))

            lock_icon = Icons.LOCK if layer.locked else Icons.UNLOCK
            lock_color = Colors.WARNING if layer.locked else Colors.TEXT_MUTED
            lock_surf = font_body().render(lock_icon, True, lock_color)
            surface.blit(lock_surf, (x + 28, ly + 8))

            color_rect = pygame.Rect(x + 50, ly + 10, 10, 12)
            pygame.draw.rect(surface, layer.color, color_rect, border_radius=2)

            name_surf = font_body().render(layer.name, True, Colors.TEXT_PRIMARY)
            surface.blit(name_surf, (x + 66, ly + 8))

            count = len(layer.tiles)
            count_surf = font_small().render(str(count), True, Colors.TEXT_MUTED)
            surface.blit(count_surf, (x + panel_w - 58, ly + 10))

            arr_up = font_small().render(Icons.ARROW_UP, True, Colors.TEXT_SECONDARY)
            arr_dn = font_small().render(Icons.ARROW_DOWN, True, Colors.TEXT_SECONDARY)
            surface.blit(arr_up, (x + panel_w - 36, ly + 6))
            surface.blit(arr_dn, (x + panel_w - 18, ly + 6))

        info_y = layer_y + len(lm.layers) * 36 + Layout.SECTION_SPACING
        Separator.draw(surface, x, info_y, panel_w, "TILE INFO")
        info_y += 24

        if self.hovered_tile_info:
            col, row, li, tile = self.hovered_tile_info
            pos_surf = font_body().render(f"Position: ({col}, {row})", True, Colors.TEXT_SECONDARY)
            surface.blit(pos_surf, (x, info_y))
            info_y += 20

            if tile:
                asset_name = tile["asset"]
                if asset_name != "COLOR":
                    import os
                    asset_name = os.path.basename(asset_name)
                asset_surf = font_body().render(f"Asset: {asset_name}", True, Colors.TEXT_SECONDARY)
                surface.blit(asset_surf, (x, info_y))
                info_y += 20

                walkable = tile["walkable"]
                wt = "Yes" if walkable else "No"
                wc = Colors.SUCCESS if walkable else Colors.DANGER
                walk_surf = font_body().render(f"Walkable: {wt}", True, wc)
                surface.blit(walk_surf, (x, info_y))
                info_y += 20

                if li is not None and li < len(lm.layers):
                    ln = lm.layers[li].name
                    layer_surf = font_body().render(f"Layer: {ln}", True, Colors.TEXT_SECONDARY)
                    surface.blit(layer_surf, (x, info_y))
            else:
                empty = font_body().render("(empty cell)", True, Colors.TEXT_MUTED)
                surface.blit(empty, (x, info_y))

        shortcut_y = self.rect.bottom - 80
        Separator.draw(surface, x, shortcut_y, panel_w, "SHORTCUTS")
        shortcut_y += 24
        shortcuts = [
            "B: Brush  E: Eraser  M: Move  F: Fill",
            "W: Toggle Mode  1-4: Layers",
            "F11: Fullscreen  Scroll: Zoom",
        ]
        for s in shortcuts:
            surf = font_small().render(s, True, Colors.TEXT_MUTED)
            surface.blit(surf, (x, shortcut_y))
            shortcut_y += 16
