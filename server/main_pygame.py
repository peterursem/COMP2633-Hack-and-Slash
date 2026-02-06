# hub_app/main_pygame.py
import pygame

from hub_app.hub.engine import HubEngine
from hub_app.hub.screens import MainMenuScreen, WIDTH, HEIGHT


class HubPygameApp:
    def __init__(self):
        self.running = True

        # One shared engine for the whole app (decks + sessions)
        self.engine = HubEngine("decks.json")

        # Backwards-compat: your current screens.py uses self.app.store
        self.store = self.engine.store

        # Start at main menu
        self.screen_obj = MainMenuScreen(self)

    def run(self):
        pygame.init()
        pygame.display.set_caption("Hub App: Flashcards + Card Game")

        screen = pygame.display.set_mode((WIDTH, HEIGHT))
        clock = pygame.time.Clock()

        font = pygame.font.SysFont(None, 26)
        big_font = pygame.font.SysFont(None, 40)

        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    break

                self.screen_obj.handle_event(event)

            # If the current screen requests a transition, switch
            if self.screen_obj.next_screen is not None:
                self.screen_obj = self.screen_obj.next_screen

            self.screen_obj.update()
            self.screen_obj.draw(screen, font, big_font)

            pygame.display.flip()
            clock.tick(60)

        pygame.quit()


def main():
    app = HubPygameApp()
    app.run()


if __name__ == "__main__":
    main()
