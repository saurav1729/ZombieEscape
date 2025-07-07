import pygame
from settings import TILE_SIZE, MAP_HEIGHT ,MAP_WIDTH ,RED, GREEN, GRAY , YELLOW
from game_states import ResourceType


class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = TILE_SIZE - 10
        self.height = TILE_SIZE - 10
        self.speed = 5
        self.sprint_speed = 8
        self.health = 100
        self.max_health = 100
        self.stamina = 100
        self.max_stamina = 100
        self.stamina_recovery_rate = 0.5
        self.sprinting = False
        self.inventory = {res_type: 0 for res_type in ResourceType}
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.last_noise_level = 0
        self.noise_cooldown = 0
         # Load images
        self.image_idle = pygame.image.load("assets/player_idle.png").convert_alpha()
        self.image_moving = pygame.image.load("assets/player_moving.png").convert_alpha()

        # Scale images
        self.image_idle = pygame.transform.scale(self.image_idle, (self.width, self.height))
        self.image_moving = pygame.transform.scale(self.image_moving, (self.width, self.height))

        # Set default image
        self.image = self.image_idle

    def move(self, dx, dy, obstacles):
        if dx != 0 or dy != 0:
            self.image = self.image_moving  # Change to moving image
        else:
            self.image = self.image_idle 
        # Check sprinting
        if self.sprinting and self.stamina > 0:
            dx *= self.sprint_speed / self.speed
            dy *= self.sprint_speed / self.speed
            self.stamina -= 1
            self.last_noise_level = 20  # Higher noise when sprinting
        else:
            self.sprinting = False
            self.last_noise_level = 5  # Normal movement noise
            if self.stamina < self.max_stamina and self.noise_cooldown <= 0:
                self.stamina += self.stamina_recovery_rate
        
        if self.noise_cooldown > 0:
            self.noise_cooldown -= 1
            
        new_x = self.rect.x + dx
        new_y = self.rect.y + dy

        # Keep player inside the map boundaries
        new_x = max(0, min(new_x, MAP_WIDTH - self.width))
        new_y = max(0, min(new_y, MAP_HEIGHT - self.height))

        new_rect = self.rect.copy()
        new_rect.x = new_x
        if not any(new_rect.colliderect(obstacle.rect) for obstacle in obstacles):
             self.rect.x = new_x
             self.x = self.rect.x

        # Test y movement (collisions)
        new_rect = self.rect.copy()
        new_rect.y = new_y
        if not any(new_rect.colliderect(obstacle.rect) for obstacle in obstacles):
           self.rect.y = new_y
           self.y = self.rect.y

    def draw(self, screen):
        screen.blit(self.image, self.rect.topleft)
        
        # Draw health bar
        health_bar_width = 40
        health_bar_height = 3
        health_ratio = self.health / self.max_health
        pygame.draw.rect(screen, RED, (self.rect.x, self.rect.y - 10, health_bar_width, health_bar_height))
        pygame.draw.rect(screen, GREEN, (self.rect.x, self.rect.y - 10, health_bar_width * health_ratio, health_bar_height))
        
        # Draw stamina bar
        stamina_ratio = self.stamina / self.max_stamina
        pygame.draw.rect(screen, GRAY, (self.rect.x, self.rect.y - 5, health_bar_width, health_bar_height))
        pygame.draw.rect(screen, YELLOW, (self.rect.x, self.rect.y - 5, health_bar_width * stamina_ratio, health_bar_height))

    def take_damage(self, amount):
        self.health -= amount
        if self.health < 0:
            self.health = 0
        return self.health <= 0
    
    def heal(self, amount):
        self.health = min(self.health + amount, self.max_health)
    
    def restore_stamina(self, amount):
        self.stamina = min(self.stamina + amount, self.max_stamina)
    
    def add_to_inventory(self, resource_type):
        self.inventory[resource_type] += 1
        
    def use_item(self, resource_type):
        if self.inventory[resource_type] > 0:
            self.inventory[resource_type] -= 1
            return True
        return False
    
    def get_grid_pos(self):
        return (int(self.rect.centerx // TILE_SIZE), int(self.rect.centery // TILE_SIZE))
