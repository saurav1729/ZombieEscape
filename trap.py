import pygame
from settings import TILE_SIZE, BLACK, RED

class Trap:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = TILE_SIZE // 2
        self.height = TILE_SIZE // 2
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.color = (139, 69, 19)  # Brown
        self.activated = False
        self.duration = 300  # 5 seconds at 60 FPS
    
    def update(self):
        if self.activated:
            self.duration -= 1
            return self.duration <= 0
        return False
    
    def draw(self, screen):
        if not self.activated:
            pygame.draw.rect(screen, self.color, self.rect)
            pygame.draw.line(screen, BLACK, 
                            (self.rect.left, self.rect.top), 
                            (self.rect.right, self.rect.bottom), 1)
            pygame.draw.line(screen, BLACK, 
                            (self.rect.left, self.rect.bottom), 
                            (self.rect.right, self.rect.top), 1)
        else:
            pygame.draw.rect(screen, RED, self.rect, 1)

