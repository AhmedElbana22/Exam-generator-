import os
from dotenv import load_dotenv

load_dotenv()


class AppConfig:
    _instance = None  

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        self.HF_TOKEN = os.getenv("HF_TOKEN", "")
        self.LLM_MODEL = "Qwen/Qwen2.5-72B-Instruct"
        self.EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
        self.SMALL_MODEL = "Qwen/Qwen3-1.7B"

        self.CHUNK_SIZE = 500
        self.CHUNK_OVERLAP = 50
        self.TOP_K_RETRIEVAL = 3
 
        self.DEFAULT_NUM_QUESTIONS = 5
        self.DIFFICULTY_LEVELS = ["easy", "medium", "hard"]
        self.QUESTION_TYPES = ["MCQ", "true_false", "short_answer"]
 
        self.DATA_DIR = "data/"
        self.SAMPLES_DIR = "data/samples/"
        self.VECTOR_STORE_PATH = "data/vector_store.faiss"


# Usage anywhere in the project:
# from config import AppConfig
# config = AppConfig()   ← always returns same instance