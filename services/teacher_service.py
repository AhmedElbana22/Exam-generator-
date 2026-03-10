"""
Teacher Agent service.
Maintains a short conversation history and answers student questions
in the context of the current quiz question.
"""

from loguru import logger
from services.hf_api_service import HFApiService
from config import AppConfig

config = AppConfig()

_SYSTEM = """You are an expert, patient, and encouraging Teacher AI.

Your role:
- Answer student questions about the quiz question they are currently on.
- Use the provided context (study material excerpt) and quiz question to ground your answers.
- Keep answers clear, educational, and concise (2–4 sentences unless asked to elaborate).
- If the student asks for the answer directly, guide them with hints instead of giving it away.
- Always be encouraging and supportive.
- Respond in the same language the student uses."""


class TeacherService:
    """
    Stateful teacher agent for one quiz session.
    Keeps a rolling conversation history (TEACHER_HISTORY_SIZE turns).
    """

    def __init__(self):
        self.llm      = HFApiService()
        self.history: list[dict] = []   # [{"role": "user"|"assistant", "content": str}]
        logger.info("TeacherService initialized")

    def reset(self) -> None:
        """Clear conversation history (call when quiz question changes)."""
        self.history = []

    def ask(
        self,
        student_message: str,
        quiz_question:   str,
        context_snippet: str = "",
    ) -> str:
        """
        Send a student message, get the teacher's full response.

        Args:
            student_message: What the student typed
            quiz_question:   Current quiz question text (for grounding)
            context_snippet: Relevant study material excerpt (optional)

        Returns:
            Teacher's response as a string
        """
        grounded_prompt = self._build_grounded_prompt(
            student_message, quiz_question, context_snippet
        )
        self.history.append({"role": "user", "content": grounded_prompt})

        # trim history to rolling window
        if len(self.history) > config.TEACHER_HISTORY_SIZE * 2:
            self.history = self.history[-(config.TEACHER_HISTORY_SIZE * 2):]

        # build full conversation string for the LLM
        conversation = "\n".join(
            f"{'Student' if m['role']=='user' else 'Teacher'}: {m['content']}"
            for m in self.history
        )
        conversation += "\nTeacher:"

        response = self.llm.generate(
            prompt        = conversation,
            system_prompt = _SYSTEM,
            max_tokens    = config.TEACHER_MAX_TOKENS,
            temperature   = config.TEACHER_TEMPERATURE,
        )

        self.history.append({"role": "assistant", "content": response})
        return response

    def stream_ask(
        self,
        student_message: str,
        quiz_question:   str,
        context_snippet: str = "",
    ):
        """Streaming version — yields text chunks. Use with st.write_stream()."""
        grounded_prompt = self._build_grounded_prompt(
            student_message, quiz_question, context_snippet
        )
        self.history.append({"role": "user", "content": grounded_prompt})

        conversation = "\n".join(
            f"{'Student' if m['role']=='user' else 'Teacher'}: {m['content']}"
            for m in self.history
        )
        conversation += "\nTeacher:"

        full_response = ""
        for chunk in self.llm.stream(
            prompt        = conversation,
            system_prompt = _SYSTEM,
            max_tokens    = config.TEACHER_MAX_TOKENS,
            temperature   = config.TEACHER_TEMPERATURE,
        ):
            full_response += chunk
            yield chunk

        self.history.append({"role": "assistant", "content": full_response})

    # Internal

    @staticmethod
    def _build_grounded_prompt(
        student_message: str,
        quiz_question:   str,
        context_snippet: str,
    ) -> str:
        parts = [f"[Current quiz question]: {quiz_question}"]
        if context_snippet:
            parts.append(f"[Relevant material]: {context_snippet[:500]}")
        parts.append(f"[Student question]: {student_message}")
        return "\n".join(parts)