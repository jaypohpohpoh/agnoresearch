# SME Research Agent

Research Singapore SME prospects for AI adoption opportunities.

## Requirements

- Python 3.11+
- [Ollama](https://ollama.ai) with models:
  - `qwen2.5:14b` (main LLM)
  - `nomic-embed-text` (embeddings)
- [uv](https://docs.astral.sh/uv/) package manager

## Setup

```bash
# Install dependencies
uv sync

# Pull required Ollama models
ollama pull qwen2.5:14b
ollama pull nomic-embed-text
```

## Run

```bash
make run
# or
uv run streamlit run app.py
```

Open http://localhost:8501 in your browser.

## Usage

1. **Upload Knowledge Base** (sidebar): Add pitch decks, case studies, service offerings (PDF, TXT, MD)
2. **Enter Company URLs**: Website (required), Instagram, Facebook (optional)
3. **Click Research**: Agent browses URLs and identifies AI adoption opportunities

## Project Structure

```
src/agnoresearch/
├── agent.py      # Research agent factory
├── knowledge.py  # LanceDB knowledge base
├── prompts.py    # System prompts
├── schemas.py    # Pydantic models
└── tools.py      # Crawl4AI browser tool
app.py            # Streamlit UI
```
