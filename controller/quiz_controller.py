"""
Main orchestrator : connects RAG + PromptBuilder + LLM + Quiz model.
Full flow:
  1. User provides text/PDF + settings
  2. RAGController indexes the document
  3. PromptBuilder constructs the prompt
  4. HFApiService calls the LLM
  5. Response parsed into Question objects
  6. Quiz object returned ready for UI
"""

import json
import uuid
import re
from loguru import logger
from config import AppConfig
from controller.rag_controller import RAGController
from services.prompt_builder import PromptBuilder
from services.hf_api_service import HFApiService
from model.question_model import Question
from model.quiz_model import Quiz

config = AppConfig()

class QuizController:
    """
    Orchestrates the full quiz generation pipeline.

    Usage:
        qc = QuizController()
        qc.load_text("some study material...")
        quiz = qc.generate_quiz(
            topic="neural networks",
            question_type="MCQ",
            difficulty="medium",
            num_questions=5,
        )
    """

    def __init__(self):
        self.rag        = RAGController()
        self.llm        = HFApiService()
        self.builder    = PromptBuilder()
        logger.info("QuizController initialized") 

    def load_text(self, text: str) -> int:
        """Load raw text into the RAG pipeline."""
        return self.rag.load_text(text)

    def load_pdf(self, pdf_path: str) -> int:
        """Load a PDF file into the RAG pipeline."""
        return self.rag.load_document(pdf_path)
 

    def generate_quiz(
        self,
        topic:         str,
        question_type: str  = "MCQ",
        difficulty:    str  = "medium",
        num_questions: int  = 5,
        language:      str  = "english",
    ) -> Quiz:
        """
        Full pipeline: topic -> RAG retrieval -> prompt -> LLM -> Quiz.

        Args:
            topic:          What to quiz about (used as RAG query)
            question_type:  'MCQ', 'true_false', or 'short_answer'
            difficulty:     'easy', 'medium', or 'hard'
            num_questions:  How many questions to generate
            language:       'english' or 'arabic'

        Returns:
            A Quiz object ready for the UI
        """
        logger.info(
            f"Generating quiz — topic='{topic}' | type={question_type} | "
            f"difficulty={difficulty} | n={num_questions} | lang={language}"
        )

        # Step 1 : retrieve relevant context from RAG
        context = self.rag.retrieve_as_context(topic, top_k=config.TOP_K_RETRIEVAL)
        logger.info(f"Context retrieved — {len(context)} characters")

        # Step 2 : build prompt
        user_prompt, system_prompt = (
            PromptBuilder()
            .set_context(context)
            .set_question_type(question_type)
            .set_difficulty(difficulty)
            .set_num_questions(num_questions)
            .set_language(language)
            .build()
        )

        # Step 3 : call LLM
        raw_response = self.llm.generate_structured(
            prompt=user_prompt,
            system_prompt=system_prompt,
            max_tokens=2048,
            temperature=0.7,
        )
        logger.info("LLM response received")

        # Step 4 : parse response into Question objects
        questions = self._parse_questions(raw_response, question_type)
        logger.success(f"Parsed {len(questions)} questions successfully")

        # Step 5 : build and return Quiz object
        quiz = Quiz(
            quiz_id=str(uuid.uuid4())[:8],
            topic=topic,
            difficulty=difficulty,
            question_type=question_type,
            language=language,
            questions=questions,
        )

        logger.success(f"Quiz ready — ID: {quiz.quiz_id}")
        return quiz
    
    #  Parsing LLM response into Question objects
    def _parse_questions(
        self,
        raw_response: str,
        question_type: str,
    ) -> list[Question]:
        """
        Parse raw LLM JSON response into Question objects.
        Handles common LLM formatting issues (extra text, markdown).

        Args:
            raw_response:  Raw string from LLM
            question_type: Type of questions expected

        Returns:
            List of Question objects
        """ 
        cleaned = raw_response.strip()
        cleaned = re.sub(r"```json|```", "", cleaned).strip() # remove markdown code fences if present

        match = re.search(r"\[.*\]", cleaned, re.DOTALL)
        if match:
            cleaned = match.group(0)

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            logger.debug(f"Raw response was: {raw_response[:300]}")
            raise ValueError(
                "LLM returned invalid JSON. Try regenerating the quiz."
            )

        questions = []
        for i, item in enumerate(data):
            try:
                q = Question.from_dict(item, question_id=i, question_type=question_type)
                questions.append(q)
            except Exception as e:
                logger.warning(f"Skipping question {i} due to parse error: {e}")
                continue

        if not questions:
            raise ValueError("No valid questions could be parsed from LLM response.")

        return questions