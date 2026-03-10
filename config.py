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
        # Auth
        self.HF_TOKEN   = os.getenv("HF_TOKEN", "")

        # Models
        self.LLM_MODEL        = "Qwen/Qwen2.5-72B-Instruct"
        self.EMBED_MODEL      = "sentence-transformers/all-MiniLM-L6-v2" 
        self.FINE_TUNED_MODEL = "Elbana22/imtiqan-qwen-1.7b-quiz-lora"

        # RAG
        self.CHUNK_SIZE       = 512 
        self.CHUNK_OVERLAP    = 64 
        self.TOP_K_RETRIEVAL  = 4      # increased: more context = better questions
        self.MAX_USED_CHUNKS = 100 
        
        # Quiz generation 
        self.DEFAULT_NUM_QUESTIONS = 5
        self.MAX_NUM_QUESTIONS     = 20
        self.DIFFICULTY_LEVELS     = ["easy", "medium", "hard"]
        self.QUESTION_TYPES        = ["MCQ", "true_false", "short_answer", "mixed"]

        # LLM call settings
        self.MAX_TOKENS      = 4096    # increased for larger batches & incomplete JSON handling
        self.TEMPERATURE     = 0.75 
        self.API_TIMEOUT     = 120     # seconds before giving up
        self.MAX_RETRIES     = 3       # retry attempts on failure
        self.RETRY_BACKOFF   = 2.0     # exponential backoff multiplier 

        # Context window cap
        
        self.MAX_CONTEXT_CHARS = 6000  # hard cap before sending to LLM

        # Adaptive learning thresholds
        self.PROMOTE_THRESHOLD = 80.0 
        self.DEMOTE_THRESHOLD  = 40.0 

        # Deduplication
        self.MAX_SEEN_QUESTIONS = 500  # rolling window, drop oldest beyond this

        # Paths
        self.DATA_DIR           = "data/"
        self.SAMPLES_DIR        = "data/samples/"
        self.VECTOR_STORE_PATH  = "data/vector_store.faiss"
        self.SEEN_QUESTIONS_PATH = "data/seen_questions.json"

        # Teacher agent
        self.TEACHER_MAX_TOKENS   = 512
        self.TEACHER_TEMPERATURE  = 0.6
        self.TEACHER_HISTORY_SIZE = 10   # messages kept in context window