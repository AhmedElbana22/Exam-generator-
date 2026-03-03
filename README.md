# 🎓 ImtiQan — Adaptive RAG Quiz Generator

An AI-powered quiz generator that reads your documents and creates
personalized, adaptive quizzes using Retrieval-Augmented Generation (RAG).

## 🚀 Features

- 📄 Upload PDF or paste text
- 🔍 RAG pipeline: chunks → embeddings → FAISS retrieval
- 🤖 Qwen3.5-35B generates questions via HuggingFace API
- 🎯 Adaptive difficulty based on user performance
- 📊 BLEU/ROUGE evaluation metrics
- 🌐 Streamlit web interface

## 🏗️ Architecture

- **MVC** pattern across all layers
- **RAG**: sentence-transformers + FAISS
- **Fine-tuned**: Qwen3-1.7B with QLoRA as difficulty classifier

## ⚙️ Setup

```bash
conda create -n quizforge python=3.10 -y
conda activate quizforge
pip install -r requirements.txt
cp .env.example .env  # Add your HF_TOKEN
streamlit run app.py
```

## 📁 Project Structure

```
QuizForge/
├── model/          # Data models
├── controller/     # Business logic
├── view/           # Streamlit pages
├── services/       # NLP, embeddings, API
├── notebooks/      # Fine-tuning (Colab/Lightning.ai)
├── tests/          # Unit tests
├── app.py          # Entry point
└── config.py       # Singleton config
```

## 🧠 Tech Stack

| Layer         | Tool                            |
| ------------- | ------------------------------- |
| LLM Inference | Qwen3.5-35B via HuggingFace API |
| Embeddings    | sentence-transformers           |
| Vector Store  | FAISS                           |
| Fine-tuning   | QLoRA on Qwen3-1.7B             |
| Frontend      | Streamlit                       |

## 📬 Author

Ahmed Elbana
