import pygame
import random
import math
from settings import TILE_SIZE, GRID_HEIGHT,RED, WHITE, YELLOW, GRID_WIDTH
from game_states import ZombieState
from collections import deque


class Zombie:
    def __init__(self, x, y, zombie_type="normal"):
        self.x = x
        self.y = y
        self.width = TILE_SIZE - 10
        self.height = TILE_SIZE - 10
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.type = zombie_type
        self.state = ZombieState.IDLE
        self.speed = 2 if zombie_type == "normal" else 3
        self.detection_radius = 150 if zombie_type == "normal" else 200
        self.target_x = None
        self.target_y = None
        self.path = []
        self.idle_counter = 0
        self.idle_direction = random.choice([(1, 0), (0, 1), (-1, 0), (0, -1)])
        self.idle_direction_change_prob = 0.05
        self.is_stunned = False
        self.stun_time = 0
        # self.color = RED if zombie_type == "normal" else (200, 0, 0)
         # Load zombie images
        self.image_normal = pygame.image.load("assets/zombie.png").convert_alpha()
        self.image_stunned = pygame.image.load("assets/people.png").convert_alpha()
        self.image_markov = pygame.image.load("assets/markov.png").convert_alpha()
        self.image_normal = pygame.transform.scale(self.image_normal, (self.width, self.height))
        self.image_stunned = pygame.transform.scale(self.image_stunned, (self.width, self.height))
        self.image_markov = pygame.transform.scale(self.image_markov, (self.width, self.height))
        # For Markov chain-based zombies
        self.is_markov = (zombie_type == "markov")
        self.markov_direction = random.choice([(1, 0), (0, 1), (-1, 0), (0, -1)])
        self.direction_change_prob = 0.2
        
    def update(self, player, obstacles, grid, noise_level=0):
        if self.is_stunned:
            self.stun_time -= 1
            if self.stun_time <= 0:
                self.is_stunned = False
            return
        
        player_pos = player.get_grid_pos()
        zombie_grid_pos = (int(self.rect.centerx // TILE_SIZE), int(self.rect.centery // TILE_SIZE))
        
        # Check if player is within detection radius
        dist_to_player = math.sqrt((self.rect.centerx - player.rect.centerx)**2 + 
                                  (self.rect.centery - player.rect.centery)**2)
        
        # Adjust detection based on noise level
        effective_detection_radius = self.detection_radius + noise_level + player.last_noise_level
        
        if dist_to_player < effective_detection_radius:
            self.state = ZombieState.CHASE
            self.find_path_to_player(zombie_grid_pos, player_pos, grid)
        elif noise_level > 0 or player.last_noise_level > 0:
            self.state = ZombieState.INVESTIGATE
            # Move towards the player's general direction
            if random.random() < 0.7:  # 70% chance to move towards noise
                dx = 1 if player.rect.centerx > self.rect.centerx else -1
                dy = 1 if player.rect.centery > self.rect.centery else -1
                self.move_in_direction(dx, dy, obstacles)
            else:
                self.random_movement(obstacles)
        else:
            # If not chasing, go back to idle state
            if self.state != ZombieState.IDLE:
                self.state = ZombieState.IDLE
                self.idle_counter = 0
            
            if self.is_markov:
                self.markov_movement(obstacles)
            else:
                self.idle_movement(obstacles)
    
    def find_path_to_player(self, start, goal, grid):
        # Breadth-First Search implementation
        queue = deque([start])
        visited = {start: None}
        
        while queue:
            current = queue.popleft()
            
            if current == goal:
                # Reconstruct path
                path = []
                while current != start:
                    path.append(current)
                    current = visited[current]
                path.reverse()
                self.path = path
                return
            
            # Explore neighbors
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                nx, ny = current[0] + dx, current[1] + dy
                
                # Check if in bounds and walkable
                if (0 <= nx < GRID_WIDTH and 0 <= ny < GRID_HEIGHT and 
                    (nx, ny) not in visited and grid[ny][nx] == 0):
                    queue.append((nx, ny))
                    visited[(nx, ny)] = current
        
        # If no path found, clear the path
        self.path = []
    
    def follow_path(self, obstacles):
        if not self.path:
            return
            
        next_pos = self.path[0]
        target_x = next_pos[0] * TILE_SIZE + TILE_SIZE // 2
        target_y = next_pos[1] * TILE_SIZE + TILE_SIZE // 2
        
        dx = target_x - self.rect.centerx
        dy = target_y - self.rect.centery
        
        # Normalize direction
        dist = math.sqrt(dx*dx + dy*dy)
        if dist > 0:
            dx = dx / dist * self.speed
            dy = dy / dist * self.speed
        
        # Move zombie
        new_rect = self.rect.copy()
        new_rect.x += dx
        if not any(new_rect.colliderect(obstacle.rect) for obstacle in obstacles):
            self.rect.x += dx
        
        new_rect = self.rect.copy()
        new_rect.y += dy
        if not any(new_rect.colliderect(obstacle.rect) for obstacle in obstacles):
            self.rect.y += dy
        
        # Check if reached the next point in path
        if abs(self.rect.centerx - target_x) < self.speed and abs(self.rect.centery - target_y) < self.speed:
            self.path.pop(0)
    
    def idle_movement(self, obstacles):
        self.idle_counter += 1
        
        # Change direction randomly
        if self.idle_counter > 60 or random.random() < self.idle_direction_change_prob:
            self.idle_direction = random.choice([(1, 0), (0, 1), (-1, 0), (0, -1)])
            self.idle_counter = 0
        
        dx, dy = self.idle_direction
        dx *= self.speed / 2  # Slower in idle
        dy *= self.speed / 2
        
        self.move_in_direction(dx, dy, obstacles)
    
    def markov_movement(self, obstacles):
        if random.random() < self.direction_change_prob:
            # Higher chance to maintain general direction
            current_dx, current_dy = self.markov_direction
            directions = [(1, 0), (0, 1), (-1, 0), (0, -1)]
            
            weights = []
            for dx, dy in directions:
                # Same direction gets highest weight
                if (dx, dy) == (current_dx, current_dy):
                    weights.append(0.5)
                # Opposite direction gets lowest weight
                elif (dx, dy) == (-current_dx, -current_dy):
                    weights.append(0.1)
                # Other directions get medium weight
                else:
                    weights.append(0.2)
            
            self.markov_direction = random.choices(directions, weights=weights, k=1)[0]
        
        dx, dy = self.markov_direction
        dx *= self.speed / 1.5  # Slightly faster than idle
        dy *= self.speed / 1.5
        
        self.move_in_direction(dx, dy, obstacles)
    
    def move_in_direction(self, dx, dy, obstacles):
        # Test x movement
        new_rect = self.rect.copy()
        new_rect.x += dx
        if not any(new_rect.colliderect(obstacle.rect) for obstacle in obstacles):
            self.rect.x += dx
        else:
            # If blocked in x direction, try random new direction
            if self.is_markov:
                self.markov_direction = random.choice([(0, 1), (0, -1)])
            else:
                self.idle_direction = random.choice([(0, 1), (0, -1)])
        
        # Test y movement
        new_rect = self.rect.copy()
        new_rect.y += dy
        if not any(new_rect.colliderect(obstacle.rect) for obstacle in obstacles):
            self.rect.y += dy
        else:
            if self.is_markov:
                self.markov_direction = random.choice([(1, 0), (-1, 0)])
            else:
                self.idle_direction = random.choice([(1, 0), (-1, 0)])
    
    def random_movement(self, obstacles):
        dx = random.choice([-1, 0, 1]) * self.speed
        dy = random.choice([-1, 0, 1]) * self.speed
        self.move_in_direction(dx, dy, obstacles)
    
    def draw(self, screen):
        if self.is_stunned:
           zombie_image = self.image_stunned
        elif self.is_markov:
           zombie_image = self.image_markov
        else:
           zombie_image = self.image_normal
    
    # Draw the selected zombie image
        screen.blit(zombie_image, self.rect.topleft)
        
        # Draw state indicator
        if self.state == ZombieState.CHASE:
            pygame.draw.circle(screen, RED, (self.rect.centerx, self.rect.centery), 5)
        elif self.state == ZombieState.INVESTIGATE:
            pygame.draw.circle(screen, YELLOW, (self.rect.centerx, self.rect.centery), 5)
        
        # Draw stunned indicator
        if self.is_stunned:
            pygame.draw.circle(screen, WHITE, (self.rect.centerx, self.rect.centery), 10, 2)
    
    def stun(self, duration):
        self.is_stunned = True
        self.stun_time = duration
    
    def update_movement(self, player, obstacles, grid):
        if self.state == ZombieState.CHASE:
            self.follow_path(obstacles)
        elif self.state == ZombieState.INVESTIGATE:
            # Already handled in the update method
            pass
        elif self.is_markov:
            self.markov_movement(obstacles)
        else:
            self.idle_movement(obstacles)
