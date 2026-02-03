# engine.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uuid

from cardgame_app.cardgame.engine import GameEngine  # or your engine_core

app = FastAPI()
GAMES = {}  # game_id -> GameEngine instance

class StartReq(BaseModel):
    deck_id: str = "sample"   # which flashcard deck to use
    user_id: str = "anon"

@app.post("/game/start")
def game_start(req: StartReq):
    game = GameEngine()  # create a fresh game session
    game_id = str(uuid.uuid4())
    GAMES[game_id] = game

    # return whatever state your UI/client needs
    return {
        "game_id": game_id,
        "state": {
            "turn": game.turn_number,
            "player_hp": game.player.hp,
            "player_mana": game.player.mana,
            "boss_hp": game.boss.hp,
            "boss_resists": game.boss.resistant_to,
            "hand": [c.to_short_text() for c in game.player.hand],
        }
    }

@app.get("/game/state/{game_id}")
def game_state(game_id: str):
    game = GAMES.get(game_id)
    if not game:
        raise HTTPException(404, "Unknown game_id")
    return {
        "turn": game.turn_number,
        "player_hp": game.player.hp,
        "player_mana": game.player.mana,
        "boss_hp": game.boss.hp,
        "boss_resists": game.boss.resistant_to,
        "hand": [c.to_short_text() for c in game.player.hand],
    }
