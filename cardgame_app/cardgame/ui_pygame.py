# cardgame/ui_pygame.py
import pygame
from .questions import QuestionManager

WIDTH, HEIGHT = 1000, 650

class Button:
    def __init__(self, x, y, w, h, text):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text

    def draw(self, screen, font, hover):
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
                if len(self.text) < 60:
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


def draw_hp_bar(screen, x, y, w, h, current, max_hp, label, font):
    pygame.draw.rect(screen, (30, 30, 30), (x, y, w, h), 2, border_radius=8)
    fill_w = int(w * (current / max_hp)) if max_hp > 0 else 0
    pygame.draw.rect(screen, (180, 60, 60), (x, y, fill_w, h), border_radius=8)

    text = font.render(f"{label}: {current}/{max_hp}", True, (20, 20, 20))
    screen.blit(text, (x, y - 24))


class ManaBossCardGameUI:
    """
    Pygame UI wrapper.
    Calls engine methods and displays everything.
    """

    def __init__(self, engine):
        self.engine = engine

        self.phase = "questions"  # "questions", "play", "game_over"
        self.questions = QuestionManager()
        self.answer_box = InputBox(40, 270, 520, 50, "Type answer, press Enter")

        self.end_turn_btn = Button(820, 560, 140, 50, "End Turn")

        self.message = "Answer 3 questions to gain mana (+3 each correct)."
        self.engine.start_new_turn()

    def handle_event(self, event):
        if self.phase == "game_over":
            return

        mouse_pos = pygame.mouse.get_pos()

        if self.phase == "questions":
            self.answer_box.handle_event(event)

            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                ok = self.questions.submit(self.answer_box.text)
                self.answer_box.text = ""
                if ok:
                    self.engine.grant_mana_for_correct_answer()
                else:
                    self.engine.player.mana += 0  # explicit (no mana)
                    self.engine._log("Wrong. +0 mana.")

                if self.questions.is_done():
                    self.phase = "play"
                    self.message = "Play cards (each costs 5 mana). Then End Turn."

        elif self.phase == "play":
            if event.type == pygame.MOUSEBUTTONDOWN:
                # End turn?
                if self.end_turn_btn.clicked(event.pos):
                    self.engine.end_player_turn_and_boss_acts()
                    if self.engine.game_over:
                        self.phase = "game_over"
                        return
                    # New turn begins
                    self.questions = QuestionManager()
                    self.phase = "questions"
                    self.message = "Answer 3 questions to gain mana (+3 each correct)."
                    self.engine.start_new_turn()
                    return

                # Click a card in hand?
                idx = self._hand_index_at_pos(mouse_pos)
                if idx is not None:
                    success, msg = self.engine.play_card_from_hand(idx)
                    self.message = msg
                    if self.engine.game_over:
                        self.phase = "game_over"

    def _hand_index_at_pos(self, pos):
        # Hand cards drawn as rectangles in a row
        x0, y0 = 40, 430
        w, h = 180, 90
        gap = 12

        for i in range(len(self.engine.player.hand)):
            r = pygame.Rect(x0 + i * (w + gap), y0, w, h)
            if r.collidepoint(pos):
                return i
        return None

    def draw(self, screen, font, big_font):
        mouse_pos = pygame.mouse.get_pos()
        screen.fill((245, 245, 255))

        # HP bars
        draw_hp_bar(screen, 40, 70, 420, 24, self.engine.player.hp, self.engine.player.max_hp, "Player", font)
        draw_hp_bar(screen, 540, 70, 420, 24, self.engine.boss.hp, self.engine.boss.max_hp, "Boss", font)

        # Top info
        title = big_font.render("Mana Boss Card Game", True, (20, 20, 40))
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 15))

        info = font.render(
            f"Turn: {self.engine.turn_number}   Mana: {self.engine.player.mana}   Boss resists: {self.engine.boss.resistant_to}",
            True, (30, 30, 30)
        )
        screen.blit(info, (40, 110))

        # Shields status
        shields = self.engine.player.shields
        shield_text = f"Shields: Fire[{shields['fire']}]  Water[{shields['water']}]  Ice[{shields['ice']}]"
        screen.blit(font.render(shield_text, True, (40, 40, 40)), (40, 140))

        # Message line
        if self.message:
            screen.blit(font.render(self.message, True, (120, 20, 20)), (40, 185))

        # Phase content
        if self.phase == "questions":
            q = self.questions.current_question
            screen.blit(big_font.render("Mana Questions", True, (20, 20, 40)), (40, 215))
            screen.blit(font.render(q, True, (20, 20, 20)), (40, 245))
            self.answer_box.draw(screen, font)

            hint = font.render("Tip: click the input box first, then type.", True, (90, 90, 90))
            screen.blit(hint, (40, 330))

        elif self.phase == "play":
            screen.blit(big_font.render("Your Hand (click to play)", True, (20, 20, 40)), (40, 385))
            self._draw_hand(screen, font)

            self.end_turn_btn.draw(screen, font, self.end_turn_btn.rect.collidepoint(mouse_pos))

        # Log window
        self._draw_log(screen, font)

        # Game over overlay
        if self.engine.game_over:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 130))
            screen.blit(overlay, (0, 0))

            winner = "YOU WIN!" if self.engine.winner == "player" else "YOU LOSE!"
            msg = big_font.render(winner, True, (255, 255, 255))
            screen.blit(msg, (WIDTH // 2 - msg.get_width() // 2, HEIGHT // 2 - 40))

            sub = font.render("Close the window to exit.", True, (255, 255, 255))
            screen.blit(sub, (WIDTH // 2 - sub.get_width() // 2, HEIGHT // 2 + 10))

    def _draw_hand(self, screen, font):
        x0, y0 = 40, 430
        w, h = 180, 90
        gap = 12

        for i, card in enumerate(self.engine.player.hand):
            r = pygame.Rect(x0 + i * (w + gap), y0, w, h)
            pygame.draw.rect(screen, (255, 255, 255), r, border_radius=10)
            pygame.draw.rect(screen, (30, 30, 30), r, 2, border_radius=10)

            line1 = font.render(card.to_short_text(), True, (20, 20, 20))
            screen.blit(line1, (r.x + 10, r.y + 10))

            line2 = font.render(f"Cost: {card.cost}", True, (80, 80, 80))
            screen.blit(line2, (r.x + 10, r.y + 38))

            line3 = font.render(card.card_type, True, (80, 80, 80))
            screen.blit(line3, (r.x + 10, r.y + 62))

        if len(self.engine.player.hand) == 0:
            screen.blit(font.render("(Empty hand)", True, (80, 80, 80)), (40, 455))

    def _draw_log(self, screen, font):
        box = pygame.Rect(40, 535, 740, 90)
        pygame.draw.rect(screen, (255, 255, 255), box, border_radius=10)
        pygame.draw.rect(screen, (30, 30, 30), box, 2, border_radius=10)

        y = box.y + 8
        for line in self.engine.log_lines[-4:]:
            img = font.render(line, True, (25, 25, 25))
            screen.blit(img, (box.x + 10, y))
            y += 20
