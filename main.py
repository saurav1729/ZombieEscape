import pygame
import sys 
from Game import Game
from game_states import GameState


clock = pygame.time.Clock()

def main():
    game = Game()
    running = True
    
    while running:
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            # Handle menu events
            if game.state != GameState.PLAYING:
                game.handle_menu_event(event)
        
        # Update game state
        if game.state == GameState.PLAYING:
            game.update_game()
        
        # Render game
        if game.state == GameState.PLAYING:
            game.draw_game()
        elif game.state == GameState.MAIN_MENU:
            game.draw_main_menu()
        elif game.state == GameState.SETTINGS:
            game.draw_settings_menu()
        elif game.state == GameState.GAME_OVER:
            game.draw_game_over()
        elif game.state == GameState.WIN:
            game.draw_win_screen()
        
        # Update display
        pygame.display.flip()
        game.time_elapsed += 1
        clock.tick(60)
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()