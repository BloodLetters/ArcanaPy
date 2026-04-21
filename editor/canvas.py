import pygame
from core.settings import TILE_SIZE
from editor.theme import Colors, Layout, font_small
from editor.ui_components import ContextMenu


class Canvas:
    def __init__(self, editor):
        self.editor = editor
        self.rect = pygame.Rect(Layout.LEFT_PANEL_WIDTH, Layout.TOOLBAR_HEIGHT, 800, 600)
        self.is_hovered = False

    def recalculate(self, window_width, window_height):
        self.rect.x = Layout.LEFT_PANEL_WIDTH
        self.rect.y = Layout.TOOLBAR_HEIGHT
        self.rect.width = window_width - Layout.LEFT_PANEL_WIDTH - Layout.RIGHT_PANEL_WIDTH
        self.rect.height = window_height - Layout.TOOLBAR_HEIGHT

    def _mouse_to_grid(self, pos):
        return self.editor.camera.screen_to_grid(pos, self.rect.x)

    def _is_in_canvas(self, pos):
        return self.rect.collidepoint(pos)

    def handle_event(self, event):
        if event.type == pygame.MOUSEWHEEL:
            mouse_pos = pygame.mouse.get_pos()
            if self._is_in_canvas(mouse_pos):
                self.editor.camera.zoom_at(mouse_pos, event.y, self.rect.x)
                return True

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if not self._is_in_canvas(event.pos):
                return False

            if event.button == 1:
                self.editor.left_mouse_down = True
                self.editor.mouse_last_pos = event.pos
                tool = self.editor.current_tool
                if tool == "DRAW":
                    self._do_draw(event.pos)
                elif tool == "ERASE":
                    self._do_erase(event.pos)
                elif tool == "FILL":
                    self._do_fill(event.pos)
                return True

            elif event.button == 3:
                col, row = self._mouse_to_grid(event.pos)
                self._open_context_menu(event.pos, col, row)
                return True

            elif event.button == 2:
                self.editor.middle_mouse_down = True
                self.editor.mouse_last_pos = event.pos
                return True

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.editor.left_mouse_down = False
            elif event.button == 2:
                self.editor.middle_mouse_down = False

        elif event.type == pygame.MOUSEMOTION:
            if self._is_in_canvas(event.pos):
                self.is_hovered = True
                col, row = self._mouse_to_grid(event.pos)
                self.editor.properties_panel.update_hovered_tile(col, row)

                if self.editor.left_mouse_down:
                    tool = self.editor.current_tool
                    if tool == "MOVE":
                        dx = event.pos[0] - self.editor.mouse_last_pos[0]
                        dy = event.pos[1] - self.editor.mouse_last_pos[1]
                        self.editor.camera.pan(dx, dy)
                        self.editor.mouse_last_pos = event.pos
                    elif tool == "DRAW":
                        self._do_draw(event.pos)
                    elif tool == "ERASE":
                        self._do_erase(event.pos)

                if self.editor.middle_mouse_down:
                    dx = event.pos[0] - self.editor.mouse_last_pos[0]
                    dy = event.pos[1] - self.editor.mouse_last_pos[1]
                    self.editor.camera.pan(dx, dy)
                    self.editor.mouse_last_pos = event.pos
            else:
                self.is_hovered = False

        return False

    def _do_draw(self, pos):
        col, row = self._mouse_to_grid(pos)
        lm = self.editor.layer_manager
        asset = self.editor.active_asset
        if asset:
            lm.set_tile(col, row, asset, self.editor.walkable_mode)

    def _do_erase(self, pos):
        col, row = self._mouse_to_grid(pos)
        self.editor.layer_manager.remove_tile(col, row)

    def _do_fill(self, pos):
        col, row = self._mouse_to_grid(pos)
        lm = self.editor.layer_manager
        layer = lm.active_layer
        if not layer or layer.locked:
            return
        asset = self.editor.active_asset
        if not asset:
            return

        existing = layer.get_tile(col, row)
        target_asset = existing["asset"] if existing else None

        if target_asset == asset:
            return

        visited = set()
        queue = [(col, row)]
        max_tiles = 500

        while queue and len(visited) < max_tiles:
            c, r = queue.pop(0)
            if (c, r) in visited:
                continue
            visited.add((c, r))

            tile = layer.get_tile(c, r)
            tile_asset = tile["asset"] if tile else None

            if tile_asset != target_asset:
                continue

            layer.set_tile(c, r, asset, self.editor.walkable_mode)

            for dc, dr in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nc, nr = c + dc, r + dr
                if (nc, nr) not in visited:
                    queue.append((nc, nr))

    def _open_context_menu(self, pos, col, row):
        lm = self.editor.layer_manager
        tile = lm.get_tile_at(col, row)

        items = []
        if tile:
            walkable = tile["walkable"]
            wlabel = "Walkable: Yes" if walkable else "Walkable: No"
            wcolor = Colors.SUCCESS if walkable else Colors.DANGER

            def toggle_walk():
                t = lm.get_tile_at(col, row)
                if t:
                    t["walkable"] = not t["walkable"]

            items.append(("Delete Tile", lambda: lm.remove_tile(col, row), Colors.DANGER))
            items.append((wlabel, toggle_walk, wcolor))
        else:
            items.append(("(No tile here)", lambda: None, Colors.SURFACE))

        def close():
            self.editor.context_menu = None

        self.editor.context_menu = ContextMenu(
            pos[0], pos[1], items, close,
            window_size=(self.editor.window_width, self.editor.window_height)
        )

    def draw(self, surface):
        surface.set_clip(self.rect)
        pygame.draw.rect(surface, Colors.CANVAS_BG, self.rect)

        cam = self.editor.camera
        lm = self.editor.layer_manager
        ts = cam.tile_size

        wx1, wy1 = cam.screen_to_world((self.rect.x, self.rect.y), self.rect.x)
        wx2, wy2 = cam.screen_to_world((self.rect.right, self.rect.bottom), self.rect.x)
        col_start = int(wx1 // TILE_SIZE) - 1
        col_end = int(wx2 // TILE_SIZE) + 1
        row_start = int(wy1 // TILE_SIZE) - 1
        row_end = int(wy2 // TILE_SIZE) + 1

        for layer in lm.layers:
            if not layer.visible:
                continue
            for (col, row), data in layer.tiles.items():
                if col < col_start or col > col_end or row < row_start or row > row_end:
                    continue

                sx, sy = cam.grid_to_screen(col, row, self.rect.x)
                tile_rect = pygame.Rect(int(sx), int(sy), ts, ts)

                asset_path = data["asset"]
                if asset_path == "COLOR":
                    pygame.draw.rect(surface, (120, 120, 120), tile_rect)
                else:
                    img = self.editor.asset_panel.get_image(asset_path)
                    if img:
                        scaled = pygame.transform.scale(img, (ts, ts))
                        surface.blit(scaled, tile_rect.topleft)
                    else:
                        pygame.draw.rect(surface, (120, 120, 120), tile_rect)

        self._draw_grid(surface, cam, col_start, col_end, row_start, row_end)

        if self.is_hovered and self.editor.current_tool in ("DRAW", "ERASE", "FILL"):
            mouse_pos = pygame.mouse.get_pos()
            col, row = self._mouse_to_grid(mouse_pos)
            sx, sy = cam.grid_to_screen(col, row, self.rect.x)
            preview_rect = pygame.Rect(int(sx), int(sy), ts, ts)

            if self.editor.current_tool == "DRAW" and self.editor.active_asset:
                img = self.editor.asset_panel.get_image(self.editor.active_asset)
                if img:
                    scaled = pygame.transform.scale(img, (ts, ts))
                    scaled.set_alpha(120)
                    surface.blit(scaled, preview_rect.topleft)
                pygame.draw.rect(surface, Colors.ACCENT, preview_rect, width=2, border_radius=2)
            elif self.editor.current_tool == "ERASE":
                s = pygame.Surface((ts, ts), pygame.SRCALPHA)
                s.fill((220, 70, 70, 60))
                surface.blit(s, preview_rect.topleft)
                pygame.draw.rect(surface, Colors.DANGER, preview_rect, width=2, border_radius=2)
            elif self.editor.current_tool == "FILL":
                pygame.draw.rect(surface, Colors.INFO, preview_rect, width=2, border_radius=2)

        if self.is_hovered:
            mouse_pos = pygame.mouse.get_pos()
            col, row = self._mouse_to_grid(mouse_pos)
            coord_text = font_small().render(f"({col}, {row})", True, Colors.TEXT_MUTED)
            surface.blit(coord_text, (self.rect.x + 8, self.rect.bottom - 20))

        surface.set_clip(None)

    def _draw_grid(self, surface, cam, col_start, col_end, row_start, row_end):
        ts = cam.tile_size

        for col in range(col_start, col_end + 1):
            sx, _ = cam.grid_to_screen(col, 0, self.rect.x)
            sx = int(sx)
            if self.rect.x <= sx <= self.rect.right:
                color = Colors.GRID_LINE_MAJOR if col % 10 == 0 else Colors.GRID_LINE
                pygame.draw.line(surface, color, (sx, self.rect.y), (sx, self.rect.bottom))

        for row in range(row_start, row_end + 1):
            _, sy = cam.grid_to_screen(0, row, self.rect.x)
            sy = int(sy)
            if self.rect.y <= sy <= self.rect.bottom:
                color = Colors.GRID_LINE_MAJOR if row % 10 == 0 else Colors.GRID_LINE
                pygame.draw.line(surface, color, (self.rect.x, sy), (self.rect.right, sy))
