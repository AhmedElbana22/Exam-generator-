from controller.quiz_controller import QuizController
from model.quiz_model import Quiz
from model.question_model import Question

SAMPLE_TEXT = """
Artificial intelligence is the simulation of human intelligence by machines.
Machine learning is a branch of AI where systems learn from data automatically.
Deep learning uses multi-layered neural networks to recognize patterns.
Natural language processing helps computers understand and generate human text.
Transformers are the architecture behind models like BERT and GPT.
Supervised learning uses labeled data to train models for prediction tasks.
Unsupervised learning finds hidden patterns in unlabeled data.
Reinforcement learning trains agents by rewarding correct actions.
"""


def test_load_text():
    qc = QuizController()
    count = qc.load_text(SAMPLE_TEXT)
    assert count > 0
    print(f"load_text — {count} chunks indexed")


def test_generate_mcq_quiz():
    qc = QuizController()
    qc.load_text(SAMPLE_TEXT)

    quiz = qc.generate_quiz(
        topic="machine learning and AI",
        question_type="MCQ",
        difficulty="easy",
        num_questions=3,
    )

    assert isinstance(quiz, Quiz)
    assert len(quiz.questions) > 0
    assert quiz.question_type == "MCQ"

    q = quiz.questions[0]
    assert isinstance(q, Question)
    assert q.options is not None
    assert q.answer in ("A", "B", "C", "D")
    print(f"MCQ quiz — {len(quiz.questions)} questions generated")
    print(f"   Sample: {q.question[:80]}...")


def test_generate_true_false_quiz():
    qc = QuizController()
    qc.load_text(SAMPLE_TEXT)

    quiz = qc.generate_quiz(
        topic="deep learning",
        question_type="true_false",
        difficulty="medium",
        num_questions=3,
    )

    assert len(quiz.questions) > 0
    assert quiz.questions[0].answer.lower() in ("true", "false")
    print(f"True/False quiz — {len(quiz.questions)} questions")


def test_quiz_answer_submission():
    qc = QuizController()
    qc.load_text(SAMPLE_TEXT)

    quiz = qc.generate_quiz(
        topic="AI and machine learning",
        question_type="MCQ",
        difficulty="easy",
        num_questions=2,
    )
 
    correct = quiz.questions[0].answer
    result = quiz.submit_answer(correct)

    assert quiz.current_index == 1
    assert quiz.score == 1
    assert result is True
    print(f"Answer submission — score: {quiz.score}/{len(quiz.questions)}")


def test_quiz_progress_and_summary():
    qc = QuizController()
    qc.load_text(SAMPLE_TEXT)

    quiz = qc.generate_quiz(
        topic="AI",
        question_type="MCQ",
        difficulty="easy",
        num_questions=2,
    )

    # answer all questions
    for q in quiz.questions:
        quiz.submit_answer(q.answer)

    assert quiz.is_complete is True
    summary = quiz.summary()
    assert summary["percentage"] == 100.0
    print(f"Quiz complete — score: {summary['score']}/{summary['total']} (100%)")