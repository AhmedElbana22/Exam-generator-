from loguru import logger
from config import AppConfig

config = AppConfig()


class PromptBuilder:
    """Builds LLM prompts for quiz generation."""

    def __init__(self):
        self._context = ""
        self._question_type = "MCQ"
        self._difficulty = "medium"
        self._num_questions = config.DEFAULT_NUM_QUESTIONS
        self._language = "english"

    # Builder setters

    def set_context(self, context: str) -> "PromptBuilder":
        self._context = context.strip()
        return self

    def set_question_type(self, question_type: str) -> "PromptBuilder":
        if question_type not in config.QUESTION_TYPES:
            raise ValueError(
                f"Invalid question type '{question_type}'. "
                f"Allowed: {config.QUESTION_TYPES}"
            )
        self._question_type = question_type
        return self

    def set_difficulty(self, difficulty: str) -> "PromptBuilder":
        if difficulty not in config.DIFFICULTY_LEVELS:
            raise ValueError(
                f"Invalid difficulty '{difficulty}'. "
                f"Allowed: {config.DIFFICULTY_LEVELS}"
            )
        self._difficulty = difficulty
        return self

    def set_num_questions(self, n: int) -> "PromptBuilder":
        if not 1 <= n <= 20:
            raise ValueError("Number of questions must be between 1 and 20.")
        self._num_questions = n
        return self

    def set_language(self, language: str) -> "PromptBuilder":
        if language not in ("english", "arabic"):
            raise ValueError("Language must be 'english' or 'arabic'.")
        self._language = language
        return self

    # Build

    def build(self) -> tuple[str, str]:
        if not self._context:
            raise ValueError("Context is empty.")

        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt()

        logger.info(
            f"Prompt built | type={self._question_type} "
            f"difficulty={self._difficulty} "
            f"n={self._num_questions} "
            f"lang={self._language}"
        )

        return user_prompt, system_prompt

    # Internal helpers

    def _build_system_prompt(self) -> str:
        language_instruction = (
            "Respond in Arabic only."
            if self._language == "arabic"
            else "Respond in English only."
        )

        return f"""You are an expert educational assessment designer.

Generate questions strictly based on the provided context.
Do not use outside knowledge.

Rules:
- Generate exactly {self._num_questions} questions.
- Difficulty: {self._difficulty.upper()}
- {self._difficulty_guidance()}
- {language_instruction}
- Return valid JSON only.
- No explanations outside the JSON.
"""

    def _difficulty_guidance(self) -> str:
        guidance = {
            "easy": (
                "Focus on recall and basic definitions. Use simple language."
            ),
            "medium": (
                "Test understanding and application of concepts."
            ),
            "hard": (
                "Test analysis, comparison, and deeper reasoning."
            ),
        }
        return guidance[self._difficulty]

    def _build_user_prompt(self) -> str:
        builders = {
            "MCQ": self._mcq_prompt,
            "true_false": self._true_false_prompt,
            "short_answer": self._short_answer_prompt,
        }
        return builders[self._question_type]()

    def _mcq_prompt(self) -> str:
        return f"""Based only on the context below, generate {self._num_questions} multiple choice questions.

CONTEXT:
{self._context}

Return a JSON array:
[
  {{
    "question": "...",
    "options": {{
      "A": "...",
      "B": "...",
      "C": "...",
      "D": "..."
    }},
    "answer": "A",
    "explanation": "..."
  }}
]

Generate exactly {self._num_questions} questions. JSON only."""

    def _true_false_prompt(self) -> str:
        return f"""Based only on the context below, generate {self._num_questions} true/false questions.

CONTEXT:
{self._context}

Return a JSON array:
[
  {{
    "question": "...",
    "answer": "True",
    "explanation": "..."
  }}
]

Mix true and false answers. Generate exactly {self._num_questions}. JSON only."""

    def _short_answer_prompt(self) -> str:
        return f"""Based only on the context below, generate {self._num_questions} short answer questions.

CONTEXT:
{self._context}

Return a JSON array:
[
  {{
    "question": "...",
    "answer": "1–3 sentence answer.",
    "key_points": ["point 1", "point 2"]
  }}
]

Generate exactly {self._num_questions}. JSON only."""