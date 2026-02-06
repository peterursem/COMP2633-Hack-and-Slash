import pygame
from cardgame.engine import GameEngine
from cardgame.ui_pygame import ManaBossCardGameUI, WIDTH, HEIGHT

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Mana Boss Card Game")
    clock = pygame.time.Clock()

    font = pygame.font.SysFont(None, 26)
    big_font = pygame.font.SysFont(None, 38)

    engine = GameEngine()
    ui = ManaBossCardGameUI(engine)

    running = True
    while running:
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            ui.handle_event(event)

        ui.draw(screen, font, big_font)
        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()
