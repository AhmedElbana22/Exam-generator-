# 🎓 ImtiQan — Adaptive RAG Quiz Generator

[![Python](https://img.shields.io/badge/Python-3.10-blue.svg)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.x-red.svg)](https://streamlit.io)
[![HuggingFace](https://img.shields.io/badge/🤗-HuggingFace-yellow.svg)](https://huggingface.co)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> **ImtiQan** (امتحان) means _exam_ in Arabic.  
> Upload your study material, and ImtiQan generates quizzes from it — adapting difficulty based on how you're actually doing.

---

## ✨ What it does

- 📄 **RAG Pipeline** — questions come strictly from your uploaded content, not from the model's memory
- 🧠 **Adaptive difficulty** — promotes/demotes between easy → medium → hard based on your score per session
- 🎲 **4 question modes** — MCQ, True/False, Short Answer, or Mixed (all three in one quiz)
- 🧑‍🏫 **Teacher Agent** — ask a follow-up on any quiz item and get a contextual explanation
- 🔁 **No repeated questions** — SHA-1 fingerprinting + sentence-transformer semantic dedup across sessions
- 🌍 **Bilingual** — English and Arabic
- 📊 **Performance tracking** — weak topics, accuracy per difficulty, session history

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                        Streamlit UI                          │
│            home_view / quiz_view / results_view              │
└────────────────────────┬─────────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────────┐
│                   AdaptiveController                         │
│   tracks performance → adjusts difficulty → manages seen-Q   │
└────────────────────────┬─────────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────────┐
│                    QuizController                            │
│   RAG → PromptBuilder → LLM → parse → dedup → Quiz object   │
└──────┬──────────────────────────────────┬────────────────────┘
       │                                  │
┌──────▼───────────┐             ┌────────▼────────┐
│  RAGController   │             │  HFApiService   │
│  Text → Chunks   │             │  Qwen2.5-72B    │
│  → Embeddings    │             │  retry + backoff│
│  → FAISS + MMR   │             └─────────────────┘
│  + chunk rotation│
└──────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────────┐
│                    TeacherService                            │
│   per-question chat agent · rolling history · RAG-grounded   │
└──────────────────────────────────────────────────────────────┘
```

---

## 🚀 Live Demo

👉 **[Try ImtiQan here](https://ahmedelbana22-exam-generator--app-duwoyf.streamlit.app/)**

> Paste any text or upload a PDF → configure your quiz → start learning.

---

## 🔧 Run locally

### 1 — Clone

```bash
git clone https://github.com/AhmedElbana22/Exam-generator-.git
cd Exam-generator-
```

### 2 — Environment

```bash
conda create -n imtiqan python=3.10
conda activate imtiqan
pip install -r requirements.txt
```

### 3 — API token

```bash
cp .env.example .env
# add your HuggingFace token to .env
```

```
HF_TOKEN=your_huggingface_read_token_here
```

Get yours at: https://huggingface.co/settings/tokens

### 4 — Start

```bash
streamlit run app.py
```

---

## 📁 Project Structure

```
Exam-generator-/
├── model/
│   ├── question_model.py       # Question dataclass + SHA-1 fingerprint
│   ├── quiz_model.py           # Quiz session, evaluation, type breakdown
│   └── user_model.py           # Performance tracking per topic/difficulty
├── controller/
│   ├── rag_controller.py       # RAG + MMR reranking + chunk rotation
│   ├── quiz_controller.py      # Generation pipeline + semantic dedup
│   ├── adaptive_controller.py  # Difficulty engine + seen-Q persistence
│   └── evaluation_controller.py
├── view/
│   ├── home_view.py            # Upload, settings, mixed-type preview
│   ├── quiz_view.py            # Question UI + inline feedback + Teacher panel
│   └── results_view.py         # Score, type breakdown, full review
├── services/
│   ├── text_processor.py       # PDF/text extraction + chunking
│   ├── embedding_service.py    # sentence-transformers
│   ├── vector_store.py         # FAISS index
│   ├── hf_api_service.py       # HF API + retry/backoff + streaming
│   ├── prompt_builder.py       # Bloom's Taxonomy prompt engineering
│   └── teacher_service.py      # Teacher agent with conversation history
├── notebooks/
│   └── 02_fine_tuning_qwen_1.7B.ipynb
├── tests/
├── app.py
├── config.py
└── requirements.txt
```

---

## 🧠 Design Patterns

| Pattern   | Where               | Why                                     |
| --------- | ------------------- | --------------------------------------- |
| Singleton | `config.py`         | One config instance shared across app   |
| Builder   | `prompt_builder.py` | Composable prompt construction per type |
| MVC       | whole architecture  | Clean separation between logic and UI   |
| Strategy  | `hf_api_service.py` | LLM backend can be swapped easily       |

---

## 🤖 Models

| Model                                    | Purpose                              | Size |
| ---------------------------------------- | ------------------------------------ | ---- |
| `Qwen/Qwen2.5-72B-Instruct`              | Quiz generation via HF Inference API | 72B  |
| `sentence-transformers/all-MiniLM-L6-v2` | Embeddings for RAG + semantic dedup  | 80MB |
| `Elbana22/imtiqan-qwen-1.7b-quiz-lora`   | Fine-tuned quiz model (QLoRA)        | 1.7B |

---

## 📊 How adaptation works

```
score >= 80%          →  promote:   easy → medium → hard
score <= 40%          →  demote:    hard → medium → easy
40% < score < 80%     →  stay at current level

weak topics           →  next quiz targets those first
seen questions        →  fingerprinted + embedding-checked, never repeated
```

Difficulty isn't just a label — it maps to a Bloom's Taxonomy cognitive level:

| Level  | Bloom's Target        | Example stem                                              |
| ------ | --------------------- | --------------------------------------------------------- |
| Easy   | Remember / Understand | "What is...", "Identify..."                               |
| Medium | Apply / Analyze       | "How does...", "What would happen if..."                  |
| Hard   | Evaluate / Create     | "Compare and contrast...", "What is the limitation of..." |

---

## 🔁 Deduplication

Two layers prevent repeated questions across sessions:

1. **SHA-1 fingerprint** — hashes `(question + answer)`, catches exact and near-exact repeats
2. **Semantic similarity** — embeds question text and rejects anything with cosine similarity ≥ 0.82 to a previously seen question

Both layers persist to disk between sessions.

---

## 🗂️ RAG — how context is selected

- Document split into overlapping chunks and indexed in FAISS
- Query rewritten based on difficulty before retrieval (different semantic region per level)
- **MMR (Maximal Marginal Relevance)** re-ranks candidates to balance relevance vs diversity
- **Chunk rotation** tracks used chunks and deprioritises them in future quizzes

---

## 🧪 Tests

```bash
pytest tests/ -v
```

---

## 📓 Fine-Tuning

Fine-tuned on SQuAD v2 using QLoRA:

- Base model: `Qwen/Qwen3-1.7B`
- Method: 4-bit quantization + LoRA adapters
- Dataset: 2,000 samples
- Hardware: T4 on Google Colab
- Published: [Elbana22/imtiqan-qwen-1.7b-quiz-lora](https://huggingface.co/Elbana22/imtiqan-qwen-1.7b-quiz-lora)

---

## 👤 Author

**Ahmed Elbana**  
GitHub: [@AhmedElbana22](https://github.com/AhmedElbana22)  
HuggingFace: [@Elbana22](https://huggingface.co/Elbana22)

---

## 📄 License

MIT — do whatever you want with it.
