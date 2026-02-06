# hub/engine.py
# A simple "headless" engine/controller for the whole Hub App.
# - No pygame imports.
# - Keeps the combined state for:
#     * Menu mode
#     * Flashcards study/quiz mode
#     * Card game mode (uses cardgame_app.cardgame.engine.GameEngine)
# - Designed so your pygame screens call methods here rather than owning game logic.

import random

from .deck_store import DeckStore
from .game_engine import GameEngine


def normalize_answer(s):
    return " ".join(str(s).lower().strip().split())


class FlashcardQuestionCycler:
    """
    Provides flashcard questions in random order and cycles when exhausted.
    cards: list of dicts like {"front": "...", "back": "..."}
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


class CardGameSession:
    """
    Manages one run of the card game + flashcard questions for mana.
    The pygame UI should:
      - read state via get_state()
      - call submit_mana_answer()
      - call play_card()
      - call end_turn()
    """
    def __init__(self, flashcard_cards):
        self.engine = GameEngine()

        # Questions for mana
        self.qcycler = FlashcardQuestionCycler(flashcard_cards)
        self.phase = "questions"  # "questions" | "play" | "game_over"

        self.questions_left = 3
        self.current_q, self.current_a = self.qcycler.next()

        self.message = "Answer 3 questions to gain mana (+3 each correct)."

        # Start turn 1 in the underlying engine
        self.engine.start_new_turn()

    def get_state(self):
        return {
            "mode": "card_game",
            "phase": self.phase,
            "turn": self.engine.turn_number,
            "player_hp": self.engine.player.hp,
            "player_max_hp": self.engine.player.max_hp,
            "player_mana": self.engine.player.mana,
            "boss_hp": self.engine.boss.hp,
            "boss_max_hp": self.engine.boss.max_hp,
            "boss_resists": self.engine.boss.resistant_to,
            "shields": dict(self.engine.player.shields),
            "hand": [c.to_short_text() for c in self.engine.player.hand],
            "questions_left": self.questions_left,
            "current_question": self.current_q,
            "message": self.message,
            "log": list(self.engine.log_lines),
            "game_over": bool(self.engine.game_over),
            "winner": self.engine.winner,
        }

    def submit_mana_answer(self, user_text):
        """
        Use when phase == "questions".
        Returns (ok, message).
        """
        if self.phase != "questions":
            return False, "Not in question phase."

        if self.current_q is None:
            # no questions available (empty deck)
            self.questions_left -= 1
            if self.questions_left <= 0:
                self.phase = "play"
                self.message = "No questions available. You may play cards."
                return False, self.message
            return False, "No questions available."

        ok = normalize_answer(user_text) == normalize_answer(self.current_a)

        if ok:
            self.engine.grant_mana_for_correct_answer()
            self.message = "Correct! +3 mana."
        else:
            self.engine._log("Wrong. +0 mana.")
            self.message = "Wrong. +0 mana."

        self.questions_left -= 1

        if self.questions_left <= 0:
            self.phase = "play"
            self.message += " Now you can play cards (each costs 5)."
            return ok, self.message

        # next question
        self.current_q, self.current_a = self.qcycler.next()
        return ok, self.message

    def play_card(self, hand_index):
        """
        Use when phase == "play".
        Returns (success, message).
        """
        if self.phase != "play":
            return False, "Answer questions first."

        success, msg = self.engine.play_card_from_hand(hand_index)
        self.message = msg

        if self.engine.game_over:
            self.phase = "game_over"

        return success, msg

    def end_turn(self):
        """
        Ends the player's turn, lets boss act, then starts a new turn.
        Returns message string.
        """
        if self.phase != "play":
            return "You can only end the turn during play phase."

        self.engine.end_player_turn_and_boss_acts()

        if self.engine.game_over:
            self.phase = "game_over"
            self.message = "Game over."
            return self.message

        # New turn
        self.engine.start_new_turn()
        self.phase = "questions"
        self.questions_left = 3
        self.current_q, self.current_a = self.qcycler.next()
        self.message = "New turn: answer 3 questions to gain mana."
        return self.message


class FlashcardsSession:
    """
    A simple flashcards mode for one deck.
    Supports browse + quiz.
    Pygame UI can call:
      - next_card(), prev_card(), flip()
      - start_quiz(), submit_quiz_answer(), next_quiz_question()
      - read get_state()
    """
    def __init__(self, cards):
        self.cards = cards[:] if cards else []

        self.mode = "browse"  # "browse" | "quiz" | "feedback" | "done"
        self.index = 0
        self.show_front = True

        # quiz state
        self.q_order = []
        self.q_pos = 0
        self.score = 0
        self.feedback = None

    def _current_browse_card(self):
        if len(self.cards) == 0:
            return None
        return self.cards[self.index]

    def _current_quiz_card(self):
        if self.q_pos >= len(self.q_order):
            return None
        return self.cards[self.q_order[self.q_pos]]

    def get_state(self):
        state = {
            "mode": "flashcards",
            "submode": self.mode,
            "count": len(self.cards),
            "index": self.index,
            "show_front": self.show_front,
            "score": self.score,
            "q_pos": self.q_pos,
            "feedback": self.feedback,
        }

        if len(self.cards) == 0:
            state["text"] = None
            return state

        if self.mode == "browse":
            c = self._current_browse_card()
            state["text"] = c["front"] if self.show_front else c["back"]
        elif self.mode in ("quiz", "feedback"):
            c = self._current_quiz_card()
            state["text"] = c["front"] if c else None
        else:
            state["text"] = None

        return state

    def next_card(self):
        if len(self.cards) == 0:
            return
        self.index = (self.index + 1) % len(self.cards)
        self.show_front = True

    def prev_card(self):
        if len(self.cards) == 0:
            return
        self.index = (self.index - 1) % len(self.cards)
        self.show_front = True

    def flip(self):
        if len(self.cards) == 0:
            return
        self.show_front = not self.show_front

    def start_quiz(self):
        if len(self.cards) == 0:
            return False
        self.mode = "quiz"
        self.q_order = list(range(len(self.cards)))
        random.shuffle(self.q_order)
        self.q_pos = 0
        self.score = 0
        self.feedback = None
        return True

    def submit_quiz_answer(self, user_text):
        if self.mode != "quiz":
            return False, "Not in quiz mode."

        c = self._current_quiz_card()
        if c is None:
            self.mode = "done"
            return False, "Quiz finished."

        ok = normalize_answer(user_text) == normalize_answer(c["back"])
        if ok:
            self.score += 1

        self.feedback = {"ok": ok, "correct": c["back"], "user": user_text}
        self.mode = "feedback"
        return ok, "Correct!" if ok else "Not quite."

    def next_quiz_question(self):
        if self.mode != "feedback":
            return

        self.q_pos += 1
        self.feedback = None

        if self.q_pos >= len(self.q_order):
            self.mode = "done"
        else:
            self.mode = "quiz"


class HubEngine:
    """
    The main engine/controller for the whole app.
    Your pygame App object should create ONE HubEngine and share it across screens.
    """
    def __init__(self, deck_store_path="decks.json"):
        self.store = DeckStore(deck_store_path)
        self.mode = "menu"     # "menu" | "card_game" | "flashcards" | "multiplayer"
        self.session = None    # CardGameSession or FlashcardsSession
        self.message = ""

    # ---------- Menu / Mode switching ----------

    def go_to_menu(self):
        self.mode = "menu"
        self.session = None
        self.message = ""

    def start_multiplayer_placeholder(self):
        self.mode = "multiplayer"
        self.session = None
        self.message = "Multiplayer is not implemented yet."

    # ---------- Deck helpers ----------

    def list_decks(self):
        """
        Returns a dict you can show in UI, including which deck is default.
        """
        default_id = self.store.get_default_flash_deck_id()
        flash = []
        for deck_id, name, count in self.store.list_flash_decks():
            flash.append({
                "id": deck_id,
                "name": name,
                "count": count,
                "is_default": (deck_id == default_id),
            })
        return {
            "card_game_deck": {"name": "Mana Boss Deck", "count": 40},
            "flash_decks": flash,
            "default_flash_deck_id": default_id,
        }

    def set_default_flash_deck(self, deck_id):
        ok = self.store.set_default_flash_deck(deck_id)
        self.message = "Default deck updated." if ok else "Could not set default deck."
        return ok

    def create_flash_deck(self, name):
        deck_id = self.store.create_deck(name)
        self.store.set_default_flash_deck(deck_id)
        self.message = "Deck created and set as default."
        return deck_id

    def add_flashcard(self, deck_id, front, back):
        ok = self.store.add_card(deck_id, front, back)
        self.message = "Card added." if ok else "Could not add card."
        return ok

    # ---------- Start sessions ----------

    def start_card_game(self, deck_id=None):
        """
        Starts the combined game:
          - card game engine
          - flashcard questions for mana from chosen/default deck
        """
        if deck_id is None:
            deck_id = self.store.get_default_flash_deck_id()

        cards = self.store.get_deck_cards(deck_id)
        if len(cards) == 0:
            cards = self.store.get_deck_cards("sample")

        self.session = CardGameSession(cards)
        self.mode = "card_game"
        self.message = ""
        return True

    def start_flashcards(self, deck_id):
        cards = self.store.get_deck_cards(deck_id)
        self.session = FlashcardsSession(cards)
        self.mode = "flashcards"
        self.message = ""
        return True

    # ---------- State snapshot ----------

    def get_state(self):
        """
        Returns a JSON-friendly snapshot of the hub state + active session state.
        """
        if self.mode == "menu":
            return {"mode": "menu", "message": self.message, "decks": self.list_decks()}

        if self.mode == "multiplayer":
            return {"mode": "multiplayer", "message": self.message}

        if self.session is None:
            return {"mode": self.mode, "error": "No active session."}

        # Attach hub-level message
        state = self.session.get_state()
        state["hub_message"] = self.message
        return state
