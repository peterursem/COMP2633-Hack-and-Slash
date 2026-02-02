import os
import pygame

from flash_repo import JsonFileRepository, HttpApiRepository
from flash_service import FlashcardService
from flash_ui import FlashcardsPygameApp


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
