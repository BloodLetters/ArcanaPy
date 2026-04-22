from editor.theme import Colors, Layout, Icons, font_section, font_body, font_small
import pygame
from editor.ui_components import IconButton, Separator


class Toolbar:
    def __init__(self, editor):
        self.editor = editor
        self.rect = pygame.Rect(0, 0, 100, Layout.TOOLBAR_HEIGHT)
        self.tool_buttons = {}
        self.action_buttons = []
        self.zoom_buttons = []
        self.play_btn = None
        self._build()

    def _build(self):
        pad = 8
        x = pad
        y = (Layout.TOOLBAR_HEIGHT - Layout.ICON_BUTTON_SIZE) // 2

        tools = [
            ("DRAW", Icons.BRUSH, "Brush (B)"),
            ("ERASE", Icons.ERASER, "Eraser (E)"),
            ("MOVE", Icons.MOVE, "Move (M)"),
            ("FILL", Icons.FILL, "Fill (F)"),
            ("SELECT", Icons.SELECT, "Select (S)"),
        ]
        for tool_id, icon, tooltip in tools:
            btn = IconButton(x, y, icon, tooltip, lambda t=tool_id: self.editor.set_tool(t))
            btn.group = "tools"
            self.tool_buttons[tool_id] = btn
            x += Layout.ICON_BUTTON_SIZE + 4

        if "DRAW" in self.tool_buttons:
            self.tool_buttons["DRAW"].is_active = True
        
        # New base X for play button after the tools + separator
        self.play_sep_x = x + 4
        x += 16
        self.play_btn = IconButton(x, y, Icons.PLAY, "Play Game (F5)", self.editor.play_game)

    def recalculate(self, window_width):
        self.rect.width = window_width

        self.action_buttons.clear()
        self.zoom_buttons.clear()

        y = (Layout.TOOLBAR_HEIGHT - Layout.ICON_BUTTON_SIZE) // 2
        rx = window_width - 8

        actions = [
            (Icons.FULLSCREEN, "Fullscreen (F11)", self.editor.toggle_fullscreen),
            (Icons.CLEAR, "Clear All", self.editor.clear_all),
            (Icons.LOAD, "Load (Ctrl+L)", self.editor.load_map),
            (Icons.SAVE, "Save (Ctrl+S)", self.editor.save_map),
        ]
        for icon, tooltip, cb in actions:
            rx -= Layout.ICON_BUTTON_SIZE + 4
            btn = IconButton(rx, y, icon, tooltip, cb)
            self.action_buttons.append(btn)

        rx -= 20
        rx -= Layout.ICON_BUTTON_SIZE
        self.zoom_out_btn = IconButton(rx, y, Icons.ZOOM_OUT, "Zoom Out", self.editor.zoom_out)
        self.zoom_buttons.append(self.zoom_out_btn)
        rx -= Layout.ICON_BUTTON_SIZE + 4
        self.zoom_in_btn = IconButton(rx, y, Icons.ZOOM_IN, "Zoom In", self.editor.zoom_in)
        self.zoom_buttons.append(self.zoom_in_btn)

    def set_active_tool(self, tool_id):
        for tid, btn in self.tool_buttons.items():
            btn.is_active = (tid == tool_id)

    def handle_event(self, event):
        for btn in self.tool_buttons.values():
            if btn.handle_event(event):
                return True
        if self.play_btn and self.play_btn.handle_event(event):
            return True
        for btn in self.action_buttons:
            if btn.handle_event(event):
                return True
        for btn in self.zoom_buttons:
            if btn.handle_event(event):
                return True
        return False

    def update(self, dt):
        pass

    def draw(self, surface):
        pygame.draw.rect(surface, Colors.PANEL_HEADER, self.rect)
        pygame.draw.line(surface, Colors.BORDER, (0, self.rect.bottom - 1),
                         (self.rect.width, self.rect.bottom - 1))

        for btn in self.tool_buttons.values():
            btn.draw(surface)
        
        # Divider before Play button
        pygame.draw.line(surface, Colors.BORDER,
                         (self.play_sep_x, 8), (self.play_sep_x, Layout.TOOLBAR_HEIGHT - 8))
        
        if self.play_btn:
            self.play_btn.draw(surface)

        # Divider after Play button and tools
        sep_x = self.play_btn.rect.right + 8
        pygame.draw.line(surface, Colors.BORDER,
                         (sep_x, 8), (sep_x, Layout.TOOLBAR_HEIGHT - 8))

        f = font_section()
        tool_name = self.editor.current_tool
        mode = "WALKABLE" if self.editor.walkable_mode else "SOLID"
        mode_color = Colors.SUCCESS if self.editor.walkable_mode else Colors.DANGER

        label = f.render(f"Tool: {tool_name}", True, Colors.TEXT_PRIMARY)
        surface.blit(label, (sep_x + 12, 8))

        mode_surf = font_small().render(f"Mode: {mode}", True, mode_color)
        surface.blit(mode_surf, (sep_x + 12, 26))

        zoom_pct = self.editor.camera.get_zoom_percent()
        zoom_surf = font_body().render(f"{zoom_pct}%", True, Colors.TEXT_SECONDARY)
        if self.zoom_buttons:
            zx = self.zoom_buttons[-1].rect.x - zoom_surf.get_width() - 12
        else:
            zx = self.rect.width // 2
        surface.blit(zoom_surf, (zx, (Layout.TOOLBAR_HEIGHT - zoom_surf.get_height()) // 2))

        for btn in self.action_buttons:
            btn.draw(surface)
        for btn in self.zoom_buttons:
            btn.draw(surface)

