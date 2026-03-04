from dataclasses import dataclass, field
from collections import defaultdict


@dataclass
class UserPerformance:

    total_answered:     int  = 0
    total_correct:      int  = 0
    session_history:    list = field(default_factory=list)
    current_difficulty: str  = "medium"

    # these MUST be last because they have mutable defaults
    topic_scores:       dict = field(default_factory=lambda: defaultdict(list))
    difficulty_scores:  dict = field(default_factory=lambda: defaultdict(list))

    def record_answer(self, topic: str, difficulty: str, is_correct: bool) -> None:
        self.total_answered += 1
        if is_correct:
            self.total_correct += 1
        self.topic_scores[topic].append(is_correct)
        self.difficulty_scores[difficulty].append(is_correct)

    def record_session(self, session_summary: dict) -> None:
        self.session_history.append(session_summary)

    def overall_accuracy(self) -> float:
        if self.total_answered == 0:
            return 0.0
        return round(self.total_correct / self.total_answered * 100, 1)

    def topic_accuracy(self, topic: str) -> float:
        scores = self.topic_scores.get(topic, [])
        if not scores:
            return 0.0
        return round(sum(scores) / len(scores) * 100, 1)

    def difficulty_accuracy(self, difficulty: str) -> float:
        scores = self.difficulty_scores.get(difficulty, [])
        if not scores:
            return 0.0
        return round(sum(scores) / len(scores) * 100, 1)

    def weak_topics(self, threshold: float = 60.0) -> list:
        weak = []
        for topic, scores in self.topic_scores.items():
            if len(scores) >= 2:
                acc = round(sum(scores) / len(scores) * 100, 1)
                if acc < threshold:
                    weak.append((topic, acc))
        weak.sort(key=lambda x: x[1])
        return [topic for topic, _ in weak]

    def strong_topics(self, threshold: float = 80.0) -> list:
        strong = []
        for topic, scores in self.topic_scores.items():
            if len(scores) >= 2:
                acc = round(sum(scores) / len(scores) * 100, 1)
                if acc >= threshold:
                    strong.append(topic)
        return strong

    def summary(self) -> dict:
        return {
            "total_answered":     self.total_answered,
            "total_correct":      self.total_correct,
            "overall_accuracy":   self.overall_accuracy(),
            "current_difficulty": self.current_difficulty,
            "weak_topics":        self.weak_topics(),
            "strong_topics":      self.strong_topics(),
            "sessions_completed": len(self.session_history),
        }