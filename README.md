<p align="center">
  <img src="PLACEHOLDER: AlphaLens logo (wordmark, transparent background, ~800x200px)" alt="AlphaLens" width="480"/>
</p>

<h1 align="center">AlphaLens</h1>
<p align="center"><b>A retrieval-augmented question-answering system for SEC 10-K filings, built around structure-aware parsing and source-grounded answers.</b></p>

<p align="center">
  <a href="https://huggingface.co/spaces/omkumar1729/new_s"><img src="https://img.shields.io/badge/🚀-Live%20Demo-brightgreen?style=for-the-badge" alt="Live Demo"/></a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/UI-Gradio-FF7C00?style=flat-square&logo=gradio&logoColor=white" alt="Gradio"/>
  <img src="https://img.shields.io/badge/LLM-Gemini-4285F4?style=flat-square&logo=googlegemini&logoColor=white" alt="Gemini"/>
  <img src="https://img.shields.io/badge/VectorDB-Qdrant-DC244C?style=flat-square" alt="Qdrant"/>
  <img src="https://img.shields.io/badge/Embeddings-Jina%20v4-000000?style=flat-square" alt="Jina"/>
  <img src="https://img.shields.io/badge/🤗-HF%20Spaces-yellow?style=flat-square" alt="HuggingFace"/>
  <img src="https://img.shields.io/badge/License-MIT-lightgrey?style=flat-square" alt="MIT License"/>
</p>

<p align="center">
  <img src="PLACEHOLDER: product demo GIF — company entered, ingestion logs streaming, then a chat answer with cited source panel" alt="AlphaLens demo" width="800"/>
</p>

<br/>

## Project status

🚧 **Active development** — interfaces and pipeline internals may change between versions.
✅ **Live demo available** on Hugging Face Spaces.
📌 **Current focus:** retrieval quality and source traceability for financial filings.

<br/>

## Highlights

✓ Structure-aware parsing by SEC Item
✓ LLM-assisted semantic chunking with text-fidelity checks
✓ Headline and summary metadata generated per chunk
✓ Query rewriting + dual vector retrieval
✓ Cross-encoder reranking before generation
✓ Every answer traceable to its source chunk
✓ Retry and backoff logic around external API calls

<br/>

## Why AlphaLens?

General-purpose RAG pipelines are usually built and tuned against blog posts, wikis, or support docs — content with loose structure, where an approximate chunk boundary costs little. A 10-K is a different kind of document: it has a fixed regulatory structure (Items 1, 1A, 7, etc.), dense tables, and risk-factor language where a misplaced chunk boundary or a paraphrased sentence can change the meaning of the answer.

Fixed-size, token-count chunking doesn't respect that structure. AlphaLens is built specifically around it — parsing by Item, chunking by meaning rather than token count, and keeping every answer traceable back to the exact passage it came from.

## The problem

A generic RAG pipeline chunking a 10-K by token count will regularly split a table mid-row or cut a risk factor across two chunks. The retriever then returns fragments with no record of which SEC Item they belong to, and the LLM has to infer the missing context — which, for a financial filing, is exactly where an incorrect answer becomes hard to catch.

## The solution

AlphaLens parses the filing by SEC Item before chunking, uses an LLM to identify semantic boundaries within each Item, and validates chunk text against the source to catch unintended edits during processing. Retrieval runs through a 6-step pipeline rather than a single similarity search, and every generated answer is linked back to the chunk, headline, and Item it was built from — so a claim can be checked rather than taken on faith.

> Note: chunk *extraction* is validated for text fidelity. Final *answer generation* is still performed by an LLM and should be treated the same as any LLM output — verify it against the cited source before relying on it.

<br/>

## Demo

| Ingestion (real-time logs) | Chat + Source Verification |
| :---: | :---: |
| `PLACEHOLDER: screenshot of ingestion pipeline logs` | `PLACEHOLDER: screenshot of chat UI with source panel` |

**[→ Try it live on Hugging Face Spaces](https://huggingface.co/spaces/omkumar1729/new_s)**

<br/>

## Features

### 📄 Ingestion you can audit

| What you get | Why it matters |
|---|---|
| **Structure-aware parsing** | Filings are split along actual SEC Items instead of arbitrary token windows, so a "risk factors" answer isn't stitched together from unrelated sections. |
| **Semantic chunking** | Chunk boundaries follow the meaning of the text within each Item, reducing mid-sentence and mid-table splits. |
| **Text-fidelity checks** | Extracted chunk text is checked against the source during ingestion, so processing errors are caught rather than silently passed downstream. |
| **Per-chunk metadata** | Each chunk carries an LLM-generated headline and summary, embedded alongside the raw text to improve retrieval relevance. |

### 🔍 Retrieval you can trace

| What you get | Why it matters |
|---|---|
| **Query rewriting** | The question is reformulated for vector search, improving recall on phrasing the filing itself wouldn't use. |
| **Dual retrieval** | Both the original and rewritten queries are searched independently, widening the candidate pool. |
| **Merge & deduplicate** | Overlapping results from both passes are combined into a single ranked set. |
| **Cross-encoder reranking** | A Jina reranker scores every candidate for relevance before it reaches the generation step. |
| **Source-grounded answers** | Each answer is generated from the top-ranked chunks, and the UI surfaces the exact Item and headline behind it. |

### 🛡️ Handling for unreliable dependencies

Embedding, reranking, and generation all depend on external APIs. AlphaLens wraps these calls with retry and exponential-backoff logic and handles common cold-start delays on hosted inference — reducing, though not eliminating, the impact of transient API failures.

<br/>

## Architecture

At a high level: a filing goes in, gets parsed and chunked by SEC Item, and is embedded into Qdrant. A question goes through query rewriting, dual retrieval against that same index, reranking, and finally generation — with the source chunks surfaced alongside the answer.

`PLACEHOLDER: high-level architecture diagram — user → ingestion pipeline → Qdrant → RAG orchestrator → chat UI`

<details>
<summary><b>Ingestion pipeline</b> — how the knowledge base is built</summary>
<br/>

`PLACEHOLDER: ingestion pipeline diagram`

1. **Ticker lookup** — resolve the company name against SEC EDGAR
2. **Download** — pull the raw 10-K filing
3. **Stage 1 — Structure-aware parsing** — extract SEC Items, merge undersized sections
4. **Stage 2 — Semantic chunking** — LLM-identified boundaries, text-fidelity check, headline/summary generation
5. **Stage 3 — Embed & upload** — Jina v4 embeddings upserted to Qdrant Cloud

</details>

<details>
<summary><b>RAG orchestrator</b> — how questions are answered</summary>
<br/>

`PLACEHOLDER: retrieval pipeline diagram`

1. **Query rewriting** — reformulate the question for vector search
2. **Dual retrieval** — search original + rewritten query against Qdrant
3. **Merge & deduplicate** — combine both result sets
4. **Cross-encoder reranking** — score candidates, keep the top-N
5. **Generation** — build the prompt from context + history, generate a source-grounded answer

</details>

<br/>

## Example workflow

```
Company:              NVIDIA, FY2024
        │
        ▼
Knowledge base build:  10-K downloaded → parsed by Item → chunked →
                        embedded → indexed in Qdrant
        │
        ▼
User question:         "What are the primary risk factors related to
                        regulatory changes?"
        │
        ▼
Retrieved sources:     Item 1A – Risk Factors › "Government Regulation" (chunk 14)
                        Item 1A – Risk Factors › "Export Controls" (chunk 21)
        │
        ▼
Generated answer:      Summary of the regulatory risks, with each claim
                        linked back to its source chunk above
```

<br/>

## Tech stack

| Layer | Technology |
|---|---|
| **Interface** | Gradio |
| **LLM orchestration** | LiteLLM |
| **Reasoning & chunking** | Google Gemini 3.1 Flash Lite |
| **Embeddings** | Jina Embeddings v4 |
| **Reranking** | Jina Reranker (cross-encoder) |
| **Vector store** | Qdrant Cloud |
| **Validation** | Pydantic |
| **Resiliency** | Tenacity |
| **Filing source** | edgartools (SEC EDGAR) |

<br/>

## Getting started

\`\`\`bash
git clone https://github.com/YOUR_USERNAME/AlphaLens.git
cd AlphaLens
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
\`\`\`

Create a \`.env\` file in the project root:

\`\`\`env
GEMINI_API_KEY=your_gemini_api_key
jina=your_jina_api_key
QDRANT_URL=https://your-cluster-url.aws.cloud.qdrant.io
QDRANT_API_KEY=your_qdrant_api_key
\`\`\`

Launch:

\`\`\`bash
python app.py
\`\`\`

Open \`http://localhost:7860\`.

<br/>

## Usage

1. **Build a knowledge base** — enter a company and year, e.g. \`nvidia\`, \`2024\`, then select **Build Knowledge Base**. Ingestion progress streams live in the log panel.
2. **Download the parsed filing** — once ingestion finishes, the processed \`.md\` file is available for download.
3. **Ask a question** — for example: *"What are the primary risk factors related to regulatory changes?"*
4. **Check the sources** — the source panel lists the exact Item, headline, and chunk text behind the answer, so you can verify it against the original filing before relying on it.

<br/>

## Project structure

\`\`\`text
AlphaLens/
├── app.py                  # Gradio entry point
├── master_pipeline.py      # Ingestion orchestrator
│
├── ingest/                 # Parsing → chunking → embedding
│   ├── parsing.py
│   ├── stage_2_worker.py
│   └── stage_3_embed.py
│
├── rag_orchestrator/       # 6-step retrieval engine
│   ├── pipeline.py
│   ├── rewrite.py
│   ├── retriever.py
│   ├── merger.py
│   ├── reranker.py
│   ├── prompt_builder.py
│   └── generator.py
│
└── Knowledge-base/         # Ingested filings + vector data
\`\`\`

<br/>

## Acknowledgements

AlphaLens is built on top of [Gradio](https://gradio.app/), [LiteLLM](https://github.com/BerriAI/litellm), [Google Gemini](https://ai.google.dev/), [Jina AI](https://jina.ai/) (embeddings and reranking), [Qdrant](https://qdrant.tech/), and [edgartools](https://github.com/dgunning/edgartools) for SEC EDGAR access.

<br/>

## License

MIT — see [LICENSE](LICENSE).
