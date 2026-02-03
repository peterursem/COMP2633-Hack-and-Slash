import random

def normalize_answer(s):
    return " ".join(s.lower().strip().split())

def start_quiz(cards):
    order = list(range(len(cards)))
    random.shuffle(order)
    return {"order": order, "pos": 0, "score": 0}

def current_card(cards, state):
    if state["pos"] >= len(state["order"]):
        return None
    idx = state["order"][state["pos"]]
    return cards[idx]

def check_answer(correct, user):
    return normalize_answer(correct) == normalize_answer(user)

def apply_answer(cards, state, user_answer):
    card = current_card(cards, state)
    if card is None:
        return {"done": True, "state": state, "correct": False, "correct_answer": ""}

    correct = check_answer(card["back"], user_answer)
    new_state = dict(state)
    if correct:
        new_state["score"] += 1

    # advance to next question
    new_state["pos"] += 1
    done = new_state["pos"] >= len(new_state["order"])

    return {
        "done": done,
        "state": new_state,
        "correct": correct,
        "correct_answer": card["back"],
    }
