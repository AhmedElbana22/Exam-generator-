from dataclasses import dataclass, field
from typing import Optional
from model.question_model import Question


@dataclass
class Quiz:
    """
    Represents a full quiz session.

    Attributes:
        quiz_id:        Unique identifier
        topic:          What the quiz is about
        difficulty:     'easy', 'medium', or 'hard'
        question_type:  'MCQ', 'true_false', or 'short_answer'
        language:       'english' or 'arabic'
        questions:      List of Question objects
        current_index:  Tracks which question user is on
        score:          Number of correct answers so far
        is_complete:    True when all questions answered
    """

    quiz_id:       str
    topic:         str
    difficulty:    str
    question_type: str
    language:      str                        = "english"
    questions:     list[Question]             = field(default_factory=list)
    current_index: int                        = 0
    score:         int                        = 0
    is_complete:   bool                       = False
 

    def current_question(self) -> Optional[Question]:
        """Return the current unanswered question."""
        if self.current_index < len(self.questions):
            return self.questions[self.current_index]
        return None

    def submit_answer(self, user_answer: str) -> bool:
        """
        Submit answer for current question.
        Evaluates correctness and advances to next question.

        Args:
            user_answer: The user's answer string

        Returns:
            True if answer was correct, False otherwise
        """
        question = self.current_question()
        if question is None:
            return False

        question.user_answer = user_answer.strip()
        question.is_correct  = self._evaluate(question, user_answer)

        if question.is_correct:
            self.score += 1

        self.current_index += 1

        if self.current_index >= len(self.questions):
            self.is_complete = True

        return question.is_correct

    def _evaluate(self, question: Question, user_answer: str) -> bool:
        """
        Evaluate correctness based on question type.

        MCQ:          exact match on letter (A/B/C/D)
        true_false:   case-insensitive match
        short_answer: checks if any key_point appears in answer
        """
        ua = user_answer.strip().lower()
        ca = question.answer.strip().lower()

        if question.question_type == "MCQ":
            return ua == ca

        elif question.question_type == "true_false":
            return ua in ("true", "false") and ua == ca

        elif question.question_type == "short_answer":
            if question.key_points:
                # at least half the key points must appear in answer
                hits = sum(
                    kp.lower() in ua
                    for kp in question.key_points
                )
                return hits >= max(1, len(question.key_points) // 2)
            return ca in ua

        return False

    def progress(self) -> dict:
        """Return current progress summary."""
        total = len(self.questions)
        answered = self.current_index
        return {
            "total":      total,
            "answered":   answered,
            "remaining":  total - answered,
            "score":      self.score,
            "percentage": round((self.score / total * 100) if total > 0 else 0, 1),
            "is_complete": self.is_complete,
        }

    def summary(self) -> dict:
        """Return final quiz summary after completion."""
        return {
            "quiz_id":       self.quiz_id,
            "topic":         self.topic,
            "difficulty":    self.difficulty,
            "question_type": self.question_type,
            "total":         len(self.questions),
            "score":         self.score,
            "percentage":    self.progress()["percentage"],
            "questions":     [q.to_dict() for q in self.questions],
        }