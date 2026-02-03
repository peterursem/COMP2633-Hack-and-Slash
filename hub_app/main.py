# hub_app/main.py
import pygame

from .hub.deck_store import DeckStore
from .hub.screens import WIDTH, HEIGHT, MainMenuScreen


class HubApp:
    def __init__(self):
        self.store = DeckStore("decks.json")
        self.running = True
        self.screen_obj = MainMenuScreen(self)

    def run(self):
        pygame.init()
        screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Hub App: Flashcards + Card Game")
        clock = pygame.time.Clock()

        font = pygame.font.SysFont(None, 26)
        big_font = pygame.font.SysFont(None, 38)

        while self.running:
            clock.tick(60)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                else:
                    self.screen_obj.handle_event(event)

            # screen transition
            if self.screen_obj.next_screen is not None:
                self.screen_obj = self.screen_obj.next_screen

            self.screen_obj.update()
            self.screen_obj.draw(screen, font, big_font)
            pygame.display.flip()

        pygame.quit()


if __name__ == "__main__":
    HubApp().run()
