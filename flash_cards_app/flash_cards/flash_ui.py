import pygame


class Button:
    def __init__(self, x, y, w, h, text):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text

    def draw(self, screen, font, hover):
        border = (30, 30, 30)
        fill = (220, 220, 220) if not hover else (200, 200, 200)
        pygame.draw.rect(screen, fill, self.rect, border_radius=8)
        pygame.draw.rect(screen, border, self.rect, 2, border_radius=8)

        label = font.render(self.text, True, (20, 20, 20))
        screen.blit(label, (self.rect.centerx - label.get_width() // 2,
                            self.rect.centery - label.get_height() // 2))

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
            else:
                if len(self.text) < 400:
                    self.text += event.unicode

    def draw(self, screen, font):
        border = (50, 50, 50)
        fill = (255, 255, 255) if self.active else (245, 245, 245)
        pygame.draw.rect(screen, fill, self.rect, border_radius=8)
        pygame.draw.rect(screen, border, self.rect, 2, border_radius=8)

        if self.text.strip():
            img = font.render(self.text, True, (20, 20, 20))
            screen.blit(img, (self.rect.x + 10, self.rect.y + 10))
        else:
            img = font.render(self.placeholder, True, (140, 140, 140))
            screen.blit(img, (self.rect.x + 10, self.rect.y + 10))


class FlashcardsPygameApp:
    def __init__(self, service, width=900, height=600):
        self.service = service
        self.W, self.H = width, height

        self.mode = "menu"
        self.message = ""

        self.cards = self.service.get_all_cards()
        self.browse_index = 0
        self.show_front = True

        self.quiz_state = None
        self.quiz_feedback = None

        # UI elements (positions kept simple)
        self.front_box = InputBox(60, 140, 780, 60, "Front (question/term)")
        self.back_box = InputBox(60, 230, 780, 60, "Back (answer/definition)")
        self.answer_box = InputBox(60, 420, 780, 60, "Type answer...")

        self.btn_create = Button(320, 220, 260, 60, "Create Cards")
        self.btn_browse = Button(320, 300, 260, 60, "Browse Cards")
        self.btn_quiz = Button(320, 380, 260, 60, "Quiz Mode")

        self.btn_add = Button(60, 320, 160, 50, "Add Card")
        self.btn_menu = Button(240, 320, 160, 50, "Menu")

        self.btn_prev = Button(60, 500, 120, 50, "Prev")
        self.btn_flip = Button(200, 500, 120, 50, "Flip")
        self.btn_next = Button(340, 500, 120, 50, "Next")
        self.btn_delete = Button(480, 500, 160, 50, "Delete")
        self.btn_menu2 = Button(660, 500, 180, 50, "Menu")

        self.btn_check = Button(60, 500, 160, 50, "Check")
        self.btn_next_q = Button(240, 500, 160, 50, "Next")
        self.btn_menu3 = Button(420, 500, 160, 50, "Menu")

    def _refresh_cards(self):
        self.cards = self.service.get_all_cards()
        if self.browse_index >= len(self.cards):
            self.browse_index = max(0, len(self.cards) - 1)

    def handle_event(self, event):
        if self.mode == "create":
            self.front_box.handle_event(event)
            self.back_box.handle_event(event)
        elif self.mode == "quiz":
            self.answer_box.handle_event(event)

        if event.type == pygame.MOUSEBUTTONDOWN:
            pos = event.pos

            if self.mode == "menu":
                if self.btn_create.clicked(pos):
                    self.mode = "create"
                    self.message = ""
                elif self.btn_browse.clicked(pos):
                    self._refresh_cards()
                    self.mode = "browse"
                    self.message = ""
                elif self.btn_quiz.clicked(pos):
                    self._refresh_cards()
                    if len(self.cards) == 0:
                        self.message = "Need at least 1 card."
                    else:
                        self.quiz_state = self.service.start_quiz(self.cards)
                        self.answer_box.text = ""
                        self.quiz_feedback = None
                        self.mode = "quiz"

            elif self.mode == "create":
                if self.btn_add.clicked(pos):
                    front = self.front_box.text.strip()
                    back = self.back_box.text.strip()
                    if front and back:
                        self.service.add_card(front, back)
                        self.front_box.text = ""
                        self.back_box.text = ""
                        self.message = "Added."
                        self._refresh_cards()
                    else:
                        self.message = "Fill front and back."
                elif self.btn_menu.clicked(pos):
                    self.mode = "menu"
                    self.message = ""

            elif self.mode == "browse":
                if self.btn_menu2.clicked(pos):
                    self.mode = "menu"
                    self.message = ""
                elif len(self.cards) > 0:
                    if self.btn_prev.clicked(pos):
                        self.browse_index = (self.browse_index - 1) % len(self.cards)
                        self.show_front = True
                    elif self.btn_next.clicked(pos):
                        self.browse_index = (self.browse_index + 1) % len(self.cards)
                        self.show_front = True
                    elif self.btn_flip.clicked(pos):
                        self.show_front = not self.show_front
                    elif self.btn_delete.clicked(pos):
                        card = self.cards[self.browse_index]
                        self.service.delete_card(card.id)
                        self.message = "Deleted."
                        self._refresh_cards()
                        self.show_front = True

            elif self.mode == "quiz":
                if self.btn_menu3.clicked(pos):
                    self.mode = "menu"
                    self.message = ""
                elif self.btn_check.clicked(pos):
                    card = self.service.quiz_current_card(self.cards, self.quiz_state)
                    if card is None:
                        self.mode = "menu"
                        return

                    user = self.answer_box.text
                    ok = self.service.quiz_check_answer(card.back, user)
                    if ok:
                        self.quiz_state["score"] += 1

                    self.quiz_feedback = {
                        "correct": ok,
                        "your": user,
                        "answer": card.back,
                    }
                    self.mode = "quiz_feedback"

            elif self.mode == "quiz_feedback":
                if self.btn_menu3.clicked(pos):
                    self.mode = "menu"
                    self.message = ""
                elif self.btn_next_q.clicked(pos):
                    self.quiz_state["pos"] += 1
                    self.answer_box.text = ""
                    self.quiz_feedback = None
                    if self.quiz_state["pos"] >= len(self.quiz_state["order"]):
                        self.mode = "quiz_done"
                    else:
                        self.mode = "quiz"

            elif self.mode == "quiz_done":
                if self.btn_menu3.clicked(pos):
                    self.mode = "menu"
                    self.message = ""

    def draw(self, screen, font, big_font):
        mouse_pos = pygame.mouse.get_pos()
        screen.fill((245, 245, 255))

        title = big_font.render("Flashcards", True, (20, 20, 40))
        screen.blit(title, (self.W // 2 - title.get_width() // 2, 30))

        if self.message:
            msg = font.render(self.message, True, (140, 20, 20))
            screen.blit(msg, (60, 90))

        if self.mode == "menu":
            info = font.render(f"Cards: {len(self.cards)}", True, (30, 30, 30))
            screen.blit(info, (60, 130))

            for b in [self.btn_create, self.btn_browse, self.btn_quiz]:
                b.draw(screen, font, b.rect.collidepoint(mouse_pos))

        elif self.mode == "create":
            self.front_box.draw(screen, font)
            self.back_box.draw(screen, font)
            self.btn_add.draw(screen, font, self.btn_add.rect.collidepoint(mouse_pos))
            self.btn_menu.draw(screen, font, self.btn_menu.rect.collidepoint(mouse_pos))

        elif self.mode == "browse":
            self._refresh_cards()

            card_rect = pygame.Rect(60, 150, 780, 320)
            pygame.draw.rect(screen, (255, 255, 255), card_rect, border_radius=14)
            pygame.draw.rect(screen, (30, 30, 30), card_rect, 2, border_radius=14)

            if len(self.cards) == 0:
                empty = big_font.render("No cards yet.", True, (120, 120, 120))
                screen.blit(empty, (card_rect.centerx - empty.get_width() // 2,
                                    card_rect.centery - empty.get_height() // 2))
            else:
                card = self.cards[self.browse_index]
                header = font.render(f"Card {self.browse_index+1}/{len(self.cards)}", True, (60, 60, 60))
                screen.blit(header, (card_rect.x + 15, card_rect.y + 15))

                text = card.front if self.show_front else card.back
                content = big_font.render(text[:40] + ("..." if len(text) > 40 else ""), True, (20, 20, 20))
                screen.blit(content, (card_rect.x + 20, card_rect.y + 90))

            for b in [self.btn_prev, self.btn_flip, self.btn_next, self.btn_delete, self.btn_menu2]:
                b.draw(screen, font, b.rect.collidepoint(mouse_pos))

        elif self.mode == "quiz":
            card = self.service.quiz_current_card(self.cards, self.quiz_state)
            if card is None:
                self.mode = "quiz_done"
                return

            header = font.render(
                f"Q {self.quiz_state['pos']+1}/{len(self.quiz_state['order'])}   Score: {self.quiz_state['score']}",
                True, (50, 50, 50)
            )
            screen.blit(header, (60, 120))

            q = big_font.render(card.front[:45] + ("..." if len(card.front) > 45 else ""), True, (20, 20, 20))
            screen.blit(q, (60, 200))

            self.answer_box.draw(screen, font)
            self.btn_check.draw(screen, font, self.btn_check.rect.collidepoint(mouse_pos))
            self.btn_menu3.draw(screen, font, self.btn_menu3.rect.collidepoint(mouse_pos))

        elif self.mode == "quiz_feedback":
            fb = self.quiz_feedback
            status = "Correct!" if fb["correct"] else "Not quite."
            color = (20, 120, 20) if fb["correct"] else (170, 40, 40)
            screen.blit(big_font.render(status, True, color), (60, 160))

            screen.blit(font.render("Your: " + (fb["your"] if fb["your"].strip() else "(blank)"), True, (20, 20, 20)), (60, 240))
            screen.blit(font.render("Answer: " + fb["answer"], True, (20, 20, 20)), (60, 280))

            self.btn_next_q.draw(screen, font, self.btn_next_q.rect.collidepoint(mouse_pos))
            self.btn_menu3.draw(screen, font, self.btn_menu3.rect.collidepoint(mouse_pos))

        elif self.mode == "quiz_done":
            done = big_font.render(
                f"Final Score: {self.quiz_state['score']} / {len(self.quiz_state['order'])}",
                True, (20, 20, 20)
            )
            screen.blit(done, (60, 200))
            self.btn_menu3.draw(screen, font, self.btn_menu3.rect.collidepoint(mouse_pos))
