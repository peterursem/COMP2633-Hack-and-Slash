# engine.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uuid
import random

from hub_app.hub.game_engine import GameEngine
from hub_app.hub.deck_store import DeckStore

app = FastAPI()

# Deck storage (same thing your pygame app uses)
STORE = DeckStore("decks.json")

# game_id -> session dict (engine + question state)
GAMES = {}


def normalize_answer(s):
    return " ".join(str(s).lower().strip().split())


class FlashcardQuestionCycler:
    def __init__(self, cards):
        self.cards = cards[:] if cards else []
        self.order = list(range(len(self.cards)))
        random.shuffle(self.order)
        self.pos = 0

    def next(self):
        if len(self.cards) == 0:
            return None, None

        if self.pos >= len(self.order):
            random.shuffle(self.order)
            self.pos = 0

        idx = self.order[self.pos]
        self.pos += 1
        c = self.cards[idx]
        return c["front"], c["back"]


def snapshot(game_id):
    s = GAMES.get(game_id)
    if not s:
        raise HTTPException(404, "Unknown game_id")

    g = s["game"]
    return {
        "game_id": game_id,
        "phase": s["phase"],  # "questions" or "play" or "game_over"
        "turn": g.turn_number,
        "player_hp": g.player.hp,
        "player_max_hp": g.player.max_hp,
        "player_mana": g.player.mana,
        "boss_hp": g.boss.hp,
        "boss_max_hp": g.boss.max_hp,
        "boss_resists": g.boss.resistant_to,
        "hand": [c.to_short_text() for c in g.player.hand],
        "questions_left": s["questions_left"],
        "current_question": s["current_q"],
        "game_over": g.game_over,
        "winner": g.winner,
        "log": list(g.log_lines)[-6:],
    }


# -------------------------
# Hub / Menu endpoints
# -------------------------

@app.get("/hub/menu")
def hub_menu():
    # This is "menu data" (not a GUI)
    default_id = STORE.get_default_flash_deck_id()
    decks = []
    for deck_id, name, count in STORE.list_flash_decks():
        decks.append({
            "id": deck_id,
            "name": name,
            "count": count,
            "is_default": (deck_id == default_id),
        })

    return {
        "title": "Hub App: Flashcards + Card Game",
        "options": [
            "start_card_game",
            "view_decks",
            "create_deck",
            "multiplayer_not_implemented",
            "exit"
        ],
        "default_flash_deck_id": default_id,
        "flash_decks": decks,
        "card_game_deck": {"name": "Mana Boss Deck", "count": 40},
    }


# -------------------------
# Deck management endpoints
# -------------------------

class CreateDeckReq(BaseModel):
    name: str


class AddCardReq(BaseModel):
    front: str
    back: str


@app.get("/decks")
def list_decks():
    default_id = STORE.get_default_flash_deck_id()
    out = []
    for deck_id, name, count in STORE.list_flash_decks():
        out.append({
            "id": deck_id,
            "name": name,
            "count": count,
            "is_default": (deck_id == default_id),
        })
    return {"default_flash_deck_id": default_id, "flash_decks": out}


@app.post("/decks")
def create_deck(req: CreateDeckReq):
    name = (req.name or "").strip()
    if not name:
        raise HTTPException(400, "Deck name cannot be empty.")

    deck_id = STORE.create_deck(name)
    # optional: auto-default new deck
    STORE.set_default_flash_deck(deck_id)

    return {"ok": True, "deck_id": deck_id, "name": name}


@app.post("/decks/{deck_id}/default")
def set_default_deck(deck_id: str):
    ok = STORE.set_default_flash_deck(deck_id)
    if not ok:
        raise HTTPException(404, "Deck not found.")
    return {"ok": True, "default_flash_deck_id": deck_id}


@app.post("/decks/{deck_id}/cards")
def add_card(deck_id: str, req: AddCardReq):
    front = (req.front or "").strip()
    back = (req.back or "").strip()
    if not front or not back:
        raise HTTPException(400, "Front and back must be non-empty.")

    ok = STORE.add_card(deck_id, front, back)
    if not ok:
        raise HTTPException(404, "Deck not found.")
    return {"ok": True}


# -------------------------
# Game endpoints (integrated)
# -------------------------

class StartReq(BaseModel):
    deck_id: str = ""    # optional; if blank, use default
    user_id: str = "anon"


@app.post("/game/start")
def game_start(req: StartReq):
    # pick deck for questions
    deck_id = (req.deck_id or "").strip()
    if not deck_id:
        deck_id = STORE.get_default_flash_deck_id()

    cards = STORE.get_deck_cards(deck_id)
    if len(cards) == 0:
        cards = STORE.get_deck_cards("sample")

    cycler = FlashcardQuestionCycler(cards)
    q, a = cycler.next()

    game = GameEngine()
    game.start_new_turn()  # IMPORTANT: match pygame sequence (turn 1 + draw)

    game_id = str(uuid.uuid4())
    GAMES[game_id] = {
        "game": game,
        "cycler": cycler,
        "phase": "questions",
        "questions_left": 3,
        "current_q": q,
        "current_a": a,
        "deck_id": deck_id,
        "user_id": req.user_id,
    }

    return snapshot(game_id)


@app.get("/game/state/{game_id}")
def game_state(game_id: str):
    return snapshot(game_id)


class AnswerReq(BaseModel):
    game_id: str
    answer: str


@app.post("/game/answer")
def game_answer(req: AnswerReq):
    s = GAMES.get(req.game_id)
    if not s:
        raise HTTPException(404, "Unknown game_id")

    if s["phase"] != "questions":
        raise HTTPException(400, "Not in questions phase.")

    g = s["game"]

    # compare answer
    ok = normalize_answer(req.answer) == normalize_answer(s["current_a"])
    if ok and s["current_a"] is not None:
        g.grant_mana_for_correct_answer()
    else:
        g._log("Wrong. +0 mana.")

    s["questions_left"] -= 1

    if s["questions_left"] <= 0:
        s["phase"] = "play"
        s["current_q"], s["current_a"] = None, None
    else:
        q, a = s["cycler"].next()
        s["current_q"], s["current_a"] = q, a

    if g.game_over:
        s["phase"] = "game_over"

    out = snapshot(req.game_id)
    out["answer_correct"] = ok
    return out


class PlayReq(BaseModel):
    game_id: str
    hand_index: int


@app.post("/game/play")
def game_play(req: PlayReq):
    s = GAMES.get(req.game_id)
    if not s:
        raise HTTPException(404, "Unknown game_id")

    if s["phase"] != "play":
        raise HTTPException(400, "Not in play phase.")

    g = s["game"]
    success, msg = g.play_card_from_hand(req.hand_index)

    if g.game_over:
        s["phase"] = "game_over"

    out = snapshot(req.game_id)
    out["play_success"] = success
    out["message"] = msg
    return out


class EndTurnReq(BaseModel):
    game_id: str


@app.post("/game/endturn")
def game_endturn(req: EndTurnReq):
    s = GAMES.get(req.game_id)
    if not s:
        raise HTTPException(404, "Unknown game_id")

    if s["phase"] != "play":
        raise HTTPException(400, "Not in play phase.")

    g = s["game"]
    g.end_player_turn_and_boss_acts()

    if g.game_over:
        s["phase"] = "game_over"
        return snapshot(req.game_id)

    # Next turn begins: reset to questions
    g.start_new_turn()
    s["phase"] = "questions"
    s["questions_left"] = 3
    q, a = s["cycler"].next()
    s["current_q"], s["current_a"] = q, a

    return snapshot(req.game_id)
