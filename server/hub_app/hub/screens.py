# hub/screens.py
import random
import pygame

from .widgets import Button, InputBox, ListBox
from .deck_store import DeckStore
from .game_engine import GameEngine

WIDTH, HEIGHT = 1000, 650


def normalize_answer(s):
    return " ".join(str(s).lower().strip().split())


class FlashcardQuestionCycler:
    """
    Provides flashcard questions in random order and cycles when exhausted.
    """
    def __init__(self, cards):
        self.cards = cards[:] if cards else []
        self.order = []
        self.pos = 0
        self._reshuffle()

    def _reshuffle(self):
        self.order = list(range(len(self.cards)))
        random.shuffle(self.order)
        self.pos = 0

    def next(self):
        if len(self.cards) == 0:
            return None, None
        if self.pos >= len(self.order):
            self._reshuffle()
        idx = self.order[self.pos]
        self.pos += 1
        c = self.cards[idx]
        return c["front"], c["back"]


class ScreenBase:
    def __init__(self, app):
        self.app = app
        self.next_screen = None

    def handle_event(self, event):
        pass

    def update(self):
        pass

    def draw(self, screen, font, big_font):
        pass


class MainMenuScreen(ScreenBase):
    def __init__(self, app):
        super().__init__(app)
        cx = WIDTH // 2 - 220
        self.buttons = [
            Button(cx, 170, 440, 60, "Start Card Game"),
            Button(cx, 245, 440, 60, "View Decks"),
            Button(cx, 320, 440, 60, "Create New Flashcard Deck"),
            Button(cx, 395, 440, 60, "Multiplayer Mode (Not Implemented)"),
            Button(cx, 470, 440, 60, "Exit"),
        ]
        self.message = ""

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            pos = event.pos
            if self.buttons[0].clicked(pos):
                self.app.engine.start_card_game()     # <-- start session
                self.next_screen = CardGameScreen(self.app)
            elif self.buttons[1].clicked(pos):
                self.next_screen = ViewDecksScreen(self.app)
            elif self.buttons[2].clicked(pos):
                self.next_screen = CreateDeckNameScreen(self.app)
            elif self.buttons[3].clicked(pos):
                self.next_screen = MultiplayerPlaceholderScreen(self.app)
            elif self.buttons[4].clicked(pos):
                self.app.running = False

    def draw(self, screen, font, big_font):
        screen.fill((245, 245, 255))
        title = big_font.render("Hub App: Flashcards + Card Game", True, (20, 20, 40))
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 60))

        sub = font.render("Choose an option:", True, (40, 40, 40))
        screen.blit(sub, (WIDTH // 2 - sub.get_width() // 2, 120))

        mouse = pygame.mouse.get_pos()
        for b in self.buttons:
            b.draw(screen, font, b.rect.collidepoint(mouse))

        deck_id = self.app.store.get_default_flash_deck_id()
        deck = self.app.store.get_deck(deck_id)
        name = deck.get("name", "Unknown") if deck else "Unknown"
        info = font.render(f"Default Card-Game Question Deck: {name}", True, (60, 60, 60))
        screen.blit(info, (WIDTH // 2 - info.get_width() // 2, 545))


class MultiplayerPlaceholderScreen(ScreenBase):
    def __init__(self, app):
        super().__init__(app)
        self.back = Button(40, 580, 160, 50, "Back")

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.back.clicked(event.pos):
                self.next_screen = MainMenuScreen(self.app)

    def draw(self, screen, font, big_font):
        screen.fill((245, 245, 255))
        msg = big_font.render("Multiplayer Mode", True, (20, 20, 40))
        screen.blit(msg, (WIDTH//2 - msg.get_width()//2, 180))
        msg2 = font.render("Not implemented yet. (Placeholder)", True, (60, 60, 60))
        screen.blit(msg2, (WIDTH//2 - msg2.get_width()//2, 240))
        self.back.draw(screen, font, self.back.rect.collidepoint(pygame.mouse.get_pos()))


class ViewDecksScreen(ScreenBase):
    def __init__(self, app):
        super().__init__(app)
        self.list_box = ListBox(40, 150, 920, 280)
        self.refresh_list()

        self.btn_set_default = Button(40, 450, 250, 50, "Set Default for Card Game")
        self.btn_study = Button(310, 450, 250, 50, "Study Deck (Flashcards)")
        self.btn_back = Button(580, 450, 160, 50, "Back")

        self.message = ""

    def refresh_list(self):
        items = []
        items.append("[CARD GAME] Mana Boss Deck (40 cards)")

        default_id = self.app.store.get_default_flash_deck_id()
        for deck_id, name, count in self.app.store.list_flash_decks():
            mark = " (DEFAULT)" if deck_id == default_id else ""
            items.append(f"[FLASH] {name} - {count} cards - id={deck_id}{mark}")

        self.list_box.set_items(items)

    def _selected_flash_deck_id(self):
        item = self.list_box.selected_item()
        if not item:
            return None
        if not item.startswith("[FLASH]"):
            return None
        # parse "id=..."
        key = "id="
        idx = item.find(key)
        if idx == -1:
            return None
        deck_id = item[idx+len(key):].split()[0]
        return deck_id

    def handle_event(self, event):
        self.list_box.handle_event(event)
        if event.type == pygame.MOUSEBUTTONDOWN:
            pos = event.pos

            if self.btn_back.clicked(pos):
                self.next_screen = MainMenuScreen(self.app)
                return

            if self.btn_set_default.clicked(pos):
                deck_id = self._selected_flash_deck_id()
                if deck_id is None:
                    self.message = "Select a FLASH deck to set as default."
                else:
                    self.app.store.set_default_flash_deck(deck_id)
                    self.refresh_list()
                    self.message = "Default deck updated."

            if self.btn_study.clicked(pos):
                deck_id = self._selected_flash_deck_id()
                if deck_id is None:
                    self.message = "Select a FLASH deck to study."
                else:
                    self.app.engine.start_flashcards(deck_id)  # <-- start session
                    self.next_screen = FlashcardsStudyScreen(self.app, deck_id)

    def draw(self, screen, font, big_font):
        screen.fill((245, 245, 255))
        title = big_font.render("View Decks", True, (20, 20, 40))
        screen.blit(title, (40, 60))

        tip = font.render("Arrow keys or click to select. Only FLASH decks can be default / studied.", True, (70, 70, 70))
        screen.blit(tip, (40, 110))

        if self.message:
            m = font.render(self.message, True, (140, 20, 20))
            screen.blit(m, (40, 520))

        self.list_box.draw(screen, font)

        mouse = pygame.mouse.get_pos()
        self.btn_set_default.draw(screen, font, self.btn_set_default.rect.collidepoint(mouse))
        self.btn_study.draw(screen, font, self.btn_study.rect.collidepoint(mouse))
        self.btn_back.draw(screen, font, self.btn_back.rect.collidepoint(mouse))


class CreateDeckNameScreen(ScreenBase):
    def __init__(self, app):
        super().__init__(app)
        self.name_box = InputBox(40, 200, 700, 55, "New deck name...")
        self.create_btn = Button(760, 200, 200, 55, "Create")
        self.back_btn = Button(40, 580, 160, 50, "Back")
        self.message = ""

    def handle_event(self, event):
        self.name_box.handle_event(event)
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.back_btn.clicked(event.pos):
                self.next_screen = MainMenuScreen(self.app)
                return
            if self.create_btn.clicked(event.pos):
                name = self.name_box.text.strip()
                if not name:
                    self.message = "Please enter a deck name."
                else:
                    deck_id = self.app.store.create_deck(name)
                    # Optional: set new deck as default automatically
                    self.app.store.set_default_flash_deck(deck_id)
                    self.next_screen = DeckEditorScreen(self.app, deck_id)

    def draw(self, screen, font, big_font):
        screen.fill((245, 245, 255))
        title = big_font.render("Create New Flashcard Deck", True, (20, 20, 40))
        screen.blit(title, (40, 60))

        info = font.render("Enter a name, then create. You will add cards next.", True, (70, 70, 70))
        screen.blit(info, (40, 120))

        if self.message:
            m = font.render(self.message, True, (140, 20, 20))
            screen.blit(m, (40, 270))

        self.name_box.draw(screen, font)

        mouse = pygame.mouse.get_pos()
        self.create_btn.draw(screen, font, self.create_btn.rect.collidepoint(mouse))
        self.back_btn.draw(screen, font, self.back_btn.rect.collidepoint(mouse))


class DeckEditorScreen(ScreenBase):
    def __init__(self, app, deck_id):
        super().__init__(app)
        self.deck_id = deck_id
        deck = self.app.store.get_deck(deck_id)
        self.deck_name = deck.get("name", "Untitled") if deck else "Untitled"

        self.front = InputBox(40, 170, 920, 55, "Front (question)...")
        self.back = InputBox(40, 250, 920, 55, "Back (answer)...")

        self.add_btn = Button(40, 330, 200, 50, "Add Card")
        self.done_btn = Button(260, 330, 200, 50, "Done")
        self.message = ""

        self.list_box = ListBox(40, 400, 920, 220)
        self.refresh_list()

    def refresh_list(self):
        cards = self.app.store.get_deck_cards(self.deck_id)
        items = []
        for i, c in enumerate(cards):
            q = c["front"].strip()
            a = c["back"].strip()
            if len(q) > 35:
                q = q[:35] + "..."
            if len(a) > 25:
                a = a[:25] + "..."
            items.append(f"{i+1}. Q: {q}  |  A: {a}")
        if len(items) == 0:
            items = ["(No cards yet)"]
        self.list_box.set_items(items)

    def handle_event(self, event):
        self.front.handle_event(event)
        self.back.handle_event(event)

        if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
            # Enter adds if both filled
            f = self.front.text.strip()
            b = self.back.text.strip()
            if f and b:
                self.app.store.add_card(self.deck_id, f, b)
                self.front.text = ""
                self.back.text = ""
                self.message = "Card added."
                self.refresh_list()

        if event.type == pygame.MOUSEBUTTONDOWN:
            pos = event.pos
            if self.add_btn.clicked(pos):
                f = self.front.text.strip()
                b = self.back.text.strip()
                if not f or not b:
                    self.message = "Fill both front and back."
                else:
                    self.app.store.add_card(self.deck_id, f, b)
                    self.front.text = ""
                    self.back.text = ""
                    self.message = "Card added."
                    self.refresh_list()
            elif self.done_btn.clicked(pos):
                self.next_screen = MainMenuScreen(self.app)

    def draw(self, screen, font, big_font):
        screen.fill((245, 245, 255))
        title = big_font.render(f"Edit Deck: {self.deck_name}", True, (20, 20, 40))
        screen.blit(title, (40, 60))

        info = font.render("Add flashcards (these will be used as card-game questions).", True, (70, 70, 70))
        screen.blit(info, (40, 120))

        if self.message:
            m = font.render(self.message, True, (140, 20, 20))
            screen.blit(m, (40, 380))

        self.front.draw(screen, font)
        self.back.draw(screen, font)

        mouse = pygame.mouse.get_pos()
        self.add_btn.draw(screen, font, self.add_btn.rect.collidepoint(mouse))
        self.done_btn.draw(screen, font, self.done_btn.rect.collidepoint(mouse))

        self.list_box.draw(screen, font)


class FlashcardsStudyScreen(ScreenBase):
    """
    Lightweight flashcard study mode (browse + flip + quiz),
    tied to a specific deck_id in DeckStore.
    """
    def __init__(self, app, deck_id):
        super().__init__(app)
        self.deck_id = deck_id
        deck = self.app.store.get_deck(deck_id)
        self.deck_name = deck.get("name", "Untitled") if deck else "Untitled"

        self.mode = "browse"  # browse or quiz or feedback or done
        self.index = 0
        self.show_front = True
        self.message = ""

        self.btn_prev = Button(40, 560, 130, 50, "Prev")
        self.btn_flip = Button(190, 560, 130, 50, "Flip")
        self.btn_next = Button(340, 560, 130, 50, "Next")
        self.btn_quiz = Button(490, 560, 160, 50, "Quiz")
        self.btn_back = Button(670, 560, 160, 50, "Back")

        # quiz
        self.answer = InputBox(40, 470, 920, 55, "Type answer and press Check...")
        self.btn_check = Button(40, 560, 130, 50, "Check")
        self.btn_nextq = Button(190, 560, 130, 50, "Next")
        self.score = 0
        self.q_order = []
        self.q_pos = 0
        self.feedback = None

        self._reload_cards()

    def _reload_cards(self):
        self.cards = self.app.store.get_deck_cards(self.deck_id)
        if self.index >= len(self.cards):
            self.index = max(0, len(self.cards) - 1)
        self.show_front = True

    def _start_quiz(self):
        self._reload_cards()
        if len(self.cards) == 0:
            self.message = "This deck has no cards."
            return
        self.mode = "quiz"
        self.q_order = list(range(len(self.cards)))
        random.shuffle(self.q_order)
        self.q_pos = 0
        self.score = 0
        self.answer.text = ""
        self.feedback = None
        self.message = ""

    def _current_quiz_card(self):
        if self.q_pos >= len(self.q_order):
            return None
        return self.cards[self.q_order[self.q_pos]]

    def handle_event(self, event):
        if self.mode in ("quiz", "feedback"):
            self.answer.handle_event(event)

        if event.type == pygame.MOUSEBUTTONDOWN:
            pos = event.pos

            if self.mode == "browse":
                if self.btn_back.clicked(pos):
                    self.next_screen = ViewDecksScreen(self.app)
                    return
                if self.btn_prev.clicked(pos) and len(self.cards) > 0:
                    self.index = (self.index - 1) % len(self.cards)
                    self.show_front = True
                if self.btn_next.clicked(pos) and len(self.cards) > 0:
                    self.index = (self.index + 1) % len(self.cards)
                    self.show_front = True
                if self.btn_flip.clicked(pos) and len(self.cards) > 0:
                    self.show_front = not self.show_front
                if self.btn_quiz.clicked(pos):
                    self._start_quiz()

            elif self.mode == "quiz":
                if self.btn_back.clicked(pos):
                    self.mode = "browse"
                    self.message = ""
                    return
                if self.btn_check.clicked(pos):
                    card = self._current_quiz_card()
                    if card is None:
                        self.mode = "done"
                        return
                    user = self.answer.text
                    ok = normalize_answer(user) == normalize_answer(card["back"])
                    if ok:
                        self.score += 1
                    self.feedback = {"ok": ok, "correct": card["back"], "user": user}
                    self.mode = "feedback"

            elif self.mode == "feedback":
                if self.btn_back.clicked(pos):
                    self.mode = "browse"
                    self.message = ""
                    return
                if self.btn_nextq.clicked(pos):
                    self.q_pos += 1
                    self.answer.text = ""
                    self.feedback = None
                    if self.q_pos >= len(self.q_order):
                        self.mode = "done"
                    else:
                        self.mode = "quiz"

            elif self.mode == "done":
                if self.btn_back.clicked(pos):
                    self.mode = "browse"
                    self.message = ""
                    return

    def draw(self, screen, font, big_font):
        screen.fill((245, 245, 255))
        title = big_font.render(f"Study: {self.deck_name}", True, (20, 20, 40))
        screen.blit(title, (40, 50))

        self._reload_cards()

        card_rect = pygame.Rect(40, 120, 920, 320)
        pygame.draw.rect(screen, (255, 255, 255), card_rect, border_radius=14)
        pygame.draw.rect(screen, (30, 30, 30), card_rect, 2, border_radius=14)

        if len(self.cards) == 0:
            empty = big_font.render("No cards in this deck.", True, (120, 120, 120))
            screen.blit(empty, (card_rect.centerx - empty.get_width() // 2,
                                card_rect.centery - empty.get_height() // 2))
        else:
            if self.mode == "browse":
                header = font.render(f"{self.index+1}/{len(self.cards)}  ({'Front' if self.show_front else 'Back'})", True, (60, 60, 60))
                screen.blit(header, (card_rect.x + 15, card_rect.y + 15))
                text = self.cards[self.index]["front"] if self.show_front else self.cards[self.index]["back"]
                self._draw_wrapped(screen, big_font, (20, 20, 20), text, card_rect.inflate(-40, -80))

            elif self.mode in ("quiz", "feedback", "done"):
                header = font.render(f"Quiz {min(self.q_pos+1, len(self.q_order))}/{len(self.q_order)}  Score: {self.score}", True, (60, 60, 60))
                screen.blit(header, (card_rect.x + 15, card_rect.y + 15))

                if self.mode == "done":
                    done = big_font.render(f"Finished! Final score: {self.score}/{len(self.q_order)}", True, (20, 20, 20))
                    screen.blit(done, (card_rect.centerx - done.get_width()//2, card_rect.centery - 20))
                else:
                    card = self._current_quiz_card()
                    q = card["front"] if card else ""
                    self._draw_wrapped(screen, big_font, (20, 20, 20), q, card_rect.inflate(-40, -80))

        if self.message:
            m = font.render(self.message, True, (140, 20, 20))
            screen.blit(m, (40, 455))

        mouse = pygame.mouse.get_pos()

        if self.mode == "browse":
            self.btn_prev.draw(screen, font, self.btn_prev.rect.collidepoint(mouse))
            self.btn_flip.draw(screen, font, self.btn_flip.rect.collidepoint(mouse))
            self.btn_next.draw(screen, font, self.btn_next.rect.collidepoint(mouse))
            self.btn_quiz.draw(screen, font, self.btn_quiz.rect.collidepoint(mouse))
            self.btn_back.draw(screen, font, self.btn_back.rect.collidepoint(mouse))

        elif self.mode == "quiz":
            self.answer.draw(screen, font)
            self.btn_check.draw(screen, font, self.btn_check.rect.collidepoint(mouse))
            self.btn_back.draw(screen, font, self.btn_back.rect.collidepoint(mouse))

        elif self.mode == "feedback":
            fb = self.feedback
            status = "Correct!" if fb and fb["ok"] else "Not quite."
            color = (20, 120, 20) if fb and fb["ok"] else (170, 40, 40)
            img = big_font.render(status, True, color)
            screen.blit(img, (40, 455))

            if fb:
                screen.blit(font.render("Your: " + (fb["user"].strip() or "(blank)"), True, (20, 20, 20)), (40, 500))
                screen.blit(font.render("Answer: " + fb["correct"], True, (20, 20, 20)), (40, 525))

            self.btn_nextq.draw(screen, font, self.btn_nextq.rect.collidepoint(mouse))
            self.btn_back.draw(screen, font, self.btn_back.rect.collidepoint(mouse))

        elif self.mode == "done":
            self.btn_back.draw(screen, font, self.btn_back.rect.collidepoint(mouse))

    def _draw_wrapped(self, screen, font, color, text, rect):
        words = str(text).split(" ")
        lines = []
        cur = ""
        for w in words:
            test = (cur + " " + w).strip()
            if font.size(test)[0] <= rect.width:
                cur = test
            else:
                if cur:
                    lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)

        y = rect.top
        for line in lines:
            img = font.render(line, True, color)
            screen.blit(img, (rect.left, y))
            y += img.get_height() + 6
            if y > rect.bottom:
                break


import os
import pygame

class CardGameScreen(ScreenBase):
    def __init__(self, app):
        super().__init__(app)

        # session is created by: self.app.engine.start_card_game()
        self.session = self.app.engine.session
        self.answer_box = InputBox(40, 270, 520, 50, "Type answer, press Enter")
        self.end_turn_btn = Button(820, 560, 140, 50, "End Turn")
        self.back_btn = Button(40, 560, 160, 50, "Main Menu")

        self.message = "Answer 3 flashcard questions to gain mana (+3 each correct)."

        # Boss sprite (robust path)
        self.boss_sprite = None
        try:
            hub_dir = os.path.dirname(os.path.dirname(__file__))  # .../hub_app
            img_path = os.path.join(hub_dir, "assets", "boss.png")
            self.boss_sprite = pygame.image.load(img_path).convert_alpha()
            self.boss_sprite = pygame.transform.smoothscale(self.boss_sprite, (260, 260))
        except:
            self.boss_sprite = None

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.back_btn.clicked(event.pos):
                self.app.engine.go_to_menu()
                self.next_screen = MainMenuScreen(self.app)
                return

        state = self.session.get_state()
        phase = state["phase"]

        if phase == "game_over":
            if event.type == pygame.MOUSEBUTTONDOWN and self.back_btn.clicked(event.pos):
                self.app.engine.go_to_menu()
                self.next_screen = MainMenuScreen(self.app)
            return

        if phase == "questions":
            self.answer_box.handle_event(event)
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                user_text = self.answer_box.text
                ok, msg = self.session.submit_mana_answer(user_text)
                self.message = msg
                self.answer_box.text = ""

        elif phase == "play":
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.end_turn_btn.clicked(event.pos):
                    self.message = self.session.end_turn()
                    return

                idx = self._hand_index_at_pos(event.pos)
                if idx is not None:
                    success, msg = self.session.play_card(idx)
                    self.message = msg

    def _hand_index_at_pos(self, pos):
        x0, y0 = 40, 430
        w, h = 180, 90
        gap = 12
        hand = self.session.engine.player.hand
        for i in range(len(hand)):
            r = pygame.Rect(x0 + i * (w + gap), y0, w, h)
            if r.collidepoint(pos):
                return i
        return None

    def draw(self, screen, font, big_font):
        screen.fill((245, 245, 255))

        e = self.session.engine
        state = self.session.get_state()
        phase = state["phase"]

        title = big_font.render("Mana Boss Card Game", True, (20, 20, 40))
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 15))

        self._draw_hp_bar(screen, 40, 70, 420, 24, e.player.hp, e.player.max_hp, "Player", font)
        self._draw_hp_bar(screen, 540, 70, 420, 24, e.boss.hp, e.boss.max_hp, "Boss", font)

        if self.boss_sprite:
            screen.blit(self.boss_sprite, (WIDTH // 2 - self.boss_sprite.get_width() // 2, 135))
        else:
            r = pygame.Rect(WIDTH // 2 - 120, 150, 240, 220)
            pygame.draw.rect(screen, (210, 210, 210), r, border_radius=14)
            pygame.draw.rect(screen, (30, 30, 30), r, 2, border_radius=14)
            t = font.render("boss sprite missing", True, (60, 60, 60))
            screen.blit(t, (r.centerx - t.get_width() // 2, r.centery - 10))

        info = font.render(
            f"Turn: {e.turn_number}   Mana: {e.player.mana}   Boss resists: {e.boss.resistant_to}",
            True, (30, 30, 30)
        )
        screen.blit(info, (40, 110))

        shields = e.player.shields
        shield_text = f"Shields: Fire[{shields['fire']}]  Water[{shields['water']}]  Ice[{shields['ice']}]"
        screen.blit(font.render(shield_text, True, (40, 40, 40)), (40, 140))

        if self.message:
            screen.blit(font.render(self.message, True, (120, 20, 20)), (40, 185))

        if phase == "questions":
            screen.blit(big_font.render("Mana Questions (Flashcards)", True, (20, 20, 40)), (40, 215))
            qline = f"({state['questions_left']} left)  {state['current_question']}"
            screen.blit(font.render(qline, True, (20, 20, 20)), (40, 245))
            self.answer_box.draw(screen, font)

        elif phase == "play":
            screen.blit(big_font.render("Your Hand (click to play)", True, (20, 20, 40)), (40, 385))
            self._draw_hand(screen, font)
            mouse = pygame.mouse.get_pos()
            self.end_turn_btn.draw(screen, font, self.end_turn_btn.rect.collidepoint(mouse))
            self.back_btn.draw(screen, font, self.back_btn.rect.collidepoint(mouse))

        self._draw_log(screen, font)

        if e.game_over:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 130))
            screen.blit(overlay, (0, 0))
            winner = "YOU WIN!" if e.winner == "player" else "YOU LOSE!"
            msg = big_font.render(winner, True, (255, 255, 255))
            screen.blit(msg, (WIDTH // 2 - msg.get_width() // 2, HEIGHT // 2 - 40))
            mouse = pygame.mouse.get_pos()
            self.back_btn.draw(screen, font, self.back_btn.rect.collidepoint(mouse))

    # keep your existing helper methods:
    def _draw_hp_bar(self, screen, x, y, w, h, current, max_hp, label, font):
        pygame.draw.rect(screen, (30, 30, 30), (x, y, w, h), 2, border_radius=8)
        fill_w = int(w * (current / max_hp)) if max_hp > 0 else 0
        pygame.draw.rect(screen, (180, 60, 60), (x, y, fill_w, h), border_radius=8)
        text = font.render(f"{label}: {current}/{max_hp}", True, (20, 20, 20))
        screen.blit(text, (x, y - 24))

    def _draw_hand(self, screen, font):
        x0, y0 = 40, 430
        w, h = 180, 90
        gap = 12
        hand = self.session.engine.player.hand

        for i, card in enumerate(hand):
            r = pygame.Rect(x0 + i * (w + gap), y0, w, h)
            pygame.draw.rect(screen, (255, 255, 255), r, border_radius=10)
            pygame.draw.rect(screen, (30, 30, 30), r, 2, border_radius=10)
            screen.blit(font.render(card.to_short_text(), True, (20, 20, 20)), (r.x + 10, r.y + 10))
            screen.blit(font.render(f"Cost: {card.cost}", True, (80, 80, 80)), (r.x + 10, r.y + 38))
            screen.blit(font.render(card.card_type, True, (80, 80, 80)), (r.x + 10, r.y + 62))

    def _draw_log(self, screen, font):
        box = pygame.Rect(40, 535, 740, 90)
        pygame.draw.rect(screen, (255, 255, 255), box, border_radius=10)
        pygame.draw.rect(screen, (30, 30, 30), box, 2, border_radius=10)
        y = box.y + 8
        for line in self.session.engine.log_lines[-4:]:
            screen.blit(font.render(line, True, (25, 25, 25)), (box.x + 10, y))
            y += 20
