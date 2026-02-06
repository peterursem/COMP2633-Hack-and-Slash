# hub/deck_store.py
import json
import os
import time

from .sample_flashcards import get_sample_flashcards_20


class DeckStore:
    """
    Stores multiple flashcard decks in one JSON file.

    decks.json format:
    {
      "default_flash_deck_id": "sample",
      "decks": {
         "sample": {"name": "...", "cards": [{"front":"...","back":"..."}]}
      }
    }
    """

    def __init__(self, path="decks.json"):
        self.path = path
        self.data = {"default_flash_deck_id": "sample", "decks": {}}
        self.load()
        self.ensure_sample_deck()

    def load(self):
        if not os.path.exists(self.path):
            return
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                self.data = json.load(f)
            if "decks" not in self.data or not isinstance(self.data["decks"], dict):
                self.data["decks"] = {}
            if "default_flash_deck_id" not in self.data:
                self.data["default_flash_deck_id"] = "sample"
        except:
            # keep defaults
            self.data = {"default_flash_deck_id": "sample", "decks": {}}

    def save(self):
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except:
            pass

    def ensure_sample_deck(self):
        if "sample" not in self.data["decks"]:
            self.data["decks"]["sample"] = {
                "name": "Sample Deck (20)",
                "cards": get_sample_flashcards_20()
            }
            self.data["default_flash_deck_id"] = "sample"
            self.save()

    def list_flash_decks(self):
        # returns list of (deck_id, name, count)
        result = []
        for deck_id, d in self.data["decks"].items():
            name = str(d.get("name", "Untitled"))
            cards = d.get("cards", [])
            count = len(cards) if isinstance(cards, list) else 0
            result.append((deck_id, name, count))
        # stable ordering: sample first, then by name
        result.sort(key=lambda x: (0 if x[0] == "sample" else 1, x[1].lower()))
        return result

    def get_default_flash_deck_id(self):
        deck_id = self.data.get("default_flash_deck_id", "sample")
        if deck_id not in self.data["decks"]:
            return "sample"
        return deck_id

    def set_default_flash_deck(self, deck_id):
        if deck_id in self.data["decks"]:
            self.data["default_flash_deck_id"] = deck_id
            self.save()
            return True
        return False

    def get_deck(self, deck_id):
        return self.data["decks"].get(deck_id)

    def get_deck_cards(self, deck_id):
        d = self.get_deck(deck_id)
        if not d:
            return []
        cards = d.get("cards", [])
        if not isinstance(cards, list):
            return []
        # ensure strings
        fixed = []
        for c in cards:
            if isinstance(c, dict) and "front" in c and "back" in c:
                fixed.append({"front": str(c["front"]), "back": str(c["back"])})
        return fixed

    def create_deck(self, name):
        # simple unique id
        deck_id = "deck_" + str(int(time.time() * 1000))
        self.data["decks"][deck_id] = {"name": str(name), "cards": []}
        self.save()
        return deck_id

    def add_card(self, deck_id, front, back):
        if deck_id not in self.data["decks"]:
            return False
        self.data["decks"][deck_id]["cards"].append({"front": str(front), "back": str(back)})
        self.save()
        return True
