"""
Quiz generation orchestrator.

Changes vs v2: {Updated2--}
    - difficulty passed into RAG query (not just prompt)
    - semantic dedup using embedding cosine similarity (catches paraphrases)
    - mixed quiz uses correct difficulty-aware RAG per sub-type
    - parse retry with temperature bump on 2nd attempt
"""

import json
import uuid
import re
import random
import numpy as np
from loguru import logger
from config import AppConfig
from controller.rag_controller import RAGController
from services.prompt_builder import PromptBuilder
from services.hf_api_service import HFApiService
from services.embedding_service import EmbeddingService
from model.question_model import Question
from model.quiz_model import Quiz

config = AppConfig()

_MIXED_TYPES = ["MCQ", "true_false", "short_answer"]

# cosine similarity threshold — questions more similar than this are duplicates
_SEMANTIC_SIM_THRESHOLD = 0.82


class QuizController:

    def __init__(self):
        self.rag       = RAGController()
        self.llm       = HFApiService()
        self.builder   = PromptBuilder()
        self.embedder  = EmbeddingService()   # for semantic dedup
        # cache of (text, embedding) for all questions ever generated this session
        self._question_embeddings: list[tuple[str, np.ndarray]] = []
        logger.info("QuizController initialized")

    # Document loading  

    def load_text(self, text: str) -> int:
        return self.rag.load_text(text)

    def load_pdf(self, pdf_path: str) -> int:
        return self.rag.load_document(pdf_path)

    # Quiz generation  

    def generate_quiz(
        self,
        topic:          str,
        question_type:  str       = "MCQ",
        difficulty:     str       = "medium",
        num_questions:  int       = 5,
        language:       str       = "english",
        seen_questions: set[str]  = None,
    ) -> Quiz:
        seen_questions = seen_questions or set()
        logger.info(
            f"Generating quiz | topic='{topic}' type={question_type} "
            f"diff={difficulty} n={num_questions} lang={language}"
        )

        # RAG: pass difficulty so query is rewritten 
        context = self.rag.retrieve_as_context(
            query      = topic,
            top_k      = config.TOP_K_RETRIEVAL,
            difficulty = difficulty,         # <- KEY: different chunks per level
        )
        logger.debug(f"Context: {len(context)} chars")

        # Configure shared builder  
        self.builder = (
            PromptBuilder()
            .set_context(context)
            .set_difficulty(difficulty)
            .set_num_questions(num_questions)
            .set_language(language)
        )

        if question_type == "mixed":
            questions = self._generate_mixed(
                difficulty, num_questions, language, context, seen_questions
            )
        else:
            self.builder.set_question_type(question_type)
            questions = self._call_and_parse(
                question_type, num_questions, seen_questions
            )

        quiz = Quiz(
            quiz_id       = str(uuid.uuid4())[:8],
            topic         = topic,
            difficulty    = difficulty,
            question_type = question_type,
            language      = language,
            questions     = questions,
        )
        logger.success(f"Quiz {quiz.quiz_id} ready — {len(questions)} questions")
        return quiz

    # Mixed quiz

    def _generate_mixed(
        self,
        difficulty:     str,
        num_questions:  int,
        language:       str,
        context:        str,
        seen_questions: set[str],
    ) -> list[Question]:
        base  = num_questions // 3
        extra = num_questions  % 3
        counts = {
            "MCQ":          base + (1 if extra > 0 else 0),
            "true_false":   base + (1 if extra > 1 else 0),
            "short_answer": base,
        }

        all_questions: list[Question] = []
        global_id = 0

        for q_type, count in counts.items():
            if count == 0:
                continue
            try:
                self.builder.set_question_type(q_type).set_num_questions(count)
                qs = self._call_and_parse(q_type, count, seen_questions)
                for q in qs:
                    q.question_id = global_id
                    global_id += 1
                all_questions.extend(qs)
            except Exception as e:
                logger.warning(f"Mixed sub-type {q_type} failed: {e}")

        if not all_questions:
            raise ValueError("Mixed quiz failed for all sub-types.")

        random.shuffle(all_questions)
        for i, q in enumerate(all_questions):
            q.question_id = i
        return all_questions

    # LLM call + parse + dedup  

    def _call_and_parse(
        self,
        question_type:  str,
        num_questions:  int,
        seen_questions: set[str],
    ) -> list[Question]:
        """Build prompt → LLM (2 attempts) → parse → hash dedup → semantic dedup."""
        seen_texts = list(seen_questions)[:20]

        user_prompt, system_prompt = (
            self.builder
            .set_question_type(question_type)
            .set_num_questions(num_questions)
            .set_seen_questions(seen_texts)
            .build()
        )

        raw = None
        last_error = None

        for attempt in range(1, 3):
            try:
                raw = self.llm.generate_structured(
                    prompt        = user_prompt,
                    system_prompt = system_prompt,
                    max_tokens    = config.MAX_TOKENS,
                    # bump temperature on retry to get different output
                    temperature   = config.TEMPERATURE + (0.1 * (attempt - 1)),
                )
                questions = self._parse_questions(raw, question_type)
                # hash dedup (exact + near-exact)
                questions = self._hash_dedup(questions, seen_questions)
                # semantic dedup (paraphrase detection)
                questions = self._semantic_dedup(questions)
                return questions

            except (ValueError, json.JSONDecodeError) as e:
                last_error = e
                logger.warning(f"Parse attempt {attempt} failed: {e}")
                if raw:
                    logger.debug(f"Raw response ({len(raw)} chars): {raw[:500]}")

        # Log the full response for debugging
        if raw:
            logger.error(f"Full LLM response ({len(raw)} chars):\n{raw}")
        
        raise ValueError(
            f"LLM returned unparseable output after 2 attempts. "
            f"Last error: {last_error}. Preview: {str(raw)[:200] if raw else 'None'}"
        )

    # JSON parsing 

    def _parse_questions(self, raw: str, question_type: str) -> list[Question]:
        cleaned = re.sub(r"```(?:json)?", "", raw).strip().rstrip("`").strip()

        # Look for JSON array: try [ ... ] first, then fallback to full string
        match = re.search(r"\[.*\]", cleaned, re.DOTALL)
        if not match:
            # If no match, try parsing the whole cleaned string
            if cleaned.startswith("["):
                json_str = cleaned
            else:
                raise ValueError("No JSON array found in LLM response.")
        else:
            json_str = match.group(0)

        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}")
            logger.error(f"Attempted to parse: {json_str[:500]}...")
            
            # Try to fix incomplete JSON by closing it
            if json_str.count("[") > json_str.count("]"):
                logger.info("Detected incomplete JSON array, attempting to fix...")
                fixed_json = json_str + "]" * (json_str.count("[") - json_str.count("]"))
                try:
                    data = json.loads(fixed_json)
                    logger.info("Successfully fixed incomplete JSON")
                except json.JSONDecodeError:
                    raise ValueError(f"Cannot parse JSON even after fixing: {e}")
            else:
                raise ValueError(f"Cannot parse JSON: {e}")

        questions = []
        for i, item in enumerate(data):
            try:
                q = Question.from_dict(item, question_id=i, question_type=question_type)
                if q.question and q.answer:
                    questions.append(q)
            except Exception as e:
                logger.warning(f"Skipping item {i}: {e}")

        if not questions:
            raise ValueError("No valid questions parsed.")

        return questions

    # Hash deduplication (exact + near-exact) 

    def _hash_dedup(
        self,
        questions:      list[Question],
        seen_questions: set[str],
    ) -> list[Question]:
        """Remove questions whose fingerprint matches any previously seen question."""
        fresh   = [q for q in questions if q.fingerprint not in seen_questions]
        removed = len(questions) - len(fresh)
        if removed:
            logger.info(f"Hash dedup: removed {removed} exact/near-exact repeats")
        # fallback: keep all if everything flagged (avoids empty quiz)
        return fresh if fresh else questions

    #  Semantic deduplication (paraphrase detection)  

    def _semantic_dedup(self, questions: list[Question]) -> list[Question]:
        """
        Remove questions that are semantically too similar to ANY question
        previously generated this session (including current batch).

        Uses cosine similarity on question text embeddings.
        Threshold: _SEMANTIC_SIM_THRESHOLD (default 0.82)
        """
        if not questions:
            return questions

        kept: list[Question] = []

        for q in questions:
            q_text = q.question.strip().lower()
            q_vec  = self.embedder.embed_query(q_text)

            is_duplicate = False

            # check against all previously accepted questions this session
            for prev_text, prev_vec in self._question_embeddings:
                sim = float(np.dot(q_vec, prev_vec) / (
                    np.linalg.norm(q_vec) * np.linalg.norm(prev_vec) + 1e-9
                ))
                if sim >= _SEMANTIC_SIM_THRESHOLD:
                    logger.debug(
                        f"Semantic dedup: '{q_text[:50]}' ≈ '{prev_text[:50]}' "
                        f"(sim={sim:.3f}) — skipped"
                    )
                    is_duplicate = True
                    break

            if not is_duplicate:
                kept.append(q)
                self._question_embeddings.append((q_text, q_vec))

        # rolling cap on embedding cache
        if len(self._question_embeddings) > config.MAX_SEEN_QUESTIONS:
            self._question_embeddings = (
                self._question_embeddings[-config.MAX_SEEN_QUESTIONS:]
            )

        removed = len(questions) - len(kept)
        if removed:
            logger.info(f"Semantic dedup: removed {removed} paraphrase(s)")

        return kept if kept else questions