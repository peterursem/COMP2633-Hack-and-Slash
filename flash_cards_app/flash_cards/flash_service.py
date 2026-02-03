import random


def normalize_answer(s):
    return " ".join(s.lower().strip().split())


class FlashcardService:
    def __init__(self, repo):
        self.repo = repo

    def get_all_cards(self):
        return self.repo.list_cards()

    def add_card(self, front, back):
        return self.repo.add_card(front, back)

    def delete_card(self, card_id):
        return self.repo.delete_card(card_id)

    def start_quiz(self, cards):
        order = list(range(len(cards)))
        random.shuffle(order)
        return {"order": order, "pos": 0, "score": 0}

    def quiz_current_card(self, cards, quiz_state):
        if quiz_state["pos"] >= len(quiz_state["order"]):
            return None
        idx = quiz_state["order"][quiz_state["pos"]]
        return cards[idx]

    def quiz_check_answer(self, correct, user):
        return normalize_answer(correct) == normalize_answer(user)
