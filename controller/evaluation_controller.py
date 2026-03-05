from __future__ import annotations

import re
from dataclasses import dataclass, field, asdict
from typing import Optional

try:
    from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
    import nltk
    try:
        nltk.data.find("tokenizers/punkt")
    except LookupError:
        nltk.download("punkt", quiet=True)
    NLTK_OK = True
except ImportError:
    NLTK_OK = False

try:
    from rouge_score import rouge_scorer as rouge_lib
    ROUGE_OK = True
except ImportError:
    ROUGE_OK = False


_BLEU_THRESHOLDS  = [(0.6, "Excellent"), (0.4, "Good"), (0.2, "Fair"), (0.0, "Poor")]
_ROUGE_THRESHOLDS = [(0.6, "Excellent"), (0.5, "Good"), (0.3, "Fair"), (0.0, "Poor")]


def _interpret_bleu(score: float) -> str:
    for threshold, label in _BLEU_THRESHOLDS:
        if score >= threshold:
            return label
    return "Poor"


def _interpret_rouge(score: float) -> str:
    for threshold, label in _ROUGE_THRESHOLDS:
        if score >= threshold:
            return label
    return "Poor"


@dataclass
class QuestionScore:
    reference_question : str
    generated_question : str
    reference_answer   : str
    generated_answer   : str
    question_bleu      : float = 0.0
    question_rouge1    : float = 0.0
    question_rouge2    : float = 0.0
    question_rougeL    : float = 0.0
    answer_bleu        : float = 0.0
    answer_rouge1      : float = 0.0
    answer_rouge2      : float = 0.0
    answer_rougeL      : float = 0.0

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class AggregateScore:
    count           : int   = 0
    question_bleu   : float = 0.0
    question_rouge1 : float = 0.0
    question_rouge2 : float = 0.0
    question_rougeL : float = 0.0
    answer_bleu     : float = 0.0
    answer_rouge1   : float = 0.0
    answer_rouge2   : float = 0.0
    answer_rougeL   : float = 0.0

    def to_dict(self) -> dict:
        return asdict(self)


class EvaluationController:

    def __init__(self, use_stemmer: bool = True) -> None:
        if not NLTK_OK:
            raise ImportError("nltk not installed. Run: pip install nltk")
        if not ROUGE_OK:
            raise ImportError("rouge-score not installed. Run: pip install rouge-score")

        self._rouge_scorer = rouge_lib.RougeScorer(
            ["rouge1", "rouge2", "rougeL"],
            use_stemmer=use_stemmer,
        )
        self._smoothing = SmoothingFunction().method1
        self._history   : list[QuestionScore] = []

    @property
    def history(self) -> list[QuestionScore]:
        return list(self._history)

    def bleu_score(self, reference: str, hypothesis: str) -> float:
        ref_tokens = self._tokenize(reference)
        hyp_tokens = self._tokenize(hypothesis)

        if not ref_tokens or not hyp_tokens:
            return 0.0

        return round(
            float(sentence_bleu(
                [ref_tokens],
                hyp_tokens,
                smoothing_function=self._smoothing,
            )),
            4,
        )

    def rouge_scores(self, reference: str, hypothesis: str) -> dict[str, float]:
        if not reference.strip() or not hypothesis.strip():
            return {"rouge1": 0.0, "rouge2": 0.0, "rougeL": 0.0}

        raw = self._rouge_scorer.score(reference, hypothesis)

        return {
            "rouge1": round(raw["rouge1"].fmeasure, 4),
            "rouge2": round(raw["rouge2"].fmeasure, 4),
            "rougeL": round(raw["rougeL"].fmeasure, 4),
        }

    def evaluate_question(
        self,
        reference_question : str,
        generated_question : str,
        reference_answer   : str,
        generated_answer   : str,
    ) -> QuestionScore:
        q_bleu  = self.bleu_score(reference_question, generated_question)
        q_rouge = self.rouge_scores(reference_question, generated_question)
        a_bleu  = self.bleu_score(reference_answer, generated_answer)
        a_rouge = self.rouge_scores(reference_answer, generated_answer)

        score = QuestionScore(
            reference_question = reference_question,
            generated_question = generated_question,
            reference_answer   = reference_answer,
            generated_answer   = generated_answer,
            question_bleu      = q_bleu,
            question_rouge1    = q_rouge["rouge1"],
            question_rouge2    = q_rouge["rouge2"],
            question_rougeL    = q_rouge["rougeL"],
            answer_bleu        = a_bleu,
            answer_rouge1      = a_rouge["rouge1"],
            answer_rouge2      = a_rouge["rouge2"],
            answer_rougeL      = a_rouge["rougeL"],
        )

        self._history.append(score)
        return score

    def evaluate_batch(
        self,
        references : list[dict],
        hypotheses : list[dict],
    ) -> dict:
        if not references or not hypotheses:
            raise ValueError("references and hypotheses must not be empty")

        if len(references) != len(hypotheses):
            raise ValueError(
                f"Length mismatch: {len(references)} references "
                f"vs {len(hypotheses)} hypotheses"
            )

        scores: list[QuestionScore] = []

        for ref, hyp in zip(references, hypotheses):
            score = self.evaluate_question(
                reference_question = ref.get("question", ""),
                generated_question = hyp.get("question", ""),
                reference_answer   = ref.get("answer",   ""),
                generated_answer   = hyp.get("answer",   ""),
            )
            scores.append(score)

        aggregate = self._aggregate(scores)

        return {
            "per_pair"  : [s.to_dict() for s in scores],
            "aggregate" : aggregate.to_dict(),
            "count"     : len(scores),
        }

    def evaluate_generated_questions(
        self,
        reference_pairs : list[dict],
        generated_pairs : list[dict],
    ) -> dict:
        return self.evaluate_batch(reference_pairs, generated_pairs)

    def _aggregate(self, scores: list[QuestionScore]) -> AggregateScore:
        if not scores:
            return AggregateScore()

        n = len(scores)
        keys = [
            "question_bleu", "question_rouge1", "question_rouge2", "question_rougeL",
            "answer_bleu",   "answer_rouge1",   "answer_rouge2",   "answer_rougeL",
        ]

        agg = AggregateScore(count=n)
        for key in keys:
            setattr(agg, key, round(sum(getattr(s, key) for s in scores) / n, 4))

        return agg

    def report(self, aggregate: dict | AggregateScore) -> str:
        agg = aggregate.to_dict() if isinstance(aggregate, AggregateScore) else aggregate

        def _g(key: str) -> float:
            return agg.get(key, 0.0)

        lines = [
            "=" * 55,
            "  📊 ImtiQan — Evaluation Report",
            "=" * 55,
            "",
            f"  Evaluated pairs : {agg.get('count', 'N/A')}",
            "",
            "  🔵 Question Quality",
            f"     BLEU    : {_g('question_bleu'):.4f}  [{_interpret_bleu(_g('question_bleu'))}]",
            f"     ROUGE-1 : {_g('question_rouge1'):.4f}  [{_interpret_rouge(_g('question_rouge1'))}]",
            f"     ROUGE-2 : {_g('question_rouge2'):.4f}  [{_interpret_rouge(_g('question_rouge2'))}]",
            f"     ROUGE-L : {_g('question_rougeL'):.4f}  [{_interpret_rouge(_g('question_rougeL'))}]",
            "",
            "  🟢 Answer Quality",
            f"     BLEU    : {_g('answer_bleu'):.4f}  [{_interpret_bleu(_g('answer_bleu'))}]",
            f"     ROUGE-1 : {_g('answer_rouge1'):.4f}  [{_interpret_rouge(_g('answer_rouge1'))}]",
            f"     ROUGE-2 : {_g('answer_rouge2'):.4f}  [{_interpret_rouge(_g('answer_rouge2'))}]",
            f"     ROUGE-L : {_g('answer_rougeL'):.4f}  [{_interpret_rouge(_g('answer_rougeL'))}]",
            "",
            "  📈 Score Guide",
            "     BLEU  ≥ 0.6 → Excellent  |  ≥ 0.4 → Good",
            "     ROUGE ≥ 0.6 → Excellent  |  ≥ 0.5 → Good",
            "=" * 55,
        ]

        return "\n".join(lines)

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        text = text.lower().strip()
        text = re.sub(r"[^\w\s]", "", text)
        return text.split()

    def clear(self) -> None:
        self._history.clear()

    def __repr__(self) -> str:
        return f"EvaluationController(evaluated={len(self._history)} pairs)"