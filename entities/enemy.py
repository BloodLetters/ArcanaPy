import pygame
import math
import heapq
from core.settings import TILE_SIZE, ENEMIES_CONFIG
from core.grid import get_pixel_pos

class Enemy:
    def __init__(self, enemy_type, start_col, start_row, map_data):
        self.grid_pos = (start_col, start_row)
        self.pixel_pos = list(get_pixel_pos(self.grid_pos))
        self.target_grid_pos = None
        self.map_data = map_data
        
        config = ENEMIES_CONFIG.get(enemy_type, {})
        self.health = config.get("health", 100)
        self.damage = config.get("damage", 10)
        self.speed = config.get("speed", 180)
        asset_path = config.get("asset", "")

        try:
            self.image = pygame.image.load(asset_path).convert_alpha()
        except (pygame.error, FileNotFoundError):
            self.image = None
            print(f"Warning: Enemy image {asset_path} not found.")

        self.animation_timer = 0.0
        self.facing_right = True

    def calculate_astar_path(self, goal):
        start = self.grid_pos
        
        if start == goal:
            return []

        frontier = []
        heapq.heappush(frontier, (0, start))
        came_from = {start: None}
        cost_so_far = {start: 0}

        if self.map_data.tiles:
            min_col = min(k[0] for k in self.map_data.tiles.keys()) - 5
            max_col = max(k[0] for k in self.map_data.tiles.keys()) + 5
            min_row = min(k[1] for k in self.map_data.tiles.keys()) - 5
            max_row = max(k[1] for k in self.map_data.tiles.keys()) + 5
        else:
            min_col, max_col, min_row, max_row = -100, 100, -100, 100

        min_col = min(min_col, start[0] - 5, goal[0] - 5)
        max_col = max(max_col, start[0] + 5, goal[0] + 5)
        min_row = min(min_row, start[1] - 5, goal[1] - 5)
        max_row = max(max_row, start[1] + 5, goal[1] + 5)

        while frontier:
            _, current = heapq.heappop(frontier)

            if current == goal:
                break

            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                next_node = (current[0] + dx, current[1] + dy)
                
                if not (min_col <= next_node[0] <= max_col and min_row <= next_node[1] <= max_row):
                    continue
                    
                # The enemy can enter the goal even if it is a wall (because the goal is the player's position)
                if next_node != goal and self.map_data.is_wall(*next_node):
                    continue

                new_cost = cost_so_far[current] + 1
                if next_node not in cost_so_far or new_cost < cost_so_far[next_node]:
                    cost_so_far[next_node] = new_cost
                    priority = new_cost + abs(goal[0] - next_node[0]) + abs(goal[1] - next_node[1])
                    heapq.heappush(frontier, (priority, next_node))
                    came_from[next_node] = current

        path = []
        if goal in came_from:
            current = goal
            while current != start:
                path.append(current)
                current = came_from[current]
            path.reverse()
            
        return path

    def take_turn(self, player_grid_pos):
        # Only take a turn if we are not already moving
        if self.target_grid_pos is not None:
            # Snap to grid if it hasn't finished its previous movement
            self.pixel_pos = list(get_pixel_pos(self.target_grid_pos))
            self.grid_pos = self.target_grid_pos
            self.target_grid_pos = None

        path = self.calculate_astar_path(player_grid_pos)
        
        # We only move if the path length is strictly greater than 1 
        # (meaning we are not adjacent to the player)
        if len(path) > 1:
            self.target_grid_pos = path[0]

    def update(self, dt):
        if self.target_grid_pos:
            self.animation_timer += dt
            target_x, target_y = get_pixel_pos(self.target_grid_pos)

            move_dist = self.speed * dt
            
            dx = target_x - self.pixel_pos[0]
            dy = target_y - self.pixel_pos[1]
            
            if dx > 0:
                self.facing_right = True
            elif dx < 0:
                self.facing_right = False
                
            dist = (dx**2 + dy**2)**0.5

            if dist <= move_dist:
                self.pixel_pos[0] = target_x
                self.pixel_pos[1] = target_y
                self.grid_pos = self.target_grid_pos
                self.target_grid_pos = None
            else:
                self.pixel_pos[0] += (dx / dist) * move_dist
                self.pixel_pos[1] += (dy / dist) * move_dist
        else:
            self.animation_timer = 0.0

    def draw(self, surface, camera_x=0, camera_y=0):
        if self.image:
            image_to_draw = self.image
            if not self.facing_right:
                image_to_draw = pygame.transform.flip(self.image, True, False)
                
            center_x = self.pixel_pos[0] - camera_x + TILE_SIZE / 2
            center_y = self.pixel_pos[1] - camera_y + TILE_SIZE / 2
                
            if self.target_grid_pos:
                bob_offset = abs(math.sin(self.animation_timer * 15)) * 8
                center_y -= bob_offset
                swing_angle = math.sin(self.animation_timer * 15) * 5
                image_to_draw = pygame.transform.rotate(image_to_draw, swing_angle)

            draw_rect = image_to_draw.get_rect(center=(center_x, center_y))
            surface.blit(image_to_draw, draw_rect)
        else:
            player_rect = pygame.Rect(self.pixel_pos[0] - camera_x, self.pixel_pos[1] - camera_y, TILE_SIZE, TILE_SIZE)
            pygame.draw.rect(surface, (200, 50, 200), player_rect)
