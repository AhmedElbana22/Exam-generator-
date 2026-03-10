import time
from huggingface_hub import InferenceClient
from loguru import logger
from config import AppConfig

config = AppConfig()


class HFApiService:
    """
    Wraps HuggingFace InferenceClient.

    Improvements 
        - Exponential-backoff retry (MAX_RETRIES attempts)
        - Structured generation with enforced JSON instruction
        - Streaming helper for Teacher agent (yields token chunks)
    """
    def __init__(self):
        if not config.HF_TOKEN:
            raise ValueError("HF_TOKEN missing — add it to .env")

        self.client = InferenceClient(token=config.HF_TOKEN)
        self.model  = config.LLM_MODEL
        logger.info(f"HFApiService ready — model: {self.model}")

    # Public API 

    def generate(
        self,
        prompt:        str,
        system_prompt: str   = "You are a helpful AI assistant.",
        max_tokens:    int   = None,
        temperature:   float = None,
        model:         str   = None,
    ) -> str:
        """
        Send a chat prompt to the LLM with retry + backoff.

        Returns the model's text response.
        """
        max_tokens  = max_tokens  or config.MAX_TOKENS 
        temperature = temperature or config.TEMPERATURE 
        model       = model       or self.model 

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": prompt},
        ]
        
        last_error = None
        for attempt in range(1, config.MAX_RETRIES + 1):
            try:
                logger.info(f"LLM call attempt {attempt}/{config.MAX_RETRIES}")
                response = self.client.chat_completion(
                    model       = model,
                    messages    = messages,
                    max_tokens  = max_tokens,
                    temperature = temperature,
                )
                result = response['choices'][0]['message']['content']
                logger.success(f"LLM responded — {len(result)} chars")
                return result

            except Exception as e:
                last_error = e
                wait = config.RETRY_BACKOFF ** (attempt - 1)
                logger.warning(f"Attempt {attempt} failed: {e}. Retrying in {wait}s…")
                if attempt < config.MAX_RETRIES:
                    time.sleep(wait)

        logger.error(f"All {config.MAX_RETRIES} attempts failed.")
        raise RuntimeError(f"LLM unavailable after {config.MAX_RETRIES} retries: {last_error}")

    def generate_structured(
        self,
        prompt:        str,
        system_prompt: str   = "You are a helpful AI assistant.",
        max_tokens:    int   = None,
        temperature:   float = None,
    ) -> str:
        """
        Same as generate() but appends a strict JSON instruction.
        Used for quiz generation where we need parseable output.
        """
        json_system = (
            system_prompt
            + "\n\nCRITICAL: Respond with ONLY a valid JSON array. "
            + "No markdown, no prose, no code fences. Raw JSON only."
        )
        return self.generate(
            prompt        = prompt,
            system_prompt = json_system,
            max_tokens    = max_tokens,
            temperature   = temperature,
        )

    def stream(
        self,
        prompt:        str,
        system_prompt: str   = "You are a helpful AI assistant.",
        max_tokens:    int   = None,
        temperature:   float = None,
    ) :
        """
        Streaming generator — yields text chunks as they arrive.
        Used by the Teacher chat agent for real-time response display.
        """
        max_tokens  = max_tokens  or config.TEACHER_MAX_TOKENS
        temperature = temperature or config.TEACHER_TEMPERATURE

        try:
            stream = self.client.chat_completion(
                model       = self.model,
                messages    = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user",   "content": prompt},
                ],
                max_tokens  = max_tokens,
                temperature = temperature,
                stream      = True,
            )
            for chunk in stream:
                delta = chunk['choices'][0]['delta']['content']
                if delta:
                    yield delta

        except Exception as e:
            logger.error(f"Streaming failed: {e}")
            yield f"\n\n⚠️ Connection error: {e}"