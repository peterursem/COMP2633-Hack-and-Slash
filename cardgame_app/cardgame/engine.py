# cardgame/engine.py
import random
from .models import Player, Boss
from .deck_factory import build_starting_deck

ELEMENTS_3 = ["fire", "water", "ice"]
ELEMENTS_4 = ["fire", "water", "ice", "chaos"]  # boss resistance can include chaos too

class GameEngine:
    """
    Headless game rules. No pygame imports.
    UI calls this class.
    """

    def __init__(self):
        self.player = Player()
        self.boss = Boss()

        self.turn_number = 1
        self.game_over = False
        self.winner = None  # "player" or "boss"

        self.log_lines = []

        # Setup deck
        deck = build_starting_deck()
        random.shuffle(deck)
        self.player.draw_pile = deck

        # Boss starts with a random resistance
        self.boss.resistant_to = random.choice(ELEMENTS_4)

        # First turn draw to 5
        self._draw_cards(5)
        self._log("Game start: drew 5 cards.")

    def _log(self, text):
        self.log_lines.append(text)
        if len(self.log_lines) > 8:
            self.log_lines.pop(0)

    def _draw_one(self):
        if len(self.player.draw_pile) == 0:
            # reshuffle discard into draw pile
            if len(self.player.discard_pile) == 0:
                return None
            self.player.draw_pile = self.player.discard_pile
            self.player.discard_pile = []
            random.shuffle(self.player.draw_pile)
            self._log("Reshuffled discard into draw pile.")

        return self.player.draw_pile.pop()

    def _draw_cards(self, count):
        for _ in range(count):
            c = self._draw_one()
            if c is None:
                return
            self.player.hand.append(c)

    def start_new_turn(self):
        """
        Called by UI when it's time to start player's turn.
        Also changes boss resistance each turn.
        """
        if self.game_over:
            return

        # Boss resistance changes each turn
        self.boss.resistant_to = random.choice(ELEMENTS_4)
        self._log(f"Turn {self.turn_number}: Boss resists {self.boss.resistant_to} (50% damage).")

        if self.turn_number > 1:
            # draw 1 each turn after first
            self._draw_cards(1)
            self._log("Drew 1 card.")

    def grant_mana_for_correct_answer(self):
        """
        Each correct question gives +3 mana.
        """
        self.player.mana += 3
        self._log("Correct! +3 mana.")

    def play_card_from_hand(self, hand_index):
        """
        Attempt to cast a card by index in hand.
        Returns (success_bool, message).
        """
        if self.game_over:
            return False, "Game is over."

        if hand_index < 0 or hand_index >= len(self.player.hand):
            return False, "Invalid card."

        card = self.player.hand[hand_index]
        if self.player.mana < card.cost:
            return False, "Not enough mana (need 5)."

        # Pay mana
        self.player.mana -= card.cost

        # Remove from hand -> discard
        self.player.hand.pop(hand_index)
        self.player.discard_pile.append(card)

        # Resolve effect
        self._resolve_card(card)
        self._check_game_over()

        return True, f"Played {card.name}."

    def _resolve_card(self, card):
        if card.card_type == "attack":
            base = 14
            dmg = base
            if card.element == self.boss.resistant_to:
                dmg = int(base * 0.5)

            self.boss.hp -= dmg
            self._log(f"{card.name} hits boss for {dmg}.")

        elif card.card_type == "draw":
            self._draw_cards(2)
            self._log("Drew 2 cards.")

        elif card.card_type == "block":
            if card.element in self.player.shields:
                self.player.shields[card.element] = True
                self._log(f"Shield prepared: block next {card.element} attack.")

        elif card.card_type == "random":
            self._random_effect()

    def _random_effect(self):
        # Keep effects simple and readable
        effects = ["heal", "mana", "chaos_damage", "draw", "big_attack"]
        pick = random.choice(effects)

        if pick == "heal":
            heal = 10
            self.player.hp = min(self.player.max_hp, self.player.hp + heal)
            self._log(f"Chaos Rune: healed player for {heal}.")

        elif pick == "mana":
            gain = 6
            self.player.mana += gain
            self._log(f"Chaos Rune: gained {gain} mana.")

        elif pick == "chaos_damage":
            base = 16
            dmg = base
            if "chaos" == self.boss.resistant_to:
                dmg = int(base * 0.5)
            self.boss.hp -= dmg
            self._log(f"Chaos Rune: dealt {dmg} chaos damage.")

        elif pick == "draw":
            self._draw_cards(1)
            self._log("Chaos Rune: drew 1 card.")

        else:
            base = 22
            dmg = base
            # treat as "fire" for resistance? no — treat as chaos
            if "chaos" == self.boss.resistant_to:
                dmg = int(base * 0.5)
            self.boss.hp -= dmg
            self._log(f"Chaos Rune: big hit for {dmg} damage!")

    def end_player_turn_and_boss_acts(self):
        """
        Boss uses a basic magic attack (fire/water/ice).
        Can be blocked if the player played the matching ward.
        Then increment turn.
        """
        if self.game_over:
            return

        boss_element = random.choice(ELEMENTS_3)
        boss_dmg = 10

        if self.player.shields.get(boss_element, False):
            # Block consumes shield
            self.player.shields[boss_element] = False
            self._log(f"Boss casts {boss_element}! Blocked by ward.")
        else:
            self.player.hp -= boss_dmg
            self._log(f"Boss casts {boss_element}! Player takes {boss_dmg}.")

        self._check_game_over()

        self.turn_number += 1

    def _check_game_over(self):
        if self.boss.hp <= 0 and not self.game_over:
            self.game_over = True
            self.winner = "player"
            self.boss.hp = 0
            self._log("Boss defeated!")

        if self.player.hp <= 0 and not self.game_over:
            self.game_over = True
            self.winner = "boss"
            self.player.hp = 0
            self._log("Player defeated!")
