# hub_app/hub/game_engine.py
import random


# ----------------------------
# Simple data classes (junior-friendly)
# ----------------------------

class Card:
    def __init__(self, name, card_type, cost=5, element=None, power=0):
        self.name = name
        self.card_type = card_type      # "attack", "block", "draw", "random"
        self.cost = cost
        self.element = element          # "fire", "water", "ice", "arcane", or None
        self.power = power              # damage amount (for attacks)

    def to_short_text(self):
        # Keep it short for your hand UI
        if self.card_type == "attack":
            return f"{self.element.title()} Attack ({self.power})"
        if self.card_type == "block":
            return f"Block {self.element.title()}"
        if self.card_type == "draw":
            return "Draw +2"
        if self.card_type == "random":
            return "Random"
        return self.name


class Player:
    def __init__(self):
        self.max_hp = 60
        self.hp = self.max_hp

        self.mana = 0

        # Shields block a matching element once per shield
        self.shields = {
            "fire": 0,
            "water": 0,
            "ice": 0,
            "arcane": 0,
        }

        self.hand = []


class Boss:
    def __init__(self):
        self.max_hp = 90
        self.hp = self.max_hp

        # Each turn boss "resists" 1 type => takes 50% damage from it
        self.resistant_to = "fire"


# ----------------------------
# Integrated Game Engine
# ----------------------------

class GameEngine:
    """
    Hub-native engine for the integrated game.

    - Turn-based boss fight with mana.
    - Cards cost 5 mana.
    - Boss resists one of 4 types each turn (fire/water/ice/arcane) => 50% damage.
    - Player gains mana via flashcard questions (grant_mana_for_correct_answer = +3).
    - Deck: 40 cards
        * 5 Fire attack, 5 Water attack, 5 Ice attack (15)
        * 5 Draw +2 (5)
        * 5 Block Fire, 5 Block Water, 5 Block Ice (15)
        * 5 Random (5)
        = 40
    """

    def __init__(self):
        self.player = Player()
        self.boss = Boss()

        self.turn_number = 0
        self.log_lines = []

        self.game_over = False
        self.winner = None  # "player" or "boss"

        # Card piles
        self.draw_pile = []
        self.discard_pile = []

        self._build_default_deck()
        self._shuffle_draw_pile()

        # (Optional) If you want to integrate flashcards into this engine later:
        self.flashcards = []
        self._q_order = []
        self._q_pos = 0

    # --------- Logging ---------

    def _log(self, msg):
        self.log_lines.append(msg)
        # Keep log from growing forever
        if len(self.log_lines) > 200:
            self.log_lines = self.log_lines[-200:]

    # --------- Deck building ---------

    def _build_default_deck(self):
        self.draw_pile = []
        self.discard_pile = []

        # Attacks (5 each)
        for _ in range(5):
            self.draw_pile.append(Card("Fire Attack", "attack", 5, "fire", 12))
            self.draw_pile.append(Card("Water Attack", "attack", 5, "water", 12))
            self.draw_pile.append(Card("Ice Attack", "attack", 5, "ice", 12))

        # Draw +2 (5)
        for _ in range(5):
            self.draw_pile.append(Card("Draw Two", "draw", 5, None, 0))

        # Blocks (5 each for 3 elements)
        for _ in range(5):
            self.draw_pile.append(Card("Block Fire", "block", 5, "fire", 0))
            self.draw_pile.append(Card("Block Water", "block", 5, "water", 0))
            self.draw_pile.append(Card("Block Ice", "block", 5, "ice", 0))

        # Random (5)
        for _ in range(5):
            self.draw_pile.append(Card("Random", "random", 5, "arcane", 0))

    def _shuffle_draw_pile(self):
        random.shuffle(self.draw_pile)

    def _reshuffle_from_discard(self):
        if len(self.draw_pile) == 0 and len(self.discard_pile) > 0:
            self.draw_pile = self.discard_pile[:]
            self.discard_pile = []
            self._shuffle_draw_pile()
            self._log("Reshuffled discard into draw pile.")

    def _draw_cards(self, n):
        for _ in range(n):
            self._reshuffle_from_discard()
            if len(self.draw_pile) == 0:
                return
            self.player.hand.append(self.draw_pile.pop())

    # --------- Turn flow ---------

    def start_new_turn(self):
        if self.game_over:
            return

        self.turn_number += 1

        # Boss changes resistance each turn
        self.boss.resistant_to = random.choice(["fire", "water", "ice", "arcane"])
        self._log(f"Turn {self.turn_number} begins. Boss resists {self.boss.resistant_to}.")

        # Draw rules: turn 1 draw to 5; later turns draw 1
        if self.turn_number == 1:
            while len(self.player.hand) < 5:
                self._draw_cards(1)
            self._log("Drew up to 5 cards.")
        else:
            self._draw_cards(1)
            self._log("Drew 1 card.")

    def grant_mana_for_correct_answer(self):
        # Your screens.py calls this
        self.player.mana += 3
        self._log("Correct answer: +3 mana.")

    # --------- Actions ---------

    def play_card_from_hand(self, index):
        if self.game_over:
            return False, "Game is already over."

        if index < 0 or index >= len(self.player.hand):
            return False, "Invalid card."

        card = self.player.hand[index]

        if self.player.mana < card.cost:
            return False, "Not enough mana (need 5)."

        # Pay mana
        self.player.mana -= card.cost

        # Remove from hand and discard it
        played = self.player.hand.pop(index)
        self.discard_pile.append(played)

        # Resolve effect
        msg = self._resolve_card(played)
        self._check_game_over()
        return True, msg

    def _resolve_card(self, card):
        if card.card_type == "attack":
            dmg = card.power
            if card.element == self.boss.resistant_to:
                dmg = int(dmg * 0.5)
                self._log(f"Boss resisted {card.element}! Damage halved.")

            self.boss.hp -= dmg
            self._log(f"Player used {card.to_short_text()} for {dmg} damage.")
            return f"Dealt {dmg} damage."

        if card.card_type == "block":
            # Add a shield that blocks one hit of that type
            if card.element not in self.player.shields:
                self.player.shields[card.element] = 0
            self.player.shields[card.element] += 1
            self._log(f"Player gained 1 {card.element} shield.")
            return f"Shielded against {card.element}."

        if card.card_type == "draw":
            self._draw_cards(2)
            self._log("Player drew 2 cards.")
            return "Drew 2 cards."

        if card.card_type == "random":
            return self._resolve_random_card()

        self._log("Played an unknown card.")
        return "Played a card."

    def _resolve_random_card(self):
        # Simple random effects
        roll = random.randint(1, 5)

        if roll == 1:
            heal = 8
            self.player.hp = min(self.player.max_hp, self.player.hp + heal)
            self._log(f"Random: healed {heal} HP.")
            return f"Random: healed {heal} HP."

        if roll == 2:
            mana = 5
            self.player.mana += mana
            self._log(f"Random: gained {mana} mana.")
            return f"Random: gained {mana} mana."

        if roll == 3:
            dmg = random.randint(6, 16)
            # Treat as "arcane" damage (affected by arcane resist)
            if self.boss.resistant_to == "arcane":
                dmg = int(dmg * 0.5)
                self._log("Boss resisted arcane! Damage halved.")
            self.boss.hp -= dmg
            self._log(f"Random: dealt {dmg} arcane damage.")
            return f"Random: dealt {dmg} damage."

        if roll == 4:
            self._draw_cards(1)
            self._log("Random: drew 1 card.")
            return "Random: drew 1 card."

        # roll == 5
        elem = random.choice(["fire", "water", "ice"])
        self.player.shields[elem] += 1
        self._log(f"Random: gained 1 {elem} shield.")
        return f"Random: gained 1 {elem} shield."

    def end_player_turn_and_boss_acts(self):
        if self.game_over:
            return

        # Boss basic magic attack
        elem = random.choice(["fire", "water", "ice", "arcane"])
        base = 10

        # Shields can block matching element
        if elem in self.player.shields and self.player.shields[elem] > 0:
            self.player.shields[elem] -= 1
            self._log(f"Boss cast {elem}. Player shield blocked it!")
        else:
            self.player.hp -= base
            self._log(f"Boss cast {elem} for {base} damage!")

        self._check_game_over()

    def _check_game_over(self):
        if self.player.hp <= 0 and not self.game_over:
            self.player.hp = 0
            self.game_over = True
            self.winner = "boss"
            self._log("Player was defeated.")
        elif self.boss.hp <= 0 and not self.game_over:
            self.boss.hp = 0
            self.game_over = True
            self.winner = "player"
            self._log("Boss was defeated!")

    # ----------------------------
    # OPTIONAL: flashcards inside this engine
    # (Use if you want to remove FlashcardQuestionCycler from screens.py)
    # ----------------------------

    def set_flashcards(self, flashcards):
        """
        flashcards: list like [{"front": "...", "back": "..."}, ...]
        """
        self.flashcards = flashcards[:] if flashcards else []
        self._q_order = list(range(len(self.flashcards)))
        random.shuffle(self._q_order)
        self._q_pos = 0

    def next_flashcard(self):
        """
        Returns (front, back). Cycles when exhausted.
        """
        if len(self.flashcards) == 0:
            return None, None
        if self._q_pos >= len(self._q_order):
            random.shuffle(self._q_order)
            self._q_pos = 0
        idx = self._q_order[self._q_pos]
        self._q_pos += 1
        c = self.flashcards[idx]
        return c["front"], c["back"]
