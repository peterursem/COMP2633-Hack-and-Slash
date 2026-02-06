# cardgame/deck_factory.py
from .models import Card

def build_starting_deck():
    """
    40 cards total:
      - 5x each elemental attack: ice, fire, water (15)
      - 5x draw two more cards (5) -> total 20
      - 5x block each element type pre-emptively (fire/water/ice) (15) -> total 35
      - 5x random effects (5) -> total 40
    """
    deck = []

    # Attack cards (5 each)
    for _ in range(5):
        deck.append(Card("Ice Bolt", "attack", "ice", 5, "Deal ice damage to boss."))
        deck.append(Card("Fire Bolt", "attack", "fire", 5, "Deal fire damage to boss."))
        deck.append(Card("Water Bolt", "attack", "water", 5, "Deal water damage to boss."))

    # Draw cards (5)
    for _ in range(5):
        deck.append(Card("Quick Study", "draw", None, 5, "Draw 2 cards."))

    # Block cards (5 each)
    for _ in range(5):
        deck.append(Card("Fire Ward", "block", "fire", 5, "Block next fire attack."))
        deck.append(Card("Water Ward", "block", "water", 5, "Block next water attack."))
        deck.append(Card("Ice Ward", "block", "ice", 5, "Block next ice attack."))

    # Random effect cards (5)
    for _ in range(5):
        deck.append(Card("Chaos Rune", "random", "chaos", 5, "Random effect."))

    return deck
