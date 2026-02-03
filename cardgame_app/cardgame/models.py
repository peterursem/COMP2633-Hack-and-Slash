# cardgame/models.py

class Card:
    def __init__(self, name, card_type, element, cost, description=""):
        self.name = name
        self.card_type = card_type      # "attack", "block", "draw", "random"
        self.element = element          # "fire","water","ice","chaos" or None
        self.cost = cost                # mana cost (all are 5 per your rules)
        self.description = description

    def to_short_text(self):
        # used by UI for simple display
        if self.element:
            return f"{self.name} ({self.element})"
        return self.name


class Player:
    def __init__(self):
        self.max_hp = 60
        self.hp = 60
        self.mana = 0

        # Shields are pre-emptive: if active and boss attacks that element, block it once.
        self.shields = {"fire": False, "water": False, "ice": False}

        self.hand = []
        self.draw_pile = []
        self.discard_pile = []


class Boss:
    def __init__(self):
        self.max_hp = 120
        self.hp = 120

        # Boss resistance type changes each turn: that type takes 50% damage.
        self.resistant_to = "fire"
