import os
import pygame

from flashcards.repositories import JsonFileRepository, HttpApiRepository
from flashcards.service import FlashcardService
from flashcards.ui_pygame import FlashcardsPygameApp


def build_repo():
    backend = os.environ.get("FLASHCARDS_BACKEND", "file")  # "file" or "http"
    if backend == "http":
        base_url = os.environ.get("FLASHCARDS_API_URL", "http://localhost:3000")
        return HttpApiRepository(base_url)
    return JsonFileRepository("flashcards.json")


def main():
    pygame.init()
    screen = pygame.display.set_mode((900, 600))
    pygame.display.set_caption("Flashcards (Modular)")
    clock = pygame.time.Clock()

    font = pygame.font.SysFont(None, 28)
    big_font = pygame.font.SysFont(None, 40)

    repo = build_repo()
    service = FlashcardService(repo)
    app = FlashcardsPygameApp(service)

    running = True
    while running:
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            app.handle_event(event)

        app.draw(screen, font, big_font)
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
