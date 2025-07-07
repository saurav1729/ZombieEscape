import pygame
import random
import math
import noise
from settings import GRID_WIDTH, GRID_HEIGHT, TILE_SIZE, MAP_HEIGHT, MAP_WIDTH, SCREEN_HEIGHT, SCREEN_WIDTH, BLACK, WHITE, RED ,GREEN ,GRAY , YELLOW
from game_states import GameState, ResourceType
from player import Player
from safe_zone import SafeZone
from zombie import Zombie
from obstacle import Resource, Obstacle
from trap import Trap
import sys


pygame.init()
pygame.mixer.init()


# Create screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Zombie Escape")
clock = pygame.time.Clock()

# Load sounds
try:
    heartbeat_sound = pygame.mixer.Sound("assets/heartbeat.wav")
    zombie_growl = pygame.mixer.Sound("assets/zombie_growl.mp3")
    pickup_sound = pygame.mixer.Sound("assets/pickup.mp3")
    # Use placeholder sounds if files are missing
except:
    heartbeat_sound = pygame.mixer.Sound(pygame.mixer.Sound.get_length())
    zombie_growl = pygame.mixer.Sound(pygame.mixer.Sound.get_length())
    pickup_sound = pygame.mixer.Sound(pygame.mixer.Sound.get_length())

# Font
font = pygame.font.SysFont(None, 36)
small_font = pygame.font.SysFont(None, 24)


class Game:
    def __init__(self, difficulty="normal"):
        self.state = GameState.MAIN_MENU
        self.grid = [[0 for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
        self.player = None
        self.zombies = []
        self.obstacles = []
        self.resources = []
        self.safe_zone = None
        self.traps = []
        self.difficulty = difficulty
        self.time_elapsed = 0
        self.noise_level = 0
        self.weather = "clear"
        self.weather_timer = 0
        self.weather_duration = 600  # 10 seconds at 60 FPS
        self.fog_intensity = 0
    
    def init_game(self):
        # Clear previous game objects
        self.grid = [[0 for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
        self.zombies = []
        self.obstacles = []
        self.resources = []
        self.traps = []
        self.time_elapsed = 0
        
        # Generate map with Perlin noise
        self.generate_map()
        
        # Create player at random position where there's no obstacle
        player_pos = self.find_empty_position()
        self.player = Player(player_pos[0] * TILE_SIZE, player_pos[1] * TILE_SIZE)
        
        # Create safe zone at a position far from player
        safe_pos = self.find_position_far_from_player()
        self.safe_zone = SafeZone(safe_pos[0] * TILE_SIZE, safe_pos[1] * TILE_SIZE, 
                                  TILE_SIZE * 2, TILE_SIZE * 2)
        
        # Create zombies based on difficulty
        num_zombies = 5 if self.difficulty == "easy" else (10 if self.difficulty == "normal" else 15)
        for _ in range(num_zombies):
            zombie_pos = self.find_empty_position(min_dist_from_player=200)
            zombie_type = random.choice(["normal", "normal", "markov"])  # 2/3 normal, 1/3 markov
            self.zombies.append(Zombie(zombie_pos[0] * TILE_SIZE, zombie_pos[1] * TILE_SIZE, zombie_type))
        
        # Create resources
        num_resources = 15 if self.difficulty == "easy" else (10 if self.difficulty == "normal" else 7)
        for _ in range(num_resources):
            resource_pos = self.find_empty_position()
            resource_type = random.choice(list(ResourceType))
            self.resources.append(Resource(resource_pos[0] * TILE_SIZE, resource_pos[1] * TILE_SIZE, resource_type))
        
        # Start with clear weather
        self.weather = "clear"
        self.fog_intensity = 0
        self.weather_timer = self.weather_duration
    
    def generate_map(self):
        # Generate obstacles using Perlin noise
        scale = 15.0
        octaves = 6
        persistence = 0.5
        lacunarity = 2.0
        seed = random.randint(0, 1000)
        
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                # Generate Perlin noise value
                nx = x / GRID_WIDTH - 0.5
                ny = y / GRID_HEIGHT - 0.5
                value = noise.pnoise2(nx * scale, ny * scale, 
                                     octaves=octaves, 
                                     persistence=persistence, 
                                     lacunarity=lacunarity, 
                                     repeatx=1024, 
                                     repeaty=1024, 
                                     base=seed)
                
                # Create obstacles based on noise value
                if value > 0.2:  # Wall
                    self.grid[y][x] = 1
                    obstacle_type = "wall"
                    if value > 0.3:  # Tree
                        obstacle_type = "tree"
                    self.obstacles.append(Obstacle(x * TILE_SIZE, y * TILE_SIZE, 
                                                TILE_SIZE, TILE_SIZE, obstacle_type))
                
                # Add some random fences
                elif random.random() < 0.02:
                    self.grid[y][x] = 1
                    self.obstacles.append(Obstacle(x * TILE_SIZE, y * TILE_SIZE, 
                                                TILE_SIZE, TILE_SIZE, "fence"))
    
    def find_empty_position(self, min_dist_from_player=0):
        while True:
            x = random.randint(0, GRID_WIDTH - 1)
            y = random.randint(0, GRID_HEIGHT - 1)
            
            # Check if position is empty (no obstacles)
            if self.grid[y][x] == 0:
                # If player exists and min_dist is specified, check distance
                if self.player and min_dist_from_player > 0:
                    player_x, player_y = self.player.get_grid_pos()
                    dist = math.sqrt((x - player_x)**2 + (y - player_y)**2) * TILE_SIZE
                    if dist < min_dist_from_player:
                        continue
                
                return (x, y)
    
    def find_position_far_from_player(self):
        player_x, player_y = self.player.get_grid_pos()
        max_dist = 0
        best_pos = None

        # Define safe zone boundaries (3 tiles inside the border)
        min_x, min_y = 3, 3
        max_x = (MAP_WIDTH // TILE_SIZE) - 3
        max_y = (MAP_HEIGHT // TILE_SIZE) - 3

        # Try several random positions and pick the farthest one
        for _ in range(50):
            pos = self.find_empty_position()

            # Ensure the position is at least 3 tiles inside all borders
            if min_x <= pos[0] <= max_x and min_y <= pos[1] <= max_y:
                dist = math.sqrt((pos[0] - player_x) ** 2 + (pos[1] - player_y) ** 2)
                if dist > max_dist:
                    max_dist = dist
                    best_pos = pos

        # Fallback: If no position is found, place it at the center
        if best_pos is None:
            best_pos = ((max_x + min_x) // 2, (max_y + min_y) // 2)

        return best_pos



    
    def update_game(self):
        # Update timer
        self.time_elapsed += 1
        
        # Process keyboard input
        # Process keyboard input
        keys = pygame.key.get_pressed()
        dx, dy = 0, 0

# Movement with W, A, S, D or Arrow Keys
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            dy = -self.player.speed
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            dy = self.player.speed
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            dx = -self.player.speed
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            dx = self.player.speed

# Sprint with Shift key
        if (keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]) and self.player.stamina > 0:
            self.player.sprinting = True
        else:
            self.player.sprinting = False

        
        # Use items with number keys
        if keys[pygame.K_1]:
            if self.player.use_item(ResourceType.FOOD):
                self.player.restore_stamina(30)
        if keys[pygame.K_2]:
            if self.player.use_item(ResourceType.WATER):
                self.player.restore_stamina(20)
        if keys[pygame.K_3]:
            if self.player.use_item(ResourceType.MEDKIT):
                self.player.heal(50)
        if keys[pygame.K_4]:
            if self.player.use_item(ResourceType.FLASHBANG):
                # Stun all zombies within radius
                for zombie in self.zombies:
                    dist = math.sqrt((zombie.rect.centerx - self.player.rect.centerx)**2 + 
                                   (zombie.rect.centery - self.player.rect.centery)**2)
                    if dist < 200:  # Flashbang radius
                        zombie.stun(180)  # 3 seconds at 60 FPS
                self.noise_level = 50  # Create loud noise
        if keys[pygame.K_5]:
            if self.player.use_item(ResourceType.TRAP):
                # Place trap at player position
                self.traps.append(Trap(self.player.rect.centerx, self.player.rect.centery))
        
        # Move player
        self.player.move(dx, dy, self.obstacles)
        
        # Update noise level (decays over time)
        if self.noise_level > 0:
            self.noise_level -= 0.5
        
        # Check collisions with resources
        for resource in list(self.resources):
            if self.player.rect.colliderect(resource.rect):
                self.player.add_to_inventory(resource.type)
                self.resources.remove(resource)
                pickup_sound.play()
                
                # Apply immediate effects
                if resource.type == ResourceType.FOOD:
                    self.player.restore_stamina(20)
                elif resource.type == ResourceType.WATER:
                    self.player.restore_stamina(15)
                elif resource.type == ResourceType.MEDKIT:
                    self.player.heal(30)
        
        # Check collisions with traps (for zombies)
        for trap in list(self.traps):
            if trap.activated:
                if trap.update():  # Returns True if trap duration is over
                    self.traps.remove(trap)
            else:
                for zombie in self.zombies:
                    if zombie.rect.colliderect(trap.rect):
                        trap.activated = True
                        zombie.stun(300)  # 5 seconds at 60 FPS
        
        # Update zombies
        for zombie in self.zombies:
            zombie.update(self.player, self.obstacles, self.grid, self.noise_level)
            zombie.update_movement(self.player, self.obstacles, self.grid)
            
            # Check collision with player
          # Check collision with player
            if zombie.rect.colliderect(self.player.rect) and not zombie.is_stunned:
                if self.player.take_damage(1):  # Returns True if player died
                    self.state = GameState.GAME_OVER
                    zombie_growl.play()
        
        # Check if player reached safe zone
        if self.safe_zone.rect.colliderect(self.player.rect):
            self.state = GameState.WIN
        
        # Update weather
        self.update_weather()
    
    def update_weather(self):
        self.weather_timer -= 1
        
        if self.weather_timer <= 0:
            # Change weather randomly
            weathers = ["clear", "fog", "rain", "storm"]
            weights = [0.4, 0.3, 0.2, 0.1]  # Probabilities for each weather
            self.weather = random.choices(weathers, weights=weights, k=1)[0]
            self.weather_timer = self.weather_duration + random.randint(-100, 100)
            
            # Set fog intensity if fog weather
            if self.weather == "fog":
                self.fog_intensity = random.uniform(0.3, 0.7)
            else:
                self.fog_intensity = 0
    
    def draw_game(self):
        # Clear screen
        screen.fill(BLACK)
        
        # Draw obstacles
        for obstacle in self.obstacles:
            obstacle.draw(screen)
        
        # Draw safe zone
        self.safe_zone.draw(screen)
        
        # Draw resources
        for resource in self.resources:
            resource.draw(screen)
        
        # Draw traps
        for trap in self.traps:
            trap.draw(screen)
        
        # Draw zombies
        for zombie in self.zombies:
            zombie.draw(screen)
        
        # Draw player
        self.player.draw(screen)
        
        # Draw UI
        self.draw_ui()
        
        # Apply weather effects
        self.apply_weather_effects()
    
    def apply_weather_effects(self):
        if self.weather == "fog":
            # Create fog effect by drawing semi-transparent overlay
            fog_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            fog_surface.fill((200, 200, 200, int(self.fog_intensity * 150)))
            screen.blit(fog_surface, (0, 0))
        
        elif self.weather == "rain":
            # Create rain effect by drawing lines
            for _ in range(100):
                x = random.randint(0, SCREEN_WIDTH)
                y = random.randint(0, SCREEN_HEIGHT)
                length = random.randint(5, 15)
                pygame.draw.line(screen, (200, 200, 255), (x, y), (x - 2, y + length), 1)
        
        elif self.weather == "storm":
            # Create storm effect with occasional lightning
            for _ in range(150):
                x = random.randint(0, SCREEN_WIDTH)
                y = random.randint(0, SCREEN_HEIGHT)
                length = random.randint(5, 20)
                pygame.draw.line(screen, (200, 200, 255), (x, y), (x - 3, y + length), 1)
            
            # Occasional lightning flash
            if random.random() < 0.02:
                flash_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                flash_surface.fill((255, 255, 255, 50))
                screen.blit(flash_surface, (0, 0))
    
    def draw_ui(self):
        ui_x = SCREEN_WIDTH - 220  # UI panel starts at the right edge

        # Draw UI background panel
        pygame.draw.rect(screen, (50, 50, 50), (ui_x, 0, 220, SCREEN_HEIGHT))  # Dark UI background

        # Load images (ensure these images exist in your assets folder)
        health_icon = pygame.image.load("assets/medkit.png")
        stamina_icon = pygame.image.load("assets/medkit.png")
        inventory_icon = pygame.image.load("assets/food.png")
        weather_icon = pygame.image.load("assets/food.png")
        danger_icon = pygame.image.load("assets/zombie.png")

        health_icon = pygame.transform.scale(health_icon, (25, 25))
        stamina_icon = pygame.transform.scale(stamina_icon, (25, 25))
        inventory_icon = pygame.transform.scale(inventory_icon, (25, 25))
        weather_icon = pygame.transform.scale(weather_icon, (25, 25))
        danger_icon = pygame.transform.scale(danger_icon, (40, 40))

        # Draw health and stamina bars with icons
        health_width = int(160 * (self.player.health / self.player.max_health))
        stamina_width = int(160 * (self.player.stamina / self.player.max_stamina))

        screen.blit(health_icon, (ui_x + 10, 10))
        pygame.draw.rect(screen, RED, (ui_x + 40, 15, 160, 20))  # Background bar
        pygame.draw.rect(screen, GREEN, (ui_x + 40, 15, health_width, 20))  # Filled bar

        screen.blit(stamina_icon, (ui_x + 10, 45))
        pygame.draw.rect(screen, GRAY, (ui_x + 40, 50, 160, 15))  # Background bar
        pygame.draw.rect(screen, YELLOW, (ui_x + 40, 50, stamina_width, 15))  # Filled bar

        # Draw inventory section with icons
        screen.blit(inventory_icon, (ui_x + 10, 85))
        inventory_text = font.render("Inventory:", True, WHITE)
        screen.blit(inventory_text, (ui_x + 40, 85))

        y_offset = 120
        for res_type in ResourceType:
            count = self.player.inventory[res_type]
            item_image = pygame.image.load(f"assets/{res_type.name.lower()}.png")  
            item_image = pygame.transform.scale(item_image, (30, 30))  
            screen.blit(item_image, (ui_x + 10, y_offset))
            count_text = small_font.render(f"x{count}", True, WHITE)
            screen.blit(count_text, (ui_x + 50, y_offset + 5))
            y_offset += 40  

        # Draw weather indicator with an image
        screen.blit(weather_icon, (ui_x + 10, SCREEN_HEIGHT - 80))
        weather_text = small_font.render(self.weather.capitalize(), True, WHITE)
        screen.blit(weather_text, (ui_x + 50, SCREEN_HEIGHT - 75))

        # Draw zombie proximity indicator
        closest_zombie_dist = float('inf')
        for zombie in self.zombies:
            dist = math.sqrt((zombie.rect.centerx - self.player.rect.centerx)**2 + 
                            (zombie.rect.centery - self.player.rect.centery)**2)
            closest_zombie_dist = min(closest_zombie_dist, dist)

        if closest_zombie_dist < 150:
            screen.blit(danger_icon, (ui_x + 10, SCREEN_HEIGHT - 40))  # Show danger icon
    
    
    
    
    def draw_main_menu(self):
        # Draw dark background with fog effect
        screen.fill((20, 20, 30))
        
        # Add wandering zombies in background
        for i in range(10):
            x = int(SCREEN_WIDTH / 2 + 100 * math.sin(self.time_elapsed / 100 + i))
            y = int(SCREEN_HEIGHT / 2 + 80 * math.cos(self.time_elapsed / 120 + i))
            pygame.draw.rect(screen, (150, 0, 0), (x, y, 20, 20))
        
        # Draw title
        title_text = pygame.font.SysFont(None, 72).render("ZOMBIE ESCAPE", True, RED)
        screen.blit(title_text, (SCREEN_WIDTH // 2 - title_text.get_width() // 2, 100))
        
        # Draw buttons
        button_width, button_height = 200, 50
        button_x = SCREEN_WIDTH // 2 - button_width // 2
        
        # Play button
        play_button = pygame.Rect(button_x, 250, button_width, button_height)
        pygame.draw.rect(screen, GRAY, play_button)
        play_text = font.render("PLAY", True, WHITE)
        screen.blit(play_text, (play_button.centerx - play_text.get_width() // 2, 
                              play_button.centery - play_text.get_height() // 2))
        
        # Settings button
        settings_button = pygame.Rect(button_x, 320, button_width, button_height)
        pygame.draw.rect(screen, GRAY, settings_button)
        settings_text = font.render("SETTINGS", True, WHITE)
        screen.blit(settings_text, (settings_button.centerx - settings_text.get_width() // 2, 
                                  settings_button.centery - settings_text.get_height() // 2))
        
        # Quit button
        quit_button = pygame.Rect(button_x, 390, button_width, button_height)
        pygame.draw.rect(screen, GRAY, quit_button)
        quit_text = font.render("QUIT", True, WHITE)
        screen.blit(quit_text, (quit_button.centerx - quit_text.get_width() // 2, 
                              quit_button.centery - quit_text.get_height() // 2))
        
        # Heartbeat effect
        if self.time_elapsed % 60 == 0:
            heartbeat_sound.play()
        
        return play_button, settings_button, quit_button
    
    def draw_settings_menu(self):
        # Draw background
        screen.fill((20, 20, 30))
        
        # Draw title
        title_text = pygame.font.SysFont(None, 72).render("SETTINGS", True, WHITE)
        screen.blit(title_text, (SCREEN_WIDTH // 2 - title_text.get_width() // 2, 100))
        
        # Draw difficulty options
        button_width, button_height = 200, 50
        button_x = SCREEN_WIDTH // 2 - button_width // 2
        
        # Easy button
        easy_button = pygame.Rect(button_x, 250, button_width, button_height)
        if self.difficulty == "easy":
            pygame.draw.rect(screen, GREEN, easy_button)
        else:
            pygame.draw.rect(screen, GRAY, easy_button)
        easy_text = font.render("EASY", True, WHITE)
        screen.blit(easy_text, (easy_button.centerx - easy_text.get_width() // 2, 
                              easy_button.centery - easy_text.get_height() // 2))
        
        # Normal button
        normal_button = pygame.Rect(button_x, 320, button_width, button_height)
        if self.difficulty == "normal":
            pygame.draw.rect(screen, GREEN, normal_button)
        else:
            pygame.draw.rect(screen, GRAY, normal_button)
        normal_text = font.render("NORMAL", True, WHITE)
        screen.blit(normal_text, (normal_button.centerx - normal_text.get_width() // 2, 
                                normal_button.centery - normal_text.get_height() // 2))
        
        # Hard button
        hard_button = pygame.Rect(button_x, 390, button_width, button_height)
        if self.difficulty == "hard":
            pygame.draw.rect(screen, GREEN, hard_button)
        else:
            pygame.draw.rect(screen, GRAY, hard_button)
        hard_text = font.render("HARD", True, WHITE)
        screen.blit(hard_text, (hard_button.centerx - hard_text.get_width() // 2, 
                              hard_button.centery - hard_text.get_height() // 2))
        
        # Back button
        back_button = pygame.Rect(button_x, 460, button_width, button_height)
        pygame.draw.rect(screen, GRAY, back_button)
        back_text = font.render("BACK", True, WHITE)
        screen.blit(back_text, (back_button.centerx - back_text.get_width() // 2, 
                              back_button.centery - back_text.get_height() // 2))
        
        return easy_button, normal_button, hard_button, back_button
    
    def draw_game_over(self):
        # Draw dark red background
        screen.fill((50, 0, 0))
        
        # Draw game over text
        gameover_text = pygame.font.SysFont(None, 72).render("GAME OVER", True, WHITE)
        screen.blit(gameover_text, (SCREEN_WIDTH // 2 - gameover_text.get_width() // 2, 200))
        
        # Draw buttons
        button_width, button_height = 200, 50
        button_x = SCREEN_WIDTH // 2 - button_width // 2
        
        # Restart button
        restart_button = pygame.Rect(button_x, 300, button_width, button_height)
        pygame.draw.rect(screen, GRAY, restart_button)
        restart_text = font.render("RESTART", True, WHITE)
        screen.blit(restart_text, (restart_button.centerx - restart_text.get_width() // 2, 
                                 restart_button.centery - restart_text.get_height() // 2))
        
        # Main menu button
        menu_button = pygame.Rect(button_x, 370, button_width, button_height)
        pygame.draw.rect(screen, GRAY, menu_button)
        menu_text = font.render("MAIN MENU", True, WHITE)
        screen.blit(menu_text, (menu_button.centerx - menu_text.get_width() // 2, 
                              menu_button.centery - menu_text.get_height() // 2))
        
        # Quit button
        quit_button = pygame.Rect(button_x, 440, button_width, button_height)
        pygame.draw.rect(screen, GRAY, quit_button)
        quit_text = font.render("QUIT", True, WHITE)
        screen.blit(quit_text, (quit_button.centerx - quit_text.get_width() // 2, 
                              quit_button.centery - quit_text.get_height() // 2))
        
        return restart_button, menu_button, quit_button
    
    def draw_win_screen(self):
        # Draw dark green background
        screen.fill((0, 50, 0))
        
        # Draw win text
        win_text = pygame.font.SysFont(None, 72).render("YOU SURVIVED!", True, WHITE)
        screen.blit(win_text, (SCREEN_WIDTH // 2 - win_text.get_width() // 2, 200))
        
        # Draw buttons
        button_width, button_height = 200, 50
        button_x = SCREEN_WIDTH // 2 - button_width // 2
        
        # Play again button
        play_again_button = pygame.Rect(button_x, 300, button_width, button_height)
        pygame.draw.rect(screen, GRAY, play_again_button)
        play_again_text = font.render("PLAY AGAIN", True, WHITE)
        screen.blit(play_again_text, (play_again_button.centerx - play_again_text.get_width() // 2, 
                                    play_again_button.centery - play_again_text.get_height() // 2))
        
        # Main menu button
        menu_button = pygame.Rect(button_x, 370, button_width, button_height)
        pygame.draw.rect(screen, GRAY, menu_button)
        menu_text = font.render("MAIN MENU", True, WHITE)
        screen.blit(menu_text, (menu_button.centerx - menu_text.get_width() // 2, 
                              menu_button.centery - menu_text.get_height() // 2))
        
        # Quit button
        quit_button = pygame.Rect(button_x, 440, button_width, button_height)
        pygame.draw.rect(screen, GRAY, quit_button)
        quit_text = font.render("QUIT", True, WHITE)
        screen.blit(quit_text, (quit_button.centerx - quit_text.get_width() // 2, 
                              quit_button.centery - quit_text.get_height() // 2))
        
        return play_again_button, menu_button, quit_button
    
    def handle_menu_event(self, event):
        if self.state == GameState.MAIN_MENU:
            play_button, settings_button, quit_button = self.draw_main_menu()
            
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if play_button.collidepoint(event.pos):
                    self.state = GameState.PLAYING
                    self.init_game()
                elif settings_button.collidepoint(event.pos):
                    self.state = GameState.SETTINGS
                elif quit_button.collidepoint(event.pos):
                    pygame.quit()
                    sys.exit()
        
        elif self.state == GameState.SETTINGS:
            easy_button, normal_button, hard_button, back_button = self.draw_settings_menu()
            
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if easy_button.collidepoint(event.pos):
                    self.difficulty = "easy"
                elif normal_button.collidepoint(event.pos):
                    self.difficulty = "normal"
                elif hard_button.collidepoint(event.pos):
                    self.difficulty = "hard"
                elif back_button.collidepoint(event.pos):
                    self.state = GameState.MAIN_MENU
        
        elif self.state == GameState.GAME_OVER:
            restart_button, menu_button, quit_button = self.draw_game_over()
            
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if restart_button.collidepoint(event.pos):
                    self.state = GameState.PLAYING
                    self.init_game()
                elif menu_button.collidepoint(event.pos):
                    self.state = GameState.MAIN_MENU
                elif quit_button.collidepoint(event.pos):
                    pygame.quit()
                    sys.exit()
        
        elif self.state == GameState.WIN:
            play_again_button, menu_button, quit_button = self.draw_win_screen()
            
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if play_again_button.collidepoint(event.pos):
                    self.state = GameState.PLAYING
                    self.init_game()
                elif menu_button.collidepoint(event.pos):
                    self.state = GameState.MAIN_MENU
                elif quit_button.collidepoint(event.pos):
                    pygame.quit()
                    sys.exit()
