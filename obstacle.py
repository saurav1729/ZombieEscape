import pygame
from settings import TILE_SIZE
from game_states import ResourceType



class Obstacle:
    def __init__(self, x, y, width, height, obstacle_type="wall"):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.type = obstacle_type
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)

        # Load images based on obstacle type
        if obstacle_type == "wall":
            self.image = pygame.image.load("assets/wall.png").convert_alpha()
        elif obstacle_type == "tree":
            self.image = pygame.image.load("assets/tree.png").convert_alpha()
        elif obstacle_type == "fence":
            self.image = pygame.image.load("assets/fence.png").convert_alpha()
        elif obstacle_type == "rock":
            self.image = pygame.image.load("assets/rock.png").convert_alpha()
        else:
            self.image = pygame.image.load("assets/default.png").convert_alpha()  # Default image
        
        # Scale image to match obstacle size
        self.image = pygame.transform.scale(self.image, (self.width, self.height))

    def draw(self, screen):
        screen.blit(self.image, self.rect.topleft)
        
        
class Resource:
    def __init__(self, x, y, resource_type):
        self.x = x
        self.y = y
        self.type = resource_type
        self.width = TILE_SIZE // 2
        self.height = TILE_SIZE // 2
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)

        # Load resource images based on type
        if resource_type == ResourceType.FOOD:
            self.image = pygame.image.load("assets/food.png").convert_alpha()
        elif resource_type == ResourceType.WATER:
            self.image = pygame.image.load("assets/water.png").convert_alpha()
        elif resource_type == ResourceType.MEDKIT:
            self.image = pygame.image.load("assets/medkit.png").convert_alpha()
        elif resource_type == ResourceType.WEAPON:
            self.image = pygame.image.load("assets/weapon.png").convert_alpha()
        elif resource_type == ResourceType.FLASHBANG:
            self.image = pygame.image.load("assets/flashbang.png").convert_alpha()
        elif resource_type == ResourceType.TRAP:
            self.image = pygame.image.load("assets/trap.png").convert_alpha()
        else:
            self.image = pygame.image.load("assets/default_resource.png").convert_alpha()  # Default image
        
        # Scale the image to match the resource size
        self.image = pygame.transform.scale(self.image, (self.width, self.height))

    def draw(self, screen):
        screen.blit(self.image, self.rect.topleft)

