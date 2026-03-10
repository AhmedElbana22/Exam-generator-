"""
Adaptive learning engine.

Changes vs v1:
    - seen_questions set persisted across sessions (rolling window)
    - seen fingerprints passed to QuizController to prevent repeats
    - weak topic logic improved: tracks per-topic accuracy ratio
    - next_quiz preserves question_type correctly
"""

import json
import os
from loguru import logger
from model.user_model import UserPerformance
from model.quiz_model import Quiz
from controller.quiz_controller import QuizController
from config import AppConfig

config = AppConfig()

DIFFICULTY_LADDER  = ["easy", "medium", "hard"]
PROMOTE_THRESHOLD  = config.PROMOTE_THRESHOLD
DEMOTE_THRESHOLD   = config.DEMOTE_THRESHOLD


class AdaptiveController:

    def __init__(self):
        self.quiz_controller  = QuizController()
        self.performance      = UserPerformance()
        self.seen_questions:  set[str] = self._load_seen()   # fingerprint set
        self._last_topic      = ""
        self._last_type       = "MCQ"
        self._last_language   = "english"
        logger.info("AdaptiveController initialized")

    # Document loading

    def load_text(self, text: str) -> int:
        return self.quiz_controller.load_text(text)

    def load_pdf(self, pdf_path: str) -> int:
        return self.quiz_controller.load_pdf(pdf_path)

    # Quiz lifecycle  

    def start_quiz(
        self,
        topic:          str,
        question_type:  str  = "MCQ",
        num_questions:  int  = 5,
        language:       str  = "english",
        difficulty:     str  = None,
    ) -> Quiz:
        """Generate quiz, injecting seen_questions to prevent repetition."""
        difficulty = difficulty or self.performance.current_difficulty

        self._last_topic    = topic
        self._last_type     = question_type
        self._last_language = language

        quiz = self.quiz_controller.generate_quiz(
            topic          = topic,
            question_type  = question_type,
            difficulty     = difficulty,
            num_questions  = num_questions,
            language       = language,
            seen_questions = self.seen_questions,
        )

        # register new fingerprints immediately
        self._register_seen(quiz)
        return quiz

    def process_results(self, quiz: Quiz) -> dict:
        """Analyse completed quiz, update performance, return recommendation."""
        if not quiz.is_complete:
            raise ValueError("Quiz is not complete yet.")

        score_pct = quiz.progress()["percentage"]

        for q in quiz.questions:
            self.performance.record_answer(
                topic      = quiz.topic,
                difficulty = quiz.difficulty,
                is_correct = q.is_correct or False,
            )

        self.performance.record_session(quiz.summary())

        old_diff = self.performance.current_difficulty
        new_diff = self._adjust_difficulty(old_diff, score_pct)
        self.performance.current_difficulty = new_diff

        logger.info(
            f"Results | score={score_pct}% | diff: {old_diff} → {new_diff}"
        )
        return self._build_recommendation(score_pct, old_diff, new_diff, quiz.topic)

    def next_quiz(self, num_questions: int = 5, override_topic: str = None) -> Quiz:
        """Generate next adaptive quiz, prioritising weak topics."""
        weak  = self.performance.weak_topics()
        topic = override_topic or (weak[0] if weak else self._last_topic)

        if weak and not override_topic:
            logger.info(f"Targeting weak topic: '{topic}'")

        return self.start_quiz(
            topic         = topic,
            question_type = self._last_type,
            num_questions = num_questions,
            language      = self._last_language,
        )

    # Seen-question persistence  

    def _register_seen(self, quiz: Quiz) -> None:
        """Add all question fingerprints from a quiz to the seen set."""
        for q in quiz.questions:
            self.seen_questions.add(q.fingerprint)

        # rolling window: drop oldest if over cap
        if len(self.seen_questions) > config.MAX_SEEN_QUESTIONS:
            overflow = len(self.seen_questions) - config.MAX_SEEN_QUESTIONS
            to_remove = list(self.seen_questions)[:overflow]
            for fp in to_remove:
                self.seen_questions.discard(fp)

        self._save_seen()

    def _load_seen(self) -> set[str]:
        path = config.SEEN_QUESTIONS_PATH
        if os.path.exists(path):
            try:
                with open(path) as f:
                    return set(json.load(f))
            except Exception:
                pass
        return set()

    def _save_seen(self) -> None:
        path = config.SEEN_QUESTIONS_PATH
        os.makedirs(os.path.dirname(path), exist_ok=True)
        try:
            with open(path, "w") as f:
                json.dump(list(self.seen_questions), f)
        except Exception as e:
            logger.warning(f"Could not save seen questions: {e}")

    # Difficulty logic 

    def _adjust_difficulty(self, current: str, score_pct: float) -> str:
        idx = DIFFICULTY_LADDER.index(current)
        if score_pct >= PROMOTE_THRESHOLD:
            return DIFFICULTY_LADDER[min(idx + 1, 2)]
        elif score_pct <= DEMOTE_THRESHOLD:
            return DIFFICULTY_LADDER[max(idx - 1, 0)]
        return current

    def _build_recommendation(
        self, score_pct: float, old_diff: str, new_diff: str, topic: str
    ) -> dict:
        promoted = new_diff != old_diff and DIFFICULTY_LADDER.index(new_diff) > DIFFICULTY_LADDER.index(old_diff)
        demoted  = new_diff != old_diff and not promoted

        if score_pct >= PROMOTE_THRESHOLD:
            message = (
                f"🎉 Excellent! {score_pct}% — moving up to **{new_diff}**!"
                if promoted
                else f"🏆 Perfect! {score_pct}% — you've mastered the hardest level!"
            )
        elif score_pct <= DEMOTE_THRESHOLD:
            message = (
                f"📚 {score_pct}% — stepping back to **{new_diff}** to reinforce basics."
                if demoted
                else f"💪 {score_pct}% — let's keep reviewing the fundamentals."
            )
        else:
            message = (
                f"👍 {score_pct}% — staying at **{new_diff}** to consolidate your knowledge."
            )

        weak_topics = self.performance.weak_topics()
        return {
            "message":         message,
            "score_pct":       score_pct,
            "old_difficulty":  old_diff,
            "next_difficulty": new_diff,
            "next_topic":      weak_topics[0] if weak_topics else topic,
            "should_repeat":   score_pct <= DEMOTE_THRESHOLD,
            "weak_topics":     weak_topics,
            "performance":     self.performance.summary(),
        }