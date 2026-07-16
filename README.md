<p align="center">
  <img src="PLACEHOLDER: AlphaLens logo — wordmark, transparent background, ~800×200px" alt="AlphaLens" width="420"/>
</p>

<h1 align="center">AlphaLens</h1>

<p align="center">
  <b>Retrieval-augmented question answering for SEC 10-K filings</b><br/>
  <sub>Structure-aware parsing · Source-grounded answers · Built for financial-grade traceability</sub>
</p>

<p align="center">
  <a href="https://huggingface.co/spaces/omkumar1729/new_s"><img src="https://img.shields.io/badge/-Live%20Demo-000000?style=for-the-badge&logo=huggingface&logoColor=white" alt="Live Demo"/></a>
  <a href="https://github.com/YOUR_USERNAME/AlphaLens"><img src="https://img.shields.io/github/stars/YOUR_USERNAME/AlphaLens?style=for-the-badge&color=f2f2f2&labelColor=000000" alt="Star on GitHub"/></a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/UI-Gradio-FF7C00?style=flat-square&logo=gradio&logoColor=white" alt="Gradio"/>
  <img src="https://img.shields.io/badge/LLM-Gemini-4285F4?style=flat-square&logo=googlegemini&logoColor=white" alt="Gemini"/>
  <img src="https://img.shields.io/badge/VectorDB-Qdrant-DC244C?style=flat-square" alt="Qdrant"/>
  <img src="https://img.shields.io/badge/Embeddings-Jina%20v4-000000?style=flat-square" alt="Jina"/>
  <img src="https://img.shields.io/badge/%F0%9F%A4%97-HF%20Spaces-yellow?style=flat-square" alt="HuggingFace"/>
  <img src="https://img.shields.io/badge/License-MIT-lightgrey?style=flat-square" alt="MIT License"/>
</p>

<p align="center">
  <a href="#why-alphalens">Why</a> ·
  <a href="#features">Features</a> ·
  <a href="#architecture">Architecture</a> ·
  <a href="#getting-started">Getting Started</a> ·
  <a href="#usage">Usage</a> ·
  <a href="#tech-stack">Tech Stack</a>
</p>

<br/>

<p align="center">
  <img src="PLACEHOLDER: hero banner — abstract visualization of a 10-K filing being parsed into structured, cited chunks, dark background, ~1200×400px" alt="AlphaLens hero banner" width="820"/>
</p>

<p align="center">
  <img src="PLACEHOLDER: product demo GIF — company entered → ingestion logs streaming → chat answer with cited source panel, ~900×550px" alt="AlphaLens demo" width="760"/>
</p>

<p align="center"><sub>Ask a question about any 10-K. Get an answer you can trace back to the exact Item, headline, and chunk it came from.</sub></p>

<br/>

---

## Project status

| | |
|---|---|
| **Status** | 🚧 Active development — interfaces and pipeline internals may change between versions |
| **Demo** | ✅ Live on Hugging Face Spaces |
| **Focus** | 📌 Retrieval quality and source traceability for financial filings |

<br/>

## Highlights

<table>
<tr>
<td width="50%" valign="top">

✓ Structure-aware parsing by SEC Item
✓ LLM-assisted semantic chunking with text-fidelity checks
✓ Headline and summary metadata generated per chunk
✓ Retry and backoff logic around external API calls

</td>
<td width="50%" valign="top">

✓ Query rewriting + dual vector retrieval
✓ Cross-encoder reranking before generation
✓ Every answer traceable to its source chunk

</td>
</tr>
</table>

<br/>

---

## Why AlphaLens?

> General-purpose RAG pipelines are usually built and tuned against blog posts, wikis, or support docs — content with loose structure, where an approximate chunk boundary costs little. A 10-K is a different kind of document: it has a fixed regulatory structure (Items 1, 1A, 7, etc.), dense tables, and risk-factor language where a misplaced chunk boundary or a paraphrased sentence can change the meaning of the answer.

Fixed-size, token-count chunking doesn't respect that structure. AlphaLens is built specifically around it — parsing by Item, chunking by meaning rather than token count, and keeping every answer traceable back to the exact passage it came from.

<br/>

| ⚠️ The problem | ✅ The solution |
|---|---|
| A generic RAG pipeline chunking a 10-K by token count will regularly split a table mid-row or cut a risk factor across two chunks. The retriever then returns fragments with no record of which SEC Item they belong to, and the LLM has to infer the missing context — which, for a financial filing, is exactly where an incorrect answer becomes hard to catch. | AlphaLens parses the filing by SEC Item before chunking, uses an LLM to identify semantic boundaries within each Item, and validates chunk text against the source to catch unintended edits during processing. Retrieval runs through a 6-step pipeline rather than a single similarity search, and every generated answer is linked back to the chunk, headline, and Item it was built from — so a claim can be checked rather than taken on faith. |

> [!NOTE]
> Chunk *extraction* is validated for text fidelity. Final *answer generation* is still performed by an LLM and should be treated the same as any LLM output — verify it against the cited source before relying on it.

<br/>

---

## Demo

<table>
<tr>
<td width="50%" align="center">
<img src="PLACEHOLDER: landing / hero UI screenshot" width="380"/><br/>
<sub><b>Landing UI</b></sub>
</td>
<td width="50%" align="center">
<img src="PLACEHOLDER: ingestion pipeline logs screenshot" width="380"/><br/>
<sub><b>Ingestion Pipeline</b></sub>
</td>
</tr>
<tr>
<td width="50%" align="center">
<img src="PLACEHOLDER: chat interface screenshot" width="380"/><br/>
<sub><b>Chat</b></sub>
</td>
<td width="50%" align="center">
<img src="PLACEHOLDER: source verification panel screenshot" width="380"/><br/>
<sub><b>Source Verification</b></sub>
</td>
</tr>
</table>

<p align="center"><a href="https://huggingface.co/spaces/omkumar1729/new_s"><b>→ Try it live on Hugging Face Spaces</b></a></p>

<br/>

---

## Features

### 📄 Ingestion you can audit

<table>
<tr>
<td width="50%" valign="top">
<h4>Structure-aware parsing</h4>
Filings are split along actual SEC Items instead of arbitrary token windows.
<br/><br/>
<sub><b>Why it matters —</b> a "risk factors" answer isn't stitched together from unrelated sections.</sub>
</td>
<td width="50%" valign="top">
<h4>Semantic chunking</h4>
Chunk boundaries follow the meaning of the text within each Item.
<br/><br/>
<sub><b>Why it matters —</b> reduces mid-sentence and mid-table splits.</sub>
</td>
</tr>
<tr>
<td width="50%" valign="top">
<h4>Text-fidelity checks</h4>
Extracted chunk text is checked against the source during ingestion.
<br/><br/>
<sub><b>Why it matters —</b> processing errors are caught rather than silently passed downstream.</sub>
</td>
<td width="50%" valign="top">
<h4>Per-chunk metadata</h4>
Each chunk carries an LLM-generated headline and summary, embedded alongside the raw text.
<br/><br/>
<sub><b>Why it matters —</b> improves retrieval relevance.</sub>
</td>
</tr>
</table>

### 🔍 Retrieval you can trace

<table>
<tr>
<td width="50%" valign="top">
<h4>Query rewriting</h4>
The question is reformulated for vector search.
<br/><br/>
<sub><b>Why it matters —</b> improves recall on phrasing the filing itself wouldn't use.</sub>
</td>
<td width="50%" valign="top">
<h4>Dual retrieval</h4>
Both the original and rewritten queries are searched independently.
<br/><br/>
<sub><b>Why it matters —</b> widens the candidate pool.</sub>
</td>
</tr>
<tr>
<td width="50%" valign="top">
<h4>Merge & deduplicate</h4>
Overlapping results from both passes are combined into a single ranked set.
<br/><br/>
<sub><b>Why it matters —</b> no redundant context reaches generation.</sub>
</td>
<td width="50%" valign="top">
<h4>Cross-encoder reranking</h4>
A Jina reranker scores every candidate for relevance before it reaches the generation step.
<br/><br/>
<sub><b>Why it matters —</b> only the most relevant chunks reach the LLM.</sub>
</td>
</tr>
<tr>
<td colspan="2" valign="top">
<h4>Source-grounded answers</h4>
Each answer is generated from the top-ranked chunks, and the UI surfaces the exact Item and headline behind it.
<br/><br/>
<sub><b>Why it matters —</b> every claim can be traced back and checked.</sub>
</td>
</tr>
</table>

<br/>

> [!TIP]
> **Handling for unreliable dependencies** — Embedding, reranking, and generation all depend on external APIs. AlphaLens wraps these calls with retry and exponential-backoff logic and handles common cold-start delays on hosted inference — reducing, though not eliminating, the impact of transient API failures.

<br/>

---

## Architecture

At a high level: a filing goes in, gets parsed and chunked by SEC Item, and is embedded into Qdrant. A question goes through query rewriting, dual retrieval against that same index, reranking, and finally generation — with the source chunks surfaced alongside the answer.

<p align="center">
  <img src="PLACEHOLDER: high-level architecture diagram — user → ingestion pipeline → Qdrant → RAG orchestrator → chat UI, full-width ~1200×500px" alt="Architecture overview" width="100%"/>
</p>
<p align="center"><sub>End-to-end flow: ingestion builds the index, the RAG orchestrator answers against it.</sub></p>

<br/>

<details>
<summary><b>🔧 Ingestion pipeline</b> — how the knowledge base is built</summary>
<br/>

<p align="center">
  <img src="PLACEHOLDER: ingestion pipeline diagram — Ticker lookup → Download → Parse → Chunk → Embed, full-width" width="100%"/>
</p>

| Step | What happens |
|---|---|
| **1. Ticker lookup** | Resolve the company name against SEC EDGAR |
| **2. Download** | Pull the raw 10-K filing |
| **3. Structure-aware parsing** | Extract SEC Items, merge undersized sections |
| **4. Semantic chunking** | LLM-identified boundaries, text-fidelity check, headline/summary generation |
| **5. Embed & upload** | Jina v4 embeddings upserted to Qdrant Cloud |

</details>

<details>
<summary><b>🧠 RAG orchestrator</b> — how questions are answered</summary>
<br/>

<p align="center">
  <img src="PLACEHOLDER: retrieval pipeline diagram — Rewrite → Dual retrieval → Merge → Rerank → Generate, full-width" width="100%"/>
</p>

| Step | What happens |
|---|---|
| **1. Query rewriting** | Reformulate the question for vector search |
| **2. Dual retrieval** | Search original + rewritten query against Qdrant |
| **3. Merge & deduplicate** | Combine both result sets |
| **4. Cross-encoder reranking** | Score candidates, keep the top-N |
| **5. Generation** | Build the prompt from context + history, generate a source-grounded answer |

</details>

<br/>

---

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

---

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

---

## Getting started

```bash
git clone https://github.com/YOUR_USERNAME/AlphaLens.git
cd AlphaLens
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your_gemini_api_key
jina=your_jina_api_key
QDRANT_URL=https://your-cluster-url.aws.cloud.qdrant.io
QDRANT_API_KEY=your_qdrant_api_key
```

Launch:

```bash
python app.py
```

Open `http://localhost:7860`.

<br/>

---

## Usage

| Step | Action |
|---|---|
| **1. Build a knowledge base** | Enter a company and year, e.g. `nvidia`, `2024`, then select **Build Knowledge Base**. Ingestion progress streams live in the log panel. |
| **2. Download the parsed filing** | Once ingestion finishes, the processed `.md` file is available for download. |
| **3. Ask a question** | For example: *"What are the primary risk factors related to regulatory changes?"* |
| **4. Check the sources** | The source panel lists the exact Item, headline, and chunk text behind the answer, so you can verify it against the original filing before relying on it. |

<br/>

---

## Project structure

```text
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
```

<br/>

---

## Acknowledgements

AlphaLens is built on top of [Gradio](https://gradio.app/), [LiteLLM](https://github.com/BerriAI/litellm), [Google Gemini](https://ai.google.dev/), [Jina AI](https://jina.ai/) (embeddings and reranking), [Qdrant](https://qdrant.tech/), and [edgartools](https://github.com/dgunning/edgartools) for SEC EDGAR access.

<br/>

## License

MIT — see [LICENSE](LICENSE).

<br/>

---

## Recommended visual assets

The layout above assumes the following assets. Swap in real files as they're produced; each placeholder above is labeled with its intended dimensions and location.

- [ ] **Logo** — wordmark, transparent PNG/SVG, ~800×200px → hero section
- [ ] **Hero banner** — abstract visualization of a filing being parsed into structured, cited chunks, ~1200×400px → top of hero, below badges/nav
- [ ] **Demo GIF** — company entered → logs streaming → chat answer with source panel, ~900×550px → hero section, below banner
- [ ] **Architecture diagram** — full pipeline overview, full-width → Architecture section
- [ ] **Ingestion pipeline diagram** — 3-stage flow (parse → chunk → embed) → inside "Ingestion pipeline" collapsible
- [ ] **Retrieval pipeline diagram** — 5-step flow (rewrite → retrieve → merge → rerank → generate) → inside "RAG orchestrator" collapsible
- [ ] **Landing UI screenshot** → Demo gallery
- [ ] **Chat screenshot** → Demo gallery
- [ ] **Source verification screenshot** → Demo gallery
- [ ] **Social preview image (OpenGraph)** — 1280×640px → repository settings
- [ ] **Favicon** — if paired with a docs site or standalone Space
