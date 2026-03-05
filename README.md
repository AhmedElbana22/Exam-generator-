# 🎓 ImtiQan — Adaptive RAG Quiz Generator

[![Python](https://img.shields.io/badge/Python-3.10-blue.svg)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.x-red.svg)](https://streamlit.io)
[![HuggingFace](https://img.shields.io/badge/🤗-HuggingFace-yellow.svg)](https://huggingface.co)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> **ImtiQan** (امتحان) means _exam_ in Arabic.  
> An intelligent quiz generator that reads your study material and creates adaptive quizzes — getting harder as you improve and easier when you struggle.

---

## ✨ Features

- 📄 **RAG Pipeline** — upload any PDF or paste text, questions generated from YOUR content
- 🧠 **Adaptive Learning** — difficulty adjusts automatically based on your performance
- ❓ **3 Question Types** — Multiple Choice, True/False, Short Answer
- 🌍 **Bilingual** — English and Arabic support
- 📊 **Performance Tracking** — weak topics, accuracy trends, session history
- 🤖 **Fine-tuned Model** — Qwen3-1.7B fine-tuned on SQuAD v2 with QLoRA

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Streamlit UI                      │
│         home_view / quiz_view / results_view        │
└───────────────────┬─────────────────────────────────┘
                    │
┌───────────────────▼─────────────────────────────────┐
│              AdaptiveController                     │
│   tracks performance → adjusts difficulty           │
└───────────────────┬─────────────────────────────────┘
                    │
┌───────────────────▼─────────────────────────────────┐
│               QuizController                        │
│   RAG retrieve → PromptBuilder → LLM → Quiz object  │
└──────┬──────────────────────────────────┬───────────┘
       │                                  │
┌──────▼───────┐                  ┌───────▼─────────┐
│ RAGController│                  │  HFApiService   │
│ Text→Chunks  │                  │  Qwen2.5-72B    │
│ →Embeddings  │                  │  via HF API     │
│ →FAISS       │                  └─────────────────┘
└──────────────┘
```

---

## 🚀 Live Demo

👉 **[Try ImtiQan here](https://ahmedelbana22-exam-generator--app-duwoyf.streamlit.app/)**

> Paste any text or upload a PDF → configure your quiz → start learning!

### 1 — Clone the repo

```bash
git clone https://github.com/AhmedElbana22/Exam-generator-.git
cd Exam-generator-
```

### 2 — Create conda environment

```bash
conda create -n quizforge python=3.10
conda activate quizforge
pip install -r requirements.txt
```

### 3 — Set up environment variables

```bash
cp .env.example .env
# Edit .env and add your HuggingFace token
```

### 4 — Run the app

```bash
streamlit run app.py
```

Open `http://localhost:8501` in your browser.

---

## 🔑 Environment Variables

Create a `.env` file in the project root:

```
HF_TOKEN=your_huggingface_read_token_here
```

Get your token at: https://huggingface.co/settings/tokens

---

## 📁 Project Structure

```
Exam-generator-/
├── model/
│   ├── question_model.py      # Question dataclass
│   ├── quiz_model.py          # Quiz session + evaluation
│   └── user_model.py          # Performance tracking
├── controller/
│   ├── rag_controller.py      # RAG pipeline
│   ├── quiz_controller.py     # Quiz generation
│   ├── adaptive_controller.py # Adaptive difficulty engine
│   └── evaluation_controller.py # BLEU/ROUGE metrics
├── view/
│   ├── home_view.py           # Upload + settings page
│   ├── quiz_view.py           # Question display
│   └── results_view.py        # Score + recommendations
├── services/
│   ├── text_processor.py      # PDF/text extraction
│   ├── embedding_service.py   # sentence-transformers
│   ├── vector_store.py        # FAISS index
│   ├── hf_api_service.py      # HuggingFace API
│   └── prompt_builder.py      # Prompt engineering
├── notebooks/
│   └── 02_fine_tuning_qwen_1.7B.ipynb
├── tests/                     # Full test suite
├── app.py                     # Streamlit entry point
├── config.py                  # Singleton configuration
└── requirements.txt
```

---

## 🧠 Design Patterns

| Pattern   | File                | Purpose                          |
| --------- | ------------------- | -------------------------------- |
| Singleton | `config.py`         | One config instance app-wide     |
| Builder   | `prompt_builder.py` | Step-by-step prompt construction |
| MVC       | whole architecture  | Separation of concerns           |
| Strategy  | `hf_api_service.py` | Swap LLM backends easily         |

---

## 🤖 Models Used

| Model                                    | Purpose                    | Size |
| ---------------------------------------- | -------------------------- | ---- |
| `Qwen/Qwen2.5-72B-Instruct`              | Quiz generation via HF API | 72B  |
| `sentence-transformers/all-MiniLM-L6-v2` | Text embeddings            | 80MB |
| `Elbana22/imtiqan-qwen-1.7b-quiz-lora`   | Fine-tuned quiz model      | 1.7B |

---

## 📊 Adaptive Learning Logic

```
Score >= 80%  →  promote difficulty   easy → medium → hard
Score <= 40%  →  demote difficulty    hard → medium → easy
40% < score < 80%  →  stay at current level
```

---

## 🧪 Running Tests

```bash
pytest tests/ -v
```

All 7 test files, 30+ test cases.

---

## 📓 Fine-Tuning

Model fine-tuned using QLoRA on SQuAD v2:

- Base: `Qwen/Qwen3-1.7B`
- Method: 4-bit quantization + LoRA adapters
- Dataset: 2,000 SQuAD v2 samples
- GPU: T4 (Google Colab)
- Published: [Elbana22/imtiqan-qwen-1.7b-quiz-lora](https://huggingface.co/Elbana22/imtiqan-qwen-1.7b-quiz-lora)

---

## 👤 Author

**Ahmed Elbana**  
GitHub: [@AhmedElbana22](https://github.com/AhmedElbana22)  
HuggingFace: [@Elbana22](https://huggingface.co/Elbana22)

---

## 📄 License

MIT License — free to use, modify, and distribute.
