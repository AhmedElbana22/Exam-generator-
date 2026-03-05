import pytest
from controller.evaluation_controller import (
    EvaluationController,
    QuestionScore,
    AggregateScore,
    _interpret_bleu,
    _interpret_rouge,
)


@pytest.fixture
def evaluator():
    return EvaluationController()


@pytest.fixture
def sample_refs():
    return [
        {"question": "What is artificial intelligence?",
         "answer":   "A simulation of human intelligence by machines"},
        {"question": "What is machine learning?",
         "answer":   "A subset of AI that learns from data"},
        {"question": "What is natural language processing?",
         "answer":   "Processing and understanding of human language"},
    ]


@pytest.fixture
def sample_hyps_good():
    return [
        {"question": "What is artificial intelligence?",
         "answer":   "A simulation of human intelligence by machines"},
        {"question": "What does machine learning involve?",
         "answer":   "A branch of AI that learns patterns from data"},
        {"question": "What is natural language processing?",
         "answer":   "Processing and analysis of human language by computers"},
    ]


@pytest.fixture
def sample_hyps_poor():
    return [
        {"question": "What is photosynthesis?",
         "answer":   "Conversion of sunlight to energy"},
        {"question": "Who wrote Hamlet?",
         "answer":   "William Shakespeare"},
        {"question": "What is the speed of light?",
         "answer":   "299,792,458 metres per second"},
    ]


class TestBLEU:

    def test_identical_strings(self, evaluator):
        score = evaluator.bleu_score(
            "what is machine learning",
            "what is machine learning",
        )
        assert score > 0.9

    def test_empty_hypothesis(self, evaluator):
        assert evaluator.bleu_score("what is machine learning", "") == 0.0

    def test_empty_reference(self, evaluator):
        assert evaluator.bleu_score("", "what is machine learning") == 0.0

    def test_both_empty(self, evaluator):
        assert evaluator.bleu_score("", "") == 0.0

    def test_partial_overlap(self, evaluator):
        score = evaluator.bleu_score(
            "what is machine learning",
            "what is deep learning",
        )
        assert 0.0 < score < 1.0

    def test_single_word(self, evaluator):
        score = evaluator.bleu_score("learning", "learning")
        assert isinstance(score, float)
        assert score >= 0.0

    def test_completely_different(self, evaluator):
        score = evaluator.bleu_score(
            "what is machine learning",
            "photosynthesis occurs in chloroplasts",
        )
        assert score < 0.2

    def test_returns_float(self, evaluator):
        score = evaluator.bleu_score("hello world", "hello there")
        assert isinstance(score, float)

    def test_score_in_range(self, evaluator):
        score = evaluator.bleu_score(
            "the quick brown fox",
            "the slow brown dog",
        )
        assert 0.0 <= score <= 1.0


class TestROUGE:

    def test_identical_strings(self, evaluator):
        scores = evaluator.rouge_scores(
            "what is machine learning",
            "what is machine learning",
        )
        assert scores["rouge1"] > 0.9
        assert scores["rouge2"] > 0.9
        assert scores["rougeL"] > 0.9

    def test_empty_hypothesis(self, evaluator):
        scores = evaluator.rouge_scores("what is machine learning", "")
        assert scores["rouge1"] == 0.0
        assert scores["rouge2"] == 0.0
        assert scores["rougeL"] == 0.0

    def test_empty_reference(self, evaluator):
        scores = evaluator.rouge_scores("", "what is machine learning")
        assert scores["rouge1"] == 0.0
        assert scores["rouge2"] == 0.0
        assert scores["rougeL"] == 0.0

    def test_returns_all_keys(self, evaluator):
        scores = evaluator.rouge_scores("hello world", "hello")
        assert set(scores.keys()) == {"rouge1", "rouge2", "rougeL"}

    def test_all_scores_in_range(self, evaluator):
        scores = evaluator.rouge_scores(
            "natural language processing is a branch of AI",
            "NLP involves processing human language",
        )
        for key, val in scores.items():
            assert 0.0 <= val <= 1.0, f"{key} out of range: {val}"

    def test_rouge1_gte_rouge2(self, evaluator):
        scores = evaluator.rouge_scores(
            "machine learning is a subset of artificial intelligence",
            "machine learning involves training models on data",
        )
        assert scores["rouge1"] >= scores["rouge2"]


class TestEvaluateQuestion:

    def test_returns_question_score(self, evaluator):
        result = evaluator.evaluate_question(
            reference_question = "What is AI?",
            generated_question = "What is artificial intelligence?",
            reference_answer   = "Simulation of human intelligence",
            generated_answer   = "Mimicking human cognitive functions",
        )
        assert isinstance(result, QuestionScore)

    def test_all_fields_present(self, evaluator):
        result = evaluator.evaluate_question(
            reference_question = "What is machine learning?",
            generated_question = "What does machine learning involve?",
            reference_answer   = "A subset of AI",
            generated_answer   = "A branch of artificial intelligence",
        )
        metric_fields = [
            "question_bleu", "question_rouge1", "question_rouge2", "question_rougeL",
            "answer_bleu",   "answer_rouge1",   "answer_rouge2",   "answer_rougeL",
        ]
        for f in metric_fields:
            val = getattr(result, f)
            assert isinstance(val, float)
            assert 0.0 <= val <= 1.0

    def test_stored_in_history(self, evaluator):
        assert len(evaluator.history) == 0
        evaluator.evaluate_question("Q?", "Q?", "A", "A")
        assert len(evaluator.history) == 1

    def test_identical_pair_high_scores(self, evaluator):
        result = evaluator.evaluate_question(
            "What is deep learning?", "What is deep learning?",
            "A subset of machine learning", "A subset of machine learning",
        )
        assert result.question_bleu   > 0.9
        assert result.question_rouge1 > 0.9
        assert result.answer_bleu     > 0.9
        assert result.answer_rouge1   > 0.9

    def test_to_dict_returns_dict(self, evaluator):
        result = evaluator.evaluate_question("Q?", "Q?", "A", "A")
        d = result.to_dict()
        assert isinstance(d, dict)
        assert "question_bleu" in d


class TestEvaluateBatch:

    def test_correct_structure(self, evaluator, sample_refs, sample_hyps_good):
        result = evaluator.evaluate_batch(sample_refs, sample_hyps_good)
        assert "per_pair"  in result
        assert "aggregate" in result
        assert "count"     in result

    def test_count_matches_input(self, evaluator, sample_refs, sample_hyps_good):
        result = evaluator.evaluate_batch(sample_refs, sample_hyps_good)
        assert result["count"] == len(sample_refs)

    def test_per_pair_length(self, evaluator, sample_refs, sample_hyps_good):
        result = evaluator.evaluate_batch(sample_refs, sample_hyps_good)
        assert len(result["per_pair"]) == len(sample_refs)

    def test_good_hyps_higher_than_poor(
        self, evaluator, sample_refs, sample_hyps_good, sample_hyps_poor
    ):
        good = evaluator.evaluate_batch(sample_refs, sample_hyps_good)
        evaluator.clear()
        poor = evaluator.evaluate_batch(sample_refs, sample_hyps_poor)
        assert (
            good["aggregate"]["question_rouge1"] >
            poor["aggregate"]["question_rouge1"]
        )

    def test_length_mismatch_raises(self, evaluator, sample_refs):
        with pytest.raises(ValueError, match="Length mismatch"):
            evaluator.evaluate_batch(sample_refs, sample_refs[:2])

    def test_empty_input_raises(self, evaluator):
        with pytest.raises(ValueError):
            evaluator.evaluate_batch([], [])

    def test_aggregate_values_in_range(self, evaluator, sample_refs, sample_hyps_good):
        result    = evaluator.evaluate_batch(sample_refs, sample_hyps_good)
        aggregate = result["aggregate"]
        for key, val in aggregate.items():
            if key != "count":
                assert 0.0 <= val <= 1.0, f"{key} out of range: {val}"

    def test_aggregate_math_correctness(self, evaluator):
        refs = [
            {"question": "What is AI?", "answer": "Artificial intelligence"},
            {"question": "What is AI?", "answer": "Artificial intelligence"},
        ]
        hyps = [
            {"question": "What is AI?", "answer": "Artificial intelligence"},
            {"question": "What is AI?", "answer": "Artificial intelligence"},
        ]
        result = evaluator.evaluate_batch(refs, hyps)

        pair_0_bleu = result["per_pair"][0]["question_bleu"]
        agg_bleu    = result["aggregate"]["question_bleu"]

        assert agg_bleu == pair_0_bleu
        assert result["count"] == 2
        assert agg_bleu > 0.0

    def test_aggregate_high_score_on_long_identical_strings(self, evaluator):
        long_q = "What is the role of transformer architecture in natural language processing"
        long_a = "Transformers use self-attention mechanisms to process sequences in parallel"

        refs = [{"question": long_q, "answer": long_a}]
        hyps = [{"question": long_q, "answer": long_a}]

        result = evaluator.evaluate_batch(refs, hyps)

        assert result["aggregate"]["question_bleu"] > 0.9
        assert result["aggregate"]["answer_bleu"]   > 0.9


class TestReport:

    def test_returns_string(self, evaluator):
        agg = AggregateScore(
            count=3,
            question_bleu=0.45,   question_rouge1=0.55,
            question_rouge2=0.30, question_rougeL=0.50,
            answer_bleu=0.40,     answer_rouge1=0.52,
            answer_rouge2=0.28,   answer_rougeL=0.48,
        )
        assert isinstance(evaluator.report(agg), str)

    def test_report_contains_keywords(self, evaluator):
        agg = {
            "question_bleu": 0.4,  "question_rouge1": 0.5,
            "question_rouge2": 0.3,"question_rougeL": 0.5,
            "answer_bleu": 0.4,    "answer_rouge1": 0.5,
            "answer_rouge2": 0.3,  "answer_rougeL": 0.5,
        }
        report = evaluator.report(agg)
        for keyword in ["BLEU", "ROUGE", "Question", "Answer"]:
            assert keyword in report

    def test_report_contains_interpretation(self, evaluator):
        agg = AggregateScore(
            count=1,
            question_bleu=0.65,   question_rouge1=0.65,
            question_rouge2=0.65, question_rougeL=0.65,
            answer_bleu=0.65,     answer_rouge1=0.65,
            answer_rouge2=0.65,   answer_rougeL=0.65,
        )
        assert "Excellent" in evaluator.report(agg)


class TestHistoryAndClear:

    def test_history_grows(self, evaluator):
        for i in range(3):
            evaluator.evaluate_question(f"Q{i}?", f"Q{i}?", f"A{i}", f"A{i}")
        assert len(evaluator.history) == 3

    def test_clear_resets_history(self, evaluator):
        evaluator.evaluate_question("Q?", "Q?", "A", "A")
        evaluator.clear()
        assert len(evaluator.history) == 0

    def test_history_is_copy(self, evaluator):
        evaluator.evaluate_question("Q?", "Q?", "A", "A")
        h = evaluator.history
        h.clear()
        assert len(evaluator.history) == 1


class TestInterpretation:

    def test_bleu_excellent(self):
        assert _interpret_bleu(0.65) == "Excellent"

    def test_bleu_good(self):
        assert _interpret_bleu(0.45) == "Good"

    def test_bleu_fair(self):
        assert _interpret_bleu(0.25) == "Fair"

    def test_bleu_poor(self):
        assert _interpret_bleu(0.05) == "Poor"

    def test_rouge_excellent(self):
        assert _interpret_rouge(0.65) == "Excellent"

    def test_rouge_poor(self):
        assert _interpret_rouge(0.05) == "Poor"


def test_repr(evaluator):
    assert "EvaluationController" in repr(evaluator)
    assert "0 pairs" in repr(evaluator)