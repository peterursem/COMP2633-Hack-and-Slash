# cardgame/questions.py
import random

class QuestionManager:
    """
    Each turn: player must answer 3 questions.
    Each correct answer gives +3 mana.
    """

    def __init__(self):
        self.total = 3
        self.asked = 0
        self.current_question = ""
        self.current_answer = ""
        self._generate_next()

    def _generate_next(self):
        # Simple arithmetic questions (beginner-friendly)
        a = random.randint(2, 12)
        b = random.randint(2, 12)
        op = random.choice(["+", "-", "*"])

        if op == "+":
            self.current_question = f"What is {a} + {b}?"
            self.current_answer = str(a + b)
        elif op == "-":
            # keep it non-negative
            x = max(a, b)
            y = min(a, b)
            self.current_question = f"What is {x} - {y}?"
            self.current_answer = str(x - y)
        else:
            self.current_question = f"What is {a} * {b}?"
            self.current_answer = str(a * b)

    def submit(self, user_text):
        """
        Returns True if correct, False otherwise.
        Advances question count.
        """
        user = user_text.strip()
        correct = (user == self.current_answer)

        self.asked += 1
        if not self.is_done():
            self._generate_next()

        return correct

    def is_done(self):
        return self.asked >= self.total
