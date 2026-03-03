from huggingface_hub import InferenceClient
from loguru import logger
from config import AppConfig

config = AppConfig()


class HFApiService:

    def __init__(self):
        if not config.HF_TOKEN:
            raise ValueError("HF_TOKEN is missing! Add it to your .env file.")

        self.client = InferenceClient(
            token=config.HF_TOKEN,
        )
        self.model = config.LLM_MODEL
        logger.info(f"HFApiService ready — model: {self.model}")

    def generate(
        self,
        prompt: str,
        system_prompt: str = "You are a helpful AI assistant.",
        max_tokens: int = 1024,
        temperature: float = 0.7,
    ) -> str:
        """
        Send a prompt to the LLM and get a response.

        Args:
            prompt:        The user message
            system_prompt: Instructions for the model behavior
            max_tokens:    Max response length
            temperature:   Creativity (0.0 = deterministic, 1.0 = creative)

        Returns:
            The model's response as a string
        """
        logger.info(f"Sending request to {self.model}...")
        logger.debug(f"Prompt preview: {prompt[:100]}...")

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user",   "content": prompt},
                ],
                max_tokens=max_tokens,
                temperature=temperature,
            )

            result = response.choices[0].message.content
            logger.success(f"Response received — {len(result)} characters")
            return result

        except Exception as e:
            logger.error(f"HuggingFace API call failed: {e}")
            raise

    def generate_structured(
        self,
        prompt: str,
        system_prompt: str = "You are a helpful AI assistant.",
        max_tokens: int = 1024,
        temperature: float = 0.7,
    ) -> str:
        """
        Same as generate() but adds JSON instruction to system prompt.
        Used when we need structured quiz output.
        """
        json_system = (
            system_prompt
            + "\nAlways respond with valid JSON only. "
            + "No explanation, no markdown, no extra text."
        )
        return self.generate(prompt, json_system, max_tokens, temperature)