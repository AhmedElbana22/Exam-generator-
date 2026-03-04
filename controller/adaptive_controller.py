"""
The adaptive learning engine.
Watches user performance after every quiz session and decides:
  - Should difficulty go up, down, or stay?
  - Which topics need more practice?
  - What should the next quiz focus on?

Thresholds:
  - score >= 80% on current difficulty -> promote to harder
  - score <= 40% on current difficulty -> demote to easier
  - 40% < score < 80%                  -> stay at same difficulty
"""

from loguru import logger
from model.user_model import UserPerformance
from model.quiz_model import Quiz
from controller.quiz_controller import QuizController
from config import AppConfig

config = AppConfig()

# difficulty ladder — order matters
DIFFICULTY_LADDER = ["easy", "medium", "hard"]

# thresholds for promotion/demotion
PROMOTE_THRESHOLD = 80.0   # score% above this -> go harder
DEMOTE_THRESHOLD  = 40.0   # score% below this -> go easier


class AdaptiveController:

    def __init__(self):
        self.quiz_controller = QuizController()
        self.performance     = UserPerformance()
        self._last_topic     = ""
        self._last_type      = "MCQ"
        self._last_language  = "english"
        logger.info("AdaptiveController initialized")
    
    
    # Load 

    def load_text(self, text: str) -> int:
        """Load study material into RAG pipeline."""
        return self.quiz_controller.load_text(text)

    def load_pdf(self, pdf_path: str) -> int:
        """Load PDF into RAG pipeline."""
        return self.quiz_controller.load_pdf(pdf_path)
    
    # Start quiz

    def start_quiz(
        self,
        topic:         str,
        question_type: str = "MCQ",
        num_questions: int = 5,
        language:      str = "english",
        difficulty:    str = None,
    ) -> Quiz:
        """
        Generate a quiz at the current recommended difficulty.

        Args:
            topic:         Topic to quiz about
            question_type: 'MCQ', 'true_false', or 'short_answer'
            num_questions: How many questions
            language:      'english' or 'arabic'
            difficulty:    Override difficulty (optional — uses adaptive if None)

        Returns:
            A Quiz object ready for the UI
        """
        # use adaptive difficulty unless overridden
        difficulty = difficulty or self.performance.current_difficulty

        # remember for next_quiz()
        self._last_topic    = topic
        self._last_type     = question_type
        self._last_language = language

        logger.info(
            f"Starting adaptive quiz — topic='{topic}' | "
            f"difficulty={difficulty} | type={question_type}"
        )

        return self.quiz_controller.generate_quiz(
            topic=topic,
            question_type=question_type,
            difficulty=difficulty,
            num_questions=num_questions,
            language=language,
        )

    #process results

    def process_results(self, quiz: Quiz) -> dict: 
        """
        Analyze completed quiz results and update performance model.
        Decides next difficulty and next focus topic.

        Args:
            quiz: A completed Quiz object (is_complete must be True)

        Returns:
            Recommendation dict with:
              - message:          Human-readable feedback
              - next_difficulty:  Recommended next difficulty
              - next_topic:       Recommended next topic
              - should_repeat:    True if user should redo this topic
              - performance:      Full performance summary
        """
        if not quiz.is_complete:
            raise ValueError("Quiz is not complete yet!")

        score_pct = quiz.progress()["percentage"]
 
        for q in quiz.questions:
            self.performance.record_answer(
                topic=quiz.topic,
                difficulty=quiz.difficulty,
                is_correct=q.is_correct or False,
            )

        # record full session
        self.performance.record_session(quiz.summary()) 
 
        old_difficulty = self.performance.current_difficulty
        new_difficulty = self._adjust_difficulty(
            current=old_difficulty,
            score_pct=score_pct,
        )
        self.performance.current_difficulty = new_difficulty
 
        recommendation = self._build_recommendation(
            score_pct=score_pct,
            old_difficulty=old_difficulty,
            new_difficulty=new_difficulty,
            topic=quiz.topic,
        )

        logger.info(
            f"Results processed — score={score_pct}% | "
            f"difficulty: {old_difficulty} → {new_difficulty}"
        )
        return recommendation
    
    # Next quiz
    def next_quiz(
        self,
        num_questions: int = 5,
        override_topic: str = None,
    ) -> Quiz:
        """
        Generate the next adaptive quiz based on recommendation.
        Automatically targets weak topics if any exist.

        Args:
            num_questions:  How many questions
            override_topic: Force a specific topic (optional)

        Returns:
            Next Quiz object
        """
        # prioritize weak topics if any
        weak = self.performance.weak_topics()
        if override_topic:
            topic = override_topic
        elif weak:
            topic = weak[0]   # focus on worst topic first
            logger.info(f"Targeting weak topic: '{topic}'")
        else:
            topic = self._last_topic

        return self.start_quiz(
            topic=topic,
            question_type=self._last_type,
            num_questions=num_questions,
            language=self._last_language,
        )


    def _adjust_difficulty(
        self,
        current: str,
        score_pct: float,
    ) -> str:
        """
        Apply promotion/demotion logic.

        >= 80% -> promote (if not already hard)
        <= 40% -> demote  (if not already easy)
        else   -> stay
        """
        idx = DIFFICULTY_LADDER.index(current)

        if score_pct >= PROMOTE_THRESHOLD:
            new_idx = min(idx + 1, len(DIFFICULTY_LADDER) - 1)
        elif score_pct <= DEMOTE_THRESHOLD:
            new_idx = max(idx - 1, 0)
        else:
            new_idx = idx

        return DIFFICULTY_LADDER[new_idx]

    def _build_recommendation(
        self,
        score_pct:      float,
        old_difficulty: str,
        new_difficulty: str,
        topic:          str,
    ) -> dict:
        """Build human-readable recommendation from performance data."""

        # build feedback message
        if score_pct >= PROMOTE_THRESHOLD:
            if new_difficulty != old_difficulty:
                message = (
                    f"🎉 Excellent! {score_pct}% score. "
                    f"Moving up to {new_difficulty} difficulty!"
                )
            else:
                message = (
                    f"🏆 Perfect! {score_pct}% score. "
                    f"You've mastered the hardest level!"
                )
        elif score_pct <= DEMOTE_THRESHOLD:
            if new_difficulty != old_difficulty:
                message = (
                    f"📚 Keep practicing. {score_pct}% score. "
                    f"Stepping back to {new_difficulty} to strengthen basics."
                )
            else:
                message = (
                    f"💪 Don't give up! {score_pct}% score. "
                    f"Let's review the fundamentals again."
                )
        else:
            message = (
                f"👍 Good effort! {score_pct}% score. "
                f"Staying at {new_difficulty} difficulty to consolidate."
            )

        weak_topics   = self.performance.weak_topics()
        next_topic    = weak_topics[0] if weak_topics else topic
        should_repeat = score_pct <= DEMOTE_THRESHOLD

        return {
            "message":          message,
            "score_pct":        score_pct,
            "old_difficulty":   old_difficulty,
            "next_difficulty":  new_difficulty,
            "next_topic":       next_topic,
            "should_repeat":    should_repeat,
            "weak_topics":      weak_topics,
            "performance":      self.performance.summary(),
        }