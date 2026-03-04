from model.user_model import UserPerformance
from model.quiz_model import Quiz
from model.question_model import Question
from controller.adaptive_controller import AdaptiveController, DIFFICULTY_LADDER
import pytest 

def _make_completed_quiz(score: int, total: int, difficulty: str = "medium") -> Quiz:
    """Helper — build a fake completed quiz with given score."""
    questions = []
    for i in range(total):
        q = Question(
            question_id=i,
            question_type="MCQ",
            question=f"Question {i}?",
            answer="A",
            options={"A": "correct", "B": "wrong", "C": "wrong", "D": "wrong"},
        )
        q.user_answer = "A" if i < score else "B"
        q.is_correct  = i < score
        questions.append(q)

    quiz = Quiz(
        quiz_id=f"test_{difficulty}",
        topic="AI basics",
        difficulty=difficulty,
        question_type="MCQ",
        questions=questions,
        current_index=total,
        score=score,
        is_complete=True,
    )
    return quiz


def test_difficulty_promotes_on_high_score():
    """80%+ score should promote difficulty."""
    perf = UserPerformance(current_difficulty="easy")
    ac = AdaptiveController()
    ac.performance = perf

    quiz = _make_completed_quiz(score=5, total=5, difficulty="easy")  # 100%
    result = ac.process_results(quiz)

    assert result["next_difficulty"] == "medium"
    print(f"Promoted easy -> medium on 100% score")


def test_difficulty_demotes_on_low_score():
    """40% or below should demote difficulty."""
    perf = UserPerformance(current_difficulty="hard")
    ac = AdaptiveController()
    ac.performance = perf

    quiz = _make_completed_quiz(score=1, total=5, difficulty="hard")  # 20%
    result = ac.process_results(quiz)

    assert result["next_difficulty"] == "medium"
    print(f"Demoted hard -> medium on 20% score")


def test_difficulty_stays_on_medium_score():
    """41-79% score should keep same difficulty."""
    perf = UserPerformance(current_difficulty="medium")
    ac = AdaptiveController()
    ac.performance = perf

    quiz = _make_completed_quiz(score=3, total=5, difficulty="medium")  # 60%
    result = ac.process_results(quiz)

    assert result["next_difficulty"] == "medium"
    print(f"Stayed at medium on 60% score")


def test_no_promotion_beyond_hard():
    """Should not promote beyond hard."""
    perf = UserPerformance(current_difficulty="hard")
    ac = AdaptiveController()
    ac.performance = perf

    quiz = _make_completed_quiz(score=5, total=5, difficulty="hard")  # 100%
    result = ac.process_results(quiz)

    assert result["next_difficulty"] == "hard"
    print(f"Stayed at hard (already max difficulty)")


def test_weak_topics_detected():
    """Topics with < 60% accuracy should appear in weak_topics."""
    perf = UserPerformance() 
    for _ in range(5):
        perf.record_answer("neural networks", "medium", False)
    for _ in range(5):
        perf.record_answer("python basics", "medium", True)

    weak = perf.weak_topics()
    assert "neural networks" in weak
    assert "python basics" not in weak
    print(f"Weak topics detected: {weak}")


def test_recommendation_message_contains_score():
    """Recommendation message should mention the score."""
    ac = AdaptiveController()
    quiz = _make_completed_quiz(score=4, total=5, difficulty="medium")  # 80%
    result = ac.process_results(quiz)

    assert "80.0%" in result["message"]
    assert "message" in result
    assert "next_topic" in result
    print(f"Recommendation: {result['message']}")