import json
import os
import urllib.request
import urllib.error

from .models import Card


class CardRepository:
    # "Interface" (simple base class) — keep it beginner-friendly.
    def list_cards(self):
        raise NotImplementedError

    def add_card(self, front, back):
        raise NotImplementedError

    def delete_card(self, card_id):
        raise NotImplementedError


class JsonFileRepository(CardRepository):
    def __init__(self, path="flashcards.json"):
        self.path = path

    def _load_raw(self):
        if not os.path.exists(self.path):
            return []
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []

    def _save_raw(self, raw_list):
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(raw_list, f, ensure_ascii=False, indent=2)
        except:
            pass

    def list_cards(self):
        raw = self._load_raw()
        cards = []
        for item in raw:
            if isinstance(item, dict) and "front" in item and "back" in item:
                cards.append(Card.from_dict(item))
        return cards

    def add_card(self, front, back):
        raw = self._load_raw()

        # assign next id
        max_id = 0
        for item in raw:
            if isinstance(item, dict) and isinstance(item.get("id"), int):
                if item["id"] > max_id:
                    max_id = item["id"]

        new_card = Card(max_id + 1, front, back)
        raw.append(new_card.to_dict())
        self._save_raw(raw)
        return new_card

    def delete_card(self, card_id):
        raw = self._load_raw()
        new_raw = []
        deleted = False

        for item in raw:
            if isinstance(item, dict) and item.get("id") == card_id:
                deleted = True
            else:
                new_raw.append(item)

        self._save_raw(new_raw)
        return deleted


class HttpApiRepository(CardRepository):
    """
    For Rails integration:
      GET    /api/cards
      POST   /api/cards        body: {"front": "...", "back": "..."}
      DELETE /api/cards/:id

    This uses urllib (standard library) to stay beginner-friendly.
    """
    def __init__(self, base_url):
        self.base_url = base_url.rstrip("/")

    def _request_json(self, method, url, payload=None):
        data = None
        headers = {"Content-Type": "application/json"}
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")

        req = urllib.request.Request(url, data=data, headers=headers, method=method)

        with urllib.request.urlopen(req, timeout=5) as resp:
            text = resp.read().decode("utf-8")
            if text.strip() == "":
                return None
            return json.loads(text)

    def list_cards(self):
        try:
            url = self.base_url + "/api/cards"
            raw = self._request_json("GET", url)
            cards = []
            if isinstance(raw, list):
                for item in raw:
                    if isinstance(item, dict):
                        cards.append(Card.from_dict(item))
            return cards
        except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError):
            return []

    def add_card(self, front, back):
        try:
            url = self.base_url + "/api/cards"
            created = self._request_json("POST", url, {"front": front, "back": back})
            if isinstance(created, dict):
                return Card.from_dict(created)
        except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError):
            pass
        return None

    def delete_card(self, card_id):
        try:
            url = self.base_url + "/api/cards/" + str(card_id)
            self._request_json("DELETE", url)
            return True
        except (urllib.error.URLError, urllib.error.HTTPError):
            return False
