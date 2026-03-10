from dataclasses import dataclass, field
from typing import Optional
from model.question_model import Question


@dataclass
class Quiz:
    """
    Represents a full quiz session.
 
        - mixed type support (questions have individual types)
        - improved short_answer evaluation (keyword overlap ratio) 
        - progress() exposes per-question correctness list for dot rendering
        - summary() includes per-type breakdown
    """

    quiz_id:        str
    topic:          str
    difficulty:     str
    question_type:  str           # 'MCQ' | 'true_false' | 'short_answer' | 'mixed'
    language:       str                    = "english"
    questions:      list[Question]         = field(default_factory=list)
    current_index:  int                    = 0
    score:          int                    = 0
    is_complete:    bool                   = False

    # Navigation
    
    def current_question(self) -> Optional[Question]:
        if self.current_index < len(self.questions):
            return self.questions[self.current_index]
        return None

    def submit_answer(self, user_answer: str) -> bool:
        """
        Record user answer, evaluate, advance index.
        Returns True if correct.
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

    # Evaluation

    def _evaluate(self, question: Question, user_answer: str) -> bool:
        ua = user_answer.strip().lower()
        ca = question.answer.strip().lower()

        if question.question_type == "MCQ":
            # accept both "A" and "A) text" formats
            return ua.strip(".) ").upper() == ca.strip(".) ").upper()

        elif question.question_type == "true_false":
            # accept "true"/"false"/"t"/"f"/"yes"/"no"
            truth_map  = {"true": True,  "t": True,  "yes": True,  "1": True}
            false_map  = {"false": False, "f": False, "no": False,  "0": False}
            ua_bool = truth_map.get(ua, false_map.get(ua, None))
            ca_bool = truth_map.get(ca, false_map.get(ca, None))
            if ua_bool is None or ca_bool is None:
                return ua == ca
            return ua_bool == ca_bool

        elif question.question_type == "short_answer":
            return self._eval_short_answer(question, ua)

        return False

    def _eval_short_answer(self, question: Question, ua: str) -> bool:
        """
        Keyword overlap evaluation for short answers.
        Passes if the user answer contains ≥ 50% of key_points,
        or if the canonical answer words are sufficiently present.
        """
        if question.key_points:
            hits = sum(kp.lower() in ua for kp in question.key_points)
            threshold = max(1, len(question.key_points) // 2)
            return hits >= threshold

        # fallback: check that ≥ 60% of meaningful answer words appear
        ca_words = [
            w for w in question.answer.lower().split()
            if len(w) > 3
        ]
        if not ca_words:
            return question.answer.lower() in ua

        hits = sum(w in ua for w in ca_words)
        return hits / len(ca_words) >= 0.6

    # Progress & Summary

    def progress(self) -> dict:
        total    = len(self.questions)
        answered = self.current_index
        results  = [
            q.is_correct
            for q in self.questions[:answered] 
        ]
        return {
            "total":       total,
            "answered":    answered,
            "remaining":   total - answered,
            "score":       self.score,
            "percentage":  round((self.score / total * 100) if total > 0 else 0, 1),
            "is_complete": self.is_complete,
            "results":     results,   # [True, False, True, ...] for dot renderer
        }

    def summary(self) -> dict: 
        type_breakdown: dict[str, dict] = {}
        for q in self.questions:
            t = q.question_type
            if t not in type_breakdown:
                type_breakdown[t] = {"total": 0, "correct": 0}
            type_breakdown[t]["total"] += 1
            if q.is_correct:
                type_breakdown[t]["correct"] += 1

        return {
            "quiz_id":        self.quiz_id,
            "topic":          self.topic,
            "difficulty":     self.difficulty,
            "question_type":  self.question_type,
            "total":          len(self.questions),
            "score":          self.score,
            "percentage":     self.progress()["percentage"],
            "type_breakdown": type_breakdown,
            "questions":      [q.to_dict() for q in self.questions],
        }