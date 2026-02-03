# hub/widgets.py
import pygame


class Button:
    def __init__(self, x, y, w, h, text):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text

    def draw(self, screen, font, hover=False):
        border = (30, 30, 30)
        fill = (220, 220, 220) if not hover else (200, 200, 200)
        pygame.draw.rect(screen, fill, self.rect, border_radius=10)
        pygame.draw.rect(screen, border, self.rect, 2, border_radius=10)
        img = font.render(self.text, True, (20, 20, 20))
        screen.blit(img, (self.rect.centerx - img.get_width() // 2,
                          self.rect.centery - img.get_height() // 2))

    def clicked(self, pos):
        return self.rect.collidepoint(pos)


class InputBox:
    def __init__(self, x, y, w, h, placeholder=""):
        self.rect = pygame.Rect(x, y, w, h)
        self.placeholder = placeholder
        self.text = ""
        self.active = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)

        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key == pygame.K_RETURN:
                pass
            else:
                if len(self.text) < 200:
                    self.text += event.unicode

    def draw(self, screen, font):
        border = (50, 50, 50)
        fill = (255, 255, 255) if self.active else (245, 245, 245)
        pygame.draw.rect(screen, fill, self.rect, border_radius=10)
        pygame.draw.rect(screen, border, self.rect, 2, border_radius=10)

        show = self.text if self.text else self.placeholder
        color = (20, 20, 20) if self.text else (140, 140, 140)
        img = font.render(show, True, color)
        screen.blit(img, (self.rect.x + 10, self.rect.y + 10))


class ListBox:
    """
    Very simple selectable list.
    """
    def __init__(self, x, y, w, h):
        self.rect = pygame.Rect(x, y, w, h)
        self.items = []
        self.selected_index = 0
        self.scroll = 0

    def set_items(self, items):
        self.items = items
        self.selected_index = 0
        self.scroll = 0

    def selected_item(self):
        if 0 <= self.selected_index < len(self.items):
            return self.items[self.selected_index]
        return None

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.selected_index = max(0, self.selected_index - 1)
            elif event.key == pygame.K_DOWN:
                self.selected_index = min(len(self.items) - 1, self.selected_index + 1)

        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                # determine which row clicked
                row_h = 28
                local_y = event.pos[1] - self.rect.y
                idx = self.scroll + (local_y // row_h)
                if 0 <= idx < len(self.items):
                    self.selected_index = idx

    def draw(self, screen, font):
        pygame.draw.rect(screen, (255, 255, 255), self.rect, border_radius=10)
        pygame.draw.rect(screen, (30, 30, 30), self.rect, 2, border_radius=10)

        row_h = 28
        visible_rows = self.rect.height // row_h
        # keep selected in view (basic)
        if self.selected_index < self.scroll:
            self.scroll = self.selected_index
        if self.selected_index >= self.scroll + visible_rows:
            self.scroll = self.selected_index - visible_rows + 1

        y = self.rect.y + 6
        for i in range(self.scroll, min(len(self.items), self.scroll + visible_rows)):
            text = self.items[i]
            color = (20, 20, 20)
            if i == self.selected_index:
                sel_rect = pygame.Rect(self.rect.x + 6, y - 2, self.rect.width - 12, row_h)
                pygame.draw.rect(screen, (220, 235, 255), sel_rect, border_radius=8)
            img = font.render(text, True, color)
            screen.blit(img, (self.rect.x + 12, y))
            y += row_h
