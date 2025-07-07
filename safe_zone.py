import pygame

class SafeZone:
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)

        # Load the safe zone image
        # self.image = pygame.image.load("safe_zone.png").convert_alpha()
        self.image = pygame.image.load("assets/helicopter.png").convert_alpha()
        
        # Scale the image to match the safe zone size
        self.image = pygame.transform.scale(self.image, (self.width, self.height))

    def draw(self, screen):
        screen.blit(self.image, self.rect.topleft)

