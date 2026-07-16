```markdown
<div align="center">
  
# 🏢 AlphaLens: Next-Gen Financial RAG
**Stop settling for generic, hallucination-prone RAG pipelines.** 
*AlphaLens is a production-grade, multi-stage Retrieval-Augmented Generation engine built specifically for SEC 10-K annual reports.*

**👉 [Try the Live Demo on Hugging Face](https://huggingface.co/spaces/omkumar1729/new_s) 👈**

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![Gradio](https://img.shields.io/badge/UI-Gradio-orange.svg)](https://gradio.app/)
[![Qdrant](https://img.shields.io/badge/VectorDB-Qdrant-red.svg)](https://qdrant.tech/)
[![Hugging Face Spaces](https://img.shields.io/badge/%F0%9F%A4%97%20Hugging%20Face-Spaces-blue)](https://huggingface.co/spaces/omkumar1729/new_s)

</div>

---

### 🎯 Why is AlphaLens Different? 

Most RAG tutorials treat a 10-K like a generic PDF—blindly slicing it into 500-token chunks, destroying tables, splitting paragraphs mid-sentence, and hoping the LLM figures it out. **That doesn't work for finance.**

AlphaLens introduces a **Deterministic Semantic Chunking** & **Advanced 6-Step Retrieval** architecture:
1. 🧠 **Domain-Aware Parsing:** It doesn't split by word count; it maps the document by SEC Items (Item 1, 1A, 7, etc.) to keep related financial context together.
2. 🔒 **Zero-Hallucination Chunking:** We use an LLM to identify semantic boundaries, but **strictly enforce 100% verbatim text preservation**. No dropped tables, no paraphrased risk factors.
3. 🏷️ **Auto-Enriched Metadata:** Every chunk is automatically given a specific `headline` and `summary` by the LLM, which are embedded alongside the text for superior vector search.
4. 🔍 **Advanced 6-Step Retrieval:** We don't just do single-vector search. AlphaLens uses Query Rewriting, Dual Retrieval, Merging, and Cross-Encoder Reranking to find the exact financial needle in the haystack.
5. 🛡️ **Bulletproof Resiliency:** Built with aggressive retry logic, rate-limit handling, and cold-start management. This pipeline does not crash.

---

### 📸 Screenshots

*(Upload your screenshots to the repo and update the links below)*

| The Ingestion Pipeline (Real-time Logs) | The RAG Chat Interface (Chat + Sources) |
| :---: | :---: |
| ![Ingestion Pipeline](link_to_your_ingestion_screenshot.png) | ![Chat Interface](link_to_your_chat_screenshot.png) |

---

### 📊 Architecture Flowcharts

#### 1. The Ingestion Pipeline (How the Database is Built)
This pipeline takes a company name, downloads the raw SEC filing, and converts it into a highly structured, searchable vector database.

```text
[ User Input: Company & Year ]
            │
            ▼
    ┌───────────────┐
    │  Ticker Lookup │ (SEC EDGAR Mapping)
    └───────┬───────┘
            │
            ▼
    ┌───────────────┐
    │  Download 10-K │ (MD Generator)
    └───────┬───────┘
            │
            ▼
    ┌───────────────────────────────────┐
    │  STAGE 1: Domain-Aware Parsing    │
    │  • Extract SEC Items (1, 1A, 7...)│
    │  • Smart Merge small items        │
    └───────┬───────────────────────────┘
            │
            ▼
    ┌───────────────────────────────────┐
    │  STAGE 2: LLM Semantic Chunking   │
    │  • Gemini identifies boundaries   │
    │  • 100% Verbatim text enforcement │
    │  • Generate Headline + Summary    │
    └───────┬───────────────────────────┘
            │
            ▼
    ┌───────────────────────────────────┐
    │  STAGE 3: Embed & Upload          │
    │  • Jina v4 Embeddings             │
    │  • Upsert to Qdrant Cloud         │
    └───────────────────────────────────┘
```

#### 2. The RAG Orchestrator (How Questions are Answered)
When a user asks a question, it goes through a rigorous 6-step pipeline to ensure accuracy and reduce hallucinations.

```text
[ User Question ]
            │
            ▼
    ┌───────────────────────────────────┐
    │  STEP 1: Query Rewriting          │
    │  • Optimize query for vector search│
    └───────┬───────────────────────────┘
            │
            ▼
    ┌───────────────────────────────────┐
    │  STEP 2 & 3: Dual Retrieval       │
    │  • Search Original Query          │
    │  • Search Rewritten Query         │
    │  • Fetch from Qdrant Cloud        │
    └───────┬───────────────────────────┘
            │
            ▼
    ┌───────────────────────────────────┐
    │  STEP 4: Merge & Deduplicate      │
    │  • Combine results from both scans│
    └───────┬───────────────────────────┘
            │
            ▼
    ┌───────────────────────────────────┐
    │  STEP 5: Cross-Encoder Reranking  │
    │  • Jina Reranker scores relevance │
    │  • Keep only the top chunks       │
    └───────┬───────────────────────────┘
            │
            ▼
    ┌───────────────────────────────────┐
    │  STEP 6: Generation               │
    │  • Build Prompt (Context + Hist)  │
    │  • LLM generates final answer     │
    └───────────────────────────────────┘
```

---

### 📂 Project Structure

```text
AlphaLens/
│
├── app.py                     # 🖥️ Gradio UI (Main entry point)
├── master_pipeline.py         # 🧩 Core orchestrator for Ingestion
├── ticker_extractor.py        # 🔍 Maps company names to SEC tickers
├── MD_Generator.py            # ⬇️ Downloads raw 10-K markdown from SEC EDGAR
├── backup.py                  # 📦 Backup script
├── requirements.txt           # 📋 Python dependencies
├── .env                       # 🔑 API Keys
├── .gitignore
│
├── ingest/                    # 🏭 The Data Processing Factory
│   ├── parsing.py             # Stage 1: Extracts SEC Items & smart merges
│   ├── stage_2_worker.py      # Stage 2: LLM Semantic Chunking (Gemini)
│   └── stage_3_embed.py       # Stage 3: Jina Embeddings + Qdrant Upload
│
├── rag_orchestrator/          # 🧠 The Advanced RAG Engine
│   ├── __init__.py
│   ├── pipeline.py            # Connects all 6 RAG steps
│   ├── rewrite.py             # Step 1: Query Rewriting for better search
│   ├── retriever.py           # Step 2 & 3: Dual Vector Search (Original + Rewritten)
│   ├── merger.py              # Step 4: Deduplication & Merging
│   ├── reranker.py            # Step 5: Jina Cross-Encoder Reranking
│   ├── prompt_builder.py      # Step 6a: Context & History formatting
│   ├── generator.py           # Step 6b: Final LLM answer generation
│   ├── schema.py              # Pydantic data models
│   └── config.py              # LLM & Qdrant configuration
│
├── finance_db/                # 🗃️ Local database storage
├── Knowledge-base/            # 📂 Local storage for raw 10-K markdown files
│   └── finance_reports/
│
├── stage_1_json/              # 🔄 Caching directories for pipeline resilience
└── stage_2_json/
```

---

### 🛠️ Tech Stack

| Category | Technology | Purpose |
| :--- | :--- | :--- |
| **Frontend** | Gradio | Real-time UI for ingestion logs, chat, and source viewing |
| **LLM Orchestration** | LiteLLM | Unified interface for LLM providers (Gemini) |
| **LLM (Chunking/RAG)** | Google Gemini 3.1 Flash Lite | Semantic boundary detection & Answer Generation |
| **Embeddings** | Jina Embeddings v4 | High-accuracy financial text vectorization |
| **Reranking** | Jina Reranker (Cross-Encoder) | Precision scoring of retrieved chunks |
| **Vector Database** | Qdrant Cloud | Scalable, production-ready vector storage & search |
| **Data Validation** | Pydantic | Enforcing strict JSON schemas for LLM outputs |
| **Resiliency** | Tenacity | Retries & Exponential Backoff for API/DB timeouts |
| **SEC Data** | edgartools | Downloading structured 10-K filings from EDGAR |

---

### ⚙️ Getting Started

Follow these steps to get AlphaLens running on your local machine.

#### 1. Clone the Repository
```bash
git clone https://github.com/YOUR_USERNAME/AlphaLens.git
cd AlphaLens
```

#### 2. Create a Virtual Environment & Install Dependencies
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Mac/Linux
source .venv/bin/activate

pip install -r requirements.txt
```

#### 3. Set Up Environment Variables
Create a `.env` file in the root directory and add your API keys:
```env
# Gemini API (For Chunking & RAG LLM)
GEMINI_API_KEY=your_gemini_api_key_here

# Jina AI API (For Embeddings & Reranking)
jina=your_jina_api_key_here

# Qdrant Cloud (For Vector Database)
QDRANT_URL=https://your-cluster-url.aws.cloud.qdrant.io
QDRANT_API_KEY=your_qdrant_api_key_here
```

#### 4. Launch the App 🚀
```bash
python app.py
```
Open your browser and navigate to `http://localhost:7860`.

---

### 💡 How To Use

1. **Build the Knowledge Base:** Type a company name (e.g., "jp morgan", "nvidia") and the year (e.g., 2024). Click **🚀 Build Knowledge Base**. Watch the real-time logs as it processes the 10-K.
2. **Download the Raw Data:** Once the pipeline finishes processing, a download button for the raw `.md` file will appear.
3. **Chat:** Scroll down to the chat interface. Ask complex financial questions (e.g., *"What are the primary risk factors related to regulatory changes?"*).
4. **Verify Sources:** Check the right panel to see the exact Item, Headline, and Text chunk the AI used to formulate its answer. No more blind trust.

---

### 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
```
