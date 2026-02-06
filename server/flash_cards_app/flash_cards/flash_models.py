class Card:
    def __init__(self, card_id, front, back):
        self.id = card_id
        self.front = front
        self.back = back

    def to_dict(self):
        return {"id": self.id, "front": self.front, "back": self.back}

    @staticmethod
    def from_dict(d):
        return Card(d.get("id"), str(d.get("front", "")), str(d.get("back", "")))
