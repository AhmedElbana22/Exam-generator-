"""
PromptBuilder with full Bloom's Taxonomy difficulty enforcement.

more Changes 
    - Each difficulty maps to a Bloom's level with:
        * mandatory cognitive verbs in question stems
        * forbidden simple patterns (What is / Define / True that)
        * example question structures the LLM must follow
        * explicit cognitive operation descriptions
    - Seen-question block improved: injects both text AND fingerprints
    - Context cap respected before building
"""

import random
from loguru import logger
from config import AppConfig

config = AppConfig()

# Bloom's Taxonomy configuration 

_BLOOMS = {
    "easy": {
        "level":       "Level 1–2: Remember & Understand",
        "description": (
            "Questions test basic recall and comprehension. "
            "The student must identify, recall, define, or recognise a fact "
            "directly stated in the material."
        ),
        "stem_verbs":  ["What is", "Which of the following", "Define", "Identify",
                        "Who", "When", "Where", "List", "Name", "State"],
        "mcq_pattern": (
            "One correct answer is a direct fact from the text. "
            "Distractors are plausible but clearly wrong to someone who read the material."
        ),
        "tf_pattern":  (
            "Statements are direct facts from the text, either stated exactly or clearly negated."
        ),
        "sa_pattern":  (
            "Answer is 1 sentence, directly quoting or closely paraphrasing the material."
        ),
        "forbidden":   (
            "Do NOT ask questions that require reasoning, comparison, or inference. "
            "Do NOT use 'Why', 'How does', 'Compare', 'Evaluate', 'Analyze'."
        ),
    },

    "medium": {
        "level":       "Level 3–4: Apply & Analyze",
        "description": (
            "Questions test whether the student can apply concepts to scenarios "
            "or analyze how/why something works. "
            "Questions go beyond recall — they require understanding cause, effect, "
            "mechanism, or application to a new example."
        ),
        "stem_verbs":  ["How does", "Why does", "What would happen if", "Which best explains",
                        "What is the effect of", "How is X related to Y",
                        "What is the main reason", "Which scenario demonstrates"],
        "mcq_pattern": (
            "Correct answer requires understanding a mechanism or cause-effect. "
            "All 4 options must be plausible — wrong options should be common misconceptions."
        ),
        "tf_pattern":  (
            "Statements describe a relationship, mechanism, or implication that "
            "requires understanding, not just recall."
        ),
        "sa_pattern":  (
            "Answer is 2–3 sentences explaining a mechanism, cause, or application. "
            "Key points must include a reason or explanation, not just a definition."
        ),
        "forbidden":   (
            "Do NOT ask questions whose answer is a single term or direct quote. "
            "Do NOT use 'What is', 'Define', 'Name', 'List'."
        ),
    },

    "hard": {
        "level":       "Level 5–6: Evaluate & Create",
        "description": (
            "Questions test critical thinking: comparing approaches, evaluating tradeoffs, "
            "identifying limitations, reasoning about edge cases, or synthesizing "
            "multiple concepts from the material into a conclusion. "
            "These require multi-step reasoning — no single-sentence answers."
        ),
        "stem_verbs":  ["Compare and contrast", "Evaluate the claim that",
                        "What is the primary limitation of", "Which of the following best critiques",
                        "Under what conditions would", "What would be the consequence if",
                        "Analyze the tradeoff between", "Which conclusion can be drawn",
                        "Synthesize", "Justify why"],
        "mcq_pattern": (
            "Correct answer requires multi-step reasoning or evaluating a tradeoff. "
            "All 4 options must be sophisticated — a student who only memorized facts "
            "will likely choose a wrong option. "
            "Wrong options should represent partial understanding or common advanced misconceptions."
        ),
        "tf_pattern":  (
            "Statements involve nuanced claims about limitations, edge cases, or synthesis. "
            "A student who only knows surface facts will get these wrong."
        ),
        "sa_pattern":  (
            "Answer is 3–5 sentences involving comparison, evaluation, or synthesis. "
            "Key points must include a tradeoff, limitation, or conditional reasoning."
        ),
        "forbidden":   (
            "Do NOT ask questions answerable by simple recall. "
            "Do NOT use 'What is', 'Define', 'Who', 'When', 'Name', 'List', 'State'. "
            "Every question must require reasoning across at least 2 concepts."
        ),
    },
}


class PromptBuilder:
    """
    Builds LLM prompts with Bloom's Taxonomy cognitive level enforcement.
    """

    def __init__(self):
        self._context        = ""
        self._question_type  = "MCQ"
        self._difficulty     = "medium"
        self._num_questions  = config.DEFAULT_NUM_QUESTIONS
        self._language       = "english"
        self._seen_questions: list[str] = []

    # Setters  
    def set_context(self, context: str) -> "PromptBuilder":
        trimmed = context.strip()
        if len(trimmed) > config.MAX_CONTEXT_CHARS:
            trimmed = trimmed[:config.MAX_CONTEXT_CHARS]
            logger.debug(f"Context capped at {config.MAX_CONTEXT_CHARS} chars")
        self._context = trimmed
        return self

    def set_question_type(self, qtype: str) -> "PromptBuilder":
        if qtype not in config.QUESTION_TYPES:
            raise ValueError(f"Invalid type '{qtype}'. Allowed: {config.QUESTION_TYPES}")
        self._question_type = qtype
        return self

    def set_difficulty(self, difficulty: str) -> "PromptBuilder":
        if difficulty not in config.DIFFICULTY_LEVELS:
            raise ValueError(f"Invalid difficulty '{difficulty}'.")
        self._difficulty = difficulty
        return self

    def set_num_questions(self, n: int) -> "PromptBuilder":
        if not 1 <= n <= config.MAX_NUM_QUESTIONS:
            raise ValueError(f"n must be 1–{config.MAX_NUM_QUESTIONS}")
        self._num_questions = n
        return self

    def set_language(self, language: str) -> "PromptBuilder":
        if language not in ("english", "arabic"):
            raise ValueError("Language must be 'english' or 'arabic'.")
        self._language = language
        return self

    def set_seen_questions(self, seen: list[str]) -> "PromptBuilder":
        self._seen_questions = seen[:20]
        return self

    # Build 

    def build(self) -> tuple[str, str]:
        """Returns (user_prompt, system_prompt)."""
        if not self._context:
            raise ValueError("Context is empty — call set_context() first.")

        system_prompt = self._build_system_prompt()
        user_prompt   = self._build_user_prompt()

        logger.info(
            f"Prompt built | type={self._question_type} "
            f"diff={self._difficulty} n={self._num_questions} lang={self._language}"
        )
        return user_prompt, system_prompt

    def build_for_type(self, question_type: str, n: int) -> tuple[str, str]:
        """Build prompt for a specific type — used by mixed quiz generation."""
        return (
            PromptBuilder()
            .set_context(self._context)
            .set_question_type(question_type)
            .set_difficulty(self._difficulty)
            .set_num_questions(n)
            .set_language(self._language)
            .set_seen_questions(self._seen_questions)
            .build()
        )

    # System prompt with Bloom's taxonomy 

    def _build_system_prompt(self) -> str:
        bloom  = _BLOOMS[self._difficulty]
        verbs  = ", ".join(bloom["stem_verbs"][:6])

        # language block — stronger enforcement  
        if self._language == "arabic":
            lang_block = (
                "━━━ CRITICAL LANGUAGE RULE ━━━\n"
                "You MUST write EVERY part of your response in Arabic.\n"
                "This includes: question text, all options (A/B/C/D), "
                "the answer field, and the explanation field.\n"
                "The study material may be in English — that is fine.\n"
                "Your OUTPUT must be 100% Arabic regardless.\n"
                "Do NOT mix languages. Do NOT write any English word in the output.\n"
                "النص المرجعي قد يكون بالإنجليزية، لكن إجاباتك يجب أن تكون بالعربية فقط."
            )
        else:
            lang_block = (
                "━━━ LANGUAGE ━━━\n"
                "All output must be in English only."
            )

        return (
            f"You are an expert educational assessment designer specialized in "
            f"Bloom's Taxonomy-aligned question generation.\n\n"

            f"━━━ COGNITIVE LEVEL ━━━\n"
            f"{bloom['level']}\n"
            f"{bloom['description']}\n\n"

            f"━━━ QUESTION STEM REQUIREMENTS ━━━\n"
            f"Questions MUST begin with or center on these cognitive verbs:\n"
            f"{verbs} (or similar {self._difficulty}-level stems).\n\n"

            f"━━━ STRICT PROHIBITIONS ━━━\n"
            f"{bloom['forbidden']}\n\n"

            f"{lang_block}\n\n"

            f"━━━ FORMAT REQUIREMENTS ━━━\n"
            f"- Generate EXACTLY {self._num_questions} questions.\n"
            f"- Base questions STRICTLY on the provided context. Zero outside knowledge.\n"
            f"- Every question must have one unambiguous correct answer.\n"
            f"- Every question must have a 1–2 sentence explanation referencing the context.\n"
            f"- Return ONLY a valid JSON array. No markdown, no prose, no code fences."
        )

    # User prompt (type-specific with Bloom's pattern)

    def _build_user_prompt(self) -> str:
        if self._question_type == "mixed":
            return self._mcq_prompt()   # handled at controller level
        builders = {
            "MCQ":          self._mcq_prompt,
            "true_false":   self._tf_prompt,
            "short_answer": self._sa_prompt,
        }
        return builders[self._question_type]()

    def _seen_block(self) -> str:
        if not self._seen_questions:
            return ""
        items = "\n".join(f"  - {q}" for q in self._seen_questions)
        return (
            f"\n\n━━━ PREVIOUSLY ASKED — DO NOT REPEAT OR PARAPHRASE ━━━\n"
            f"These questions have already been asked. Do not ask them again "
            f"in any form, even with different wording:\n{items}"
        )
    
    def _lang_reminder(self) -> str:
        """Short inline reminder injected into every user prompt."""
        if self._language == "arabic":
            return (
                "\n\nتذكير: اكتب جميع الأسئلة والخيارات والإجابات والشرح باللغة العربية فقط."
                "\nREMINDER: All questions, options, answers, and explanations MUST be in Arabic."
            )
        return ""
    
    def _mcq_prompt(self) -> str:
        bloom = _BLOOMS[self._difficulty]
        return (
            f"Generate {self._num_questions} multiple-choice questions "
            f"at Bloom's {self._difficulty} level.\n\n"

            f"MCQ PATTERN FOR THIS LEVEL:\n{bloom['mcq_pattern']}\n\n"

            f"CONTEXT:\n{self._context}"
            f"{self._seen_block()}\n\n"
            f"{self._lang_reminder()}\n\n"

            f"Return a JSON array — exactly {self._num_questions} items:\n"
            f"[\n"
            f"  {{\n"
            f'    "question": "A {self._difficulty}-level question stem...",\n'
            f'    "options": {{\n'
            f'      "A": "...", "B": "...", "C": "...", "D": "..."\n'
            f'    }},\n'
            f'    "answer": "A",\n'
            f'    "explanation": "Explanation referencing the context..."\n'
            f"  }}\n"
            f"]\n\n"
            f"JSON only. No extra text."
        )

    def _tf_prompt(self) -> str:
        bloom = _BLOOMS[self._difficulty]
        return (
            f"Generate {self._num_questions} true/false questions "
            f"at Bloom's {self._difficulty} level.\n\n"

            f"T/F PATTERN FOR THIS LEVEL:\n{bloom['tf_pattern']}\n\n"

            f"CONTEXT:\n{self._context}"
            f"{self._seen_block()}\n\n"
            f"{self._lang_reminder()}\n\n"

            f"Ensure a balanced True/False split.\n\n"
            f"Return a JSON array — exactly {self._num_questions} items:\n"
            f"[\n"
            f"  {{\n"
            f'    "question": "A {self._difficulty}-level statement...",\n'
            f'    "answer": "True",\n'
            f'    "explanation": "Explanation referencing the context..."\n'
            f"  }}\n"
            f"]\n\n"
            f"JSON only. No extra text."
        )

    def _sa_prompt(self) -> str:
        bloom = _BLOOMS[self._difficulty]
        return (
            f"Generate {self._num_questions} short-answer questions "
            f"at Bloom's {self._difficulty} level.\n\n"

            f"SHORT ANSWER PATTERN FOR THIS LEVEL:\n{bloom['sa_pattern']}\n\n"

            f"CONTEXT:\n{self._context}"
            f"{self._seen_block()}\n\n"
            f"{self._lang_reminder()}\n\n"
            
            f"Return a JSON array — exactly {self._num_questions} items:\n"
            f"[\n"
            f"  {{\n"
            f'    "question": "A {self._difficulty}-level question...",\n'
            f'    "answer": "A complete answer at the correct cognitive level.",\n'
            f'    "key_points": ["point 1", "point 2"],\n'
            f'    "explanation": "Why this answer is correct per the context..."\n'
            f"  }}\n"
            f"]\n\n"
            f"JSON only. No extra text."
        )