from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Question:
    """
    Represents one quiz question regardless of type.

    Attributes:
        question_id:   Unique index within the quiz
        question_type: 'MCQ', 'true_false', or 'short_answer'
        question:      The question text
        answer:        The correct answer
        explanation:   Why this answer is correct
        options:       Only for MCQ — dict of {'A': '...', 'B': '...', ...}
        key_points:    Only for short_answer — list of expected key points
        user_answer:   Filled in when user submits their answer
        is_correct:    Filled in after evaluation
    """

    question_id:   int
    question_type: str
    question:      str
    answer:        str
    explanation:   str                        = ""
    options:       Optional[dict]             = None
    key_points:    Optional[list]             = None
    user_answer:   Optional[str]              = None
    is_correct:    Optional[bool]             = None

    def to_dict(self) -> dict:
        """Convert to plain dict for storage or display."""
        return {
            "question_id":   self.question_id,
            "question_type": self.question_type,
            "question":      self.question,
            "answer":        self.answer,
            "explanation":   self.explanation,
            "options":       self.options,
            "key_points":    self.key_points,
            "user_answer":   self.user_answer,
            "is_correct":    self.is_correct,
        }

    @staticmethod
    def from_dict(data: dict, question_id: int, question_type: str) -> "Question":
        """
        Build a Question from raw LLM JSON output.

        Args:
            data:          Dict parsed from LLM response
            question_id:   Index of this question in the quiz
            question_type: 'MCQ', 'true_false', or 'short_answer'
        """
        return Question(
            question_id=question_id,
            question_type=question_type,
            question=data.get("question", ""),
            answer=str(data.get("answer", "")),
            explanation=data.get("explanation", ""),
            options=data.get("options", None),
            key_points=data.get("key_points", None),
        )