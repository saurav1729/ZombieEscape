from enum import Enum



# Game states
class GameState(Enum):
    MAIN_MENU = 0
    PLAYING = 1
    GAME_OVER = 2
    WIN = 3
    SETTINGS = 4

# Zombie states
class ZombieState(Enum):
    IDLE = 0
    CHASE = 1
    INVESTIGATE = 2

# Resource types
class ResourceType(Enum):
    FOOD = 0
    WATER = 1
    MEDKIT = 2
    WEAPON = 3
    FLASHBANG = 4
    TRAP = 5