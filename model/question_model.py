import hashlib
from dataclasses import dataclass, field 
from typing import Optional


@dataclass 
class Question:
    """
    Represents one quiz question regardless of type.

    New fields
        fingerprint  : SHA-1 of (question + answer) for deduplication
        revealed     : True once the user has seen the feedback (UI state)
    """

    question_id:   int
    question_type: str          # 'MCQ' | 'true_false' | 'short_answer'
    question:      str
    answer:        str
    explanation:   str                    = ""
    options:       Optional[dict]         = None   # MCQ only
    key_points:    Optional[list]         = None   # short_answer only
    user_answer:   Optional[str]          = None
    is_correct:    Optional[bool]         = None
    revealed:      bool                   = False  # feedback shown to user
    fingerprint:   str                    = field(init=False) 

    def __post_init__(self): 
        self.fingerprint = self._make_fingerprint(self.question, self.answer)

    # Hashing

    @staticmethod 
    def _make_fingerprint(question: str, answer: str) -> str: 
        """SHA-1 of normalised question+answer — used for cross-session dedup."""
        raw = f"{question.strip().lower()}||{answer.strip().lower()}"
        return hashlib.sha1(raw.encode()).hexdigest()[:16]
     
    # Serialisation

    def to_dict(self) -> dict:
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
            "fingerprint":   self.fingerprint,
        }

    @staticmethod 
    def from_dict(data: dict, question_id: int, question_type: str) -> "Question":
        """Build a Question from raw LLM JSON output."""
        return Question(
            question_id   = question_id,
            question_type = question_type,
            question      = data.get("question", "").strip(),
            answer        = str(data.get("answer", "")).strip(),
            explanation   = data.get("explanation", "").strip(),
            options       = data.get("options")   or None,
            key_points    = data.get("key_points") or None,
        )