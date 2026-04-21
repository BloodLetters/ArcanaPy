import pygame
import math
import heapq
from core.settings import TILE_SIZE, PLAYER_COLOR, TARGET_COLOR, GRID_WIDTH, GRID_HEIGHT
from core.grid import get_pixel_pos

class Player:
    def __init__(self, start_col, start_row, map_data):
        self.grid_pos = (start_col, start_row)
        self.pixel_pos = list(get_pixel_pos(self.grid_pos))
        self.target_grid_pos = None
        self.path = []
        self.speed = 200  # pixels per second
        self.animation_timer = 0.0
        self.facing_right = True
        self.map_data = map_data

        # Load player image
        try:
            self.image = pygame.image.load("assets/player/player.png").convert_alpha()
        except (pygame.error, FileNotFoundError):
            self.image = None
            print("Warning: assets/player/player.png not found, using fallback color.")

    def set_target(self, col, row):
        """Sets the target grid position for the player to move towards."""
        self.target_grid_pos = (col, row)
        self.calculate_astar_path()

    def calculate_astar_path(self):
        """Calculates path using A* algorithm to avoid walls."""
        if not self.target_grid_pos:
            return

        start = self.grid_pos
        goal = self.target_grid_pos
        
        if self.map_data.is_wall(*goal):
            self.path = []
            return

        frontier = []
        heapq.heappush(frontier, (0, start))
        came_from = {start: None}
        cost_so_far = {start: 0}

        while frontier:
            _, current = heapq.heappop(frontier)

            if current == goal:
                break

            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                next_node = (current[0] + dx, current[1] + dy)
                
                if not (0 <= next_node[0] < GRID_WIDTH and 0 <= next_node[1] < GRID_HEIGHT):
                    continue
                    
                if self.map_data.is_wall(*next_node):
                    continue

                new_cost = cost_so_far[current] + 1
                if next_node not in cost_so_far or new_cost < cost_so_far[next_node]:
                    cost_so_far[next_node] = new_cost
                    # Heuristic: Manhattan distance
                    priority = new_cost + abs(goal[0] - next_node[0]) + abs(goal[1] - next_node[1])
                    heapq.heappush(frontier, (priority, next_node))
                    came_from[next_node] = current

        # Reconstruct path
        self.path = []
        if goal in came_from:
            current = goal
            while current != start:
                self.path.append(current)
                current = came_from[current]
            self.path.reverse()

    def update(self, dt):
        """Updates the player's position."""
        if not self.path and self.target_grid_pos:
            self.target_grid_pos = None # Reached target
            self.animation_timer = 0.0
            return

        if self.path:
            self.animation_timer += dt
            next_grid_pos = self.path[0]
            target_x, target_y = get_pixel_pos(next_grid_pos)

            # Move towards target pixel position
            move_dist = self.speed * dt
            
            dx = target_x - self.pixel_pos[0]
            dy = target_y - self.pixel_pos[1]
            
            if dx > 0:
                self.facing_right = True
            elif dx < 0:
                self.facing_right = False
                
            dist = (dx**2 + dy**2)**0.5

            if dist <= move_dist:
                # Reached the next grid cell
                self.pixel_pos[0] = target_x
                self.pixel_pos[1] = target_y
                self.grid_pos = next_grid_pos
                self.path.pop(0)
            else:
                # Move a fraction of the distance
                self.pixel_pos[0] += (dx / dist) * move_dist
                self.pixel_pos[1] += (dy / dist) * move_dist

    def draw(self, surface):
        """Draws the player and the target path."""
        # Draw target indicator if exists
        if self.target_grid_pos:
            tx, ty = get_pixel_pos(self.target_grid_pos)
            target_rect = pygame.Rect(tx, ty, TILE_SIZE, TILE_SIZE)
            pygame.draw.rect(surface, TARGET_COLOR, target_rect, 2)
            
            # Draw path
            for p in self.path:
                px, py = get_pixel_pos(p)
                p_rect = pygame.Rect(px + TILE_SIZE//2 - 2, py + TILE_SIZE//2 - 2, 4, 4)
                pygame.draw.rect(surface, TARGET_COLOR, p_rect)

        # Draw player
        if getattr(self, 'image', None):
            image_to_draw = self.image
            if not getattr(self, 'facing_right', True):
                image_to_draw = pygame.transform.flip(self.image, True, False)
                
            # Base center on the tile
            center_x = self.pixel_pos[0] + TILE_SIZE / 2
            center_y = self.pixel_pos[1] + TILE_SIZE / 2
                
            # Add animations if moving
            if getattr(self, 'path', []):
                anim_timer = getattr(self, 'animation_timer', 0)
                # Bobbing animation
                bob_offset = abs(math.sin(anim_timer * 15)) * 8
                center_y -= bob_offset
                
                # Swing (rotation) animation
                swing_angle = math.sin(anim_timer * 15) * 5 # Swing up to 15 degrees
                image_to_draw = pygame.transform.rotate(image_to_draw, swing_angle)

            # Draw image centered correctly
            draw_rect = image_to_draw.get_rect(center=(center_x, center_y))
            surface.blit(image_to_draw, draw_rect)
        else:
            player_rect = pygame.Rect(self.pixel_pos[0], self.pixel_pos[1], TILE_SIZE, TILE_SIZE)
            pygame.draw.rect(surface, PLAYER_COLOR, player_rect)
