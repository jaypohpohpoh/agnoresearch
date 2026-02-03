---
title: "feat: Agno SME Research Agent for AI Adoption Consulting"
type: feat
date: 2026-02-03
deepened: 2026-02-03
---

# Agno SME Research Agent for AI Adoption Consulting

## Enhancement Summary

**Deepened on:** 2026-02-03
**Research agents used:** framework-docs-researcher, agent-native-architecture, kieran-python-reviewer, architecture-strategist, code-simplicity-reviewer, best-practices-researcher, Context7

### Key Improvements
1. **Input changed:** Team provides specific URLs (website + Instagram + Facebook) instead of just company name
2. **Browser tool:** Use Crawl4AI (native Python, free) for URL scraping instead of DuckDuckGo search
3. **UI:** Streamlit form with 3 URL fields + knowledge base upload
4. **Knowledge base:** Team can upload pitch decks, case studies, service offerings for personalized output
5. **Future-ready:** Architecture designed for adding Writer agent for personalized outreach

### New Considerations Discovered
- Agno API uses `output_schema` not `response_model` (API changed)
- Instagram/Facebook scraping has anti-bot challenges - plan for graceful degradation
- Vercel agent-browser is CLI-only; Crawl4AI is native Python and simpler

---

## Overview

Build a research agent using Agno framework + local Ollama LLM that helps the Growth Foundry team research Singapore SME prospects for AI adoption consulting. The team inputs company URLs (website, Instagram, Facebook), and the agent extracts business information and identifies AI adoption opportunities.

## Problem Statement / Motivation

Growth Foundry is an AI consultancy helping Singapore SMEs adopt AI. Before client meetings, the team needs to:
- Research the company's business model and market position
- Understand their current digital/tech maturity from their online presence
- Identify specific AI adoption opportunities relevant to their industry
- Prepare personalized outreach and talking points

Currently this is manual research that takes significant time. An AI research agent can accelerate this prep work while keeping data local (privacy) and costs low (no API fees beyond Ollama).

**Future need:** Writer agent to draft personalized outreach emails based on research findings.

## Proposed Solution

A single-agent Agno application with:
- **Ollama backend** (`qwen2.5:14b`) for local, private LLM inference
- **Crawl4AI** for browsing and extracting content from provided URLs
- **LanceDB + Ollama embeddings** for knowledge base (pitch decks, case studies, service offerings)
- **Streamlit UI** for team to input URLs, upload knowledge base files, and view results
- **Pydantic structured output** for consistent research reports
- **Designed for future:** Writer agent for personalized outreach drafts

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Streamlit UI                                │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │  Website URL:    [________________________]              │   │
│   │  Instagram URL:  [________________________]              │   │
│   │  Facebook URL:   [________________________]              │   │
│   │                                                          │   │
│   │  Knowledge Base: [📁 Upload files] pitch.pdf, cases.pdf │   │
│   │                                                          │   │
│   │  [  Research  ]                                          │   │
│   └─────────────────────────────────────────────────────────┘   │
│                              │                                   │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │  Progress: ████████████░░░░░ Analyzing website...       │   │
│   └─────────────────────────────────────────────────────────┘   │
│                              │                                   │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │  ## Research Report                                      │   │
│   │  **Company:** ABC Pte Ltd                               │   │
│   │  **Industry:** F&B                                      │   │
│   │  **AI Opportunities:**                                  │   │
│   │  1. Customer service chatbot (Low complexity)           │   │
│   │  2. Inventory forecasting (Medium complexity)           │   │
│   │  **Recommended Services:** (from knowledge base)        │   │
│   │  - AI Chatbot Implementation Package                    │   │
│   └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Research Agent (Agno)                         │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Model: Ollama (qwen2.5:14b)                              │  │
│  │  Output: CompanyResearchReport (Pydantic)                 │  │
│  │  Knowledge: LanceDB + Ollama embeddings                   │  │
│  │  Storage: SQLite (session history)                        │  │
│  └───────────────────────────────────────────────────────────┘  │
│                              │                                   │
│      ┌───────────────────────┼───────────────────────┐          │
│      ▼                       ▼                       ▼          │
│  ┌─────────┐          ┌───────────┐          ┌───────────┐      │
│  │ browse  │          │  search   │          │ browse    │      │
│  │ _url    │          │ _knowledge│          │ _url      │      │
│  └─────────┘          └───────────┘          └───────────┘      │
│      │                       │                       │          │
│      ▼                       ▼                       ▼          │
│  Crawl4AI              LanceDB                  Crawl4AI        │
│  (website)         (pitch decks,            (social media)      │
│                    case studies)                                │
└─────────────────────────────────────────────────────────────────┘
```

### Research Insights

**Why Crawl4AI over Vercel agent-browser:**
- Native Python library (no subprocess wrapper needed)
- Outputs clean markdown (LLM-ready)
- Async API with Playwright under the hood
- Free and open source (58K+ GitHub stars)
- Vercel agent-browser is CLI-only, requires shell wrapper

**Why Streamlit over Agno Playground:**
- Agno Playground is a **chat interface** - no custom form fields
- Streamlit supports structured 3-field input form
- Built-in progress indicators and streaming
- Fastest path to working team UI (~30 lines of code)
- Free hosting on Streamlit Cloud

---

## Technical Considerations

### Why Agno?
- Native Ollama support (no adapters needed)
- Clean tool abstraction for browser automation
- Pydantic structured outputs (`output_schema`)
- Active development (v2.4.7 as of Jan 2026)
- Supports future multi-agent teams

### Why Ollama + qwen2.5:14b?
- **Best structured output** - Qwen 2.5 excels at JSON/Pydantic schema generation
- **14B sweet spot** - Better reasoning than 7B/8B, faster than 20B
- Runs locally (client data stays private)
- No API costs (unlimited queries)
- Recent model (late 2025) with strong instruction following

**Installed models on this machine:**
| Model | Size | Notes |
|-------|------|-------|
| qwen2.5:14b | 9GB | **Selected** - best for structured output |
| qwen2.5:7b-instruct | 4.7GB | Fallback if 14B is too slow |
| llama3.1:8b | 4.9GB | Alternative if Qwen has issues |
| gpt-oss:20b | 13GB | Too slow for quick research |

### Known Limitations & Mitigations

| Limitation | Mitigation |
|------------|------------|
| **Instagram anti-bot** | Extract visible public content only; screenshot fallback |
| **Facebook anti-bot** | Extract public page info; graceful "limited data" message |
| **English only** | Skip Chinese content in v1; note as research limitation |
| **Model quality** | Using qwen2.5:14b; fallback to 7b-instruct if too slow |

### Research Insights: Social Media Scraping

**Critical warning from research:** Instagram and Facebook actively block scrapers with:
- IP quality detection
- TLS fingerprinting
- Rate limiting
- Behavioral analysis

**Recommended approach for v1:**
1. Use Crawl4AI to fetch public page content
2. If blocked, take screenshot and extract visible text
3. Report "limited data available" rather than failing
4. Consider official Graph APIs for v2 if authorized access available

---

## Acceptance Criteria

### Setup & Infrastructure
- [ ] Project initializes with `uv` package manager
- [ ] Ollama installed and running with `qwen2.5:14b` model
- [ ] Ollama embedding model installed (`nomic-embed-text`)
- [ ] Crawl4AI installed and working
- [ ] LanceDB initializes without errors
- [ ] Agno agent starts without errors
- [ ] Streamlit UI accessible at localhost:8501

### Knowledge Base
- [ ] File upload works in Streamlit sidebar (PDF, TXT, MD)
- [ ] Uploaded files are saved to `data/knowledge/`
- [ ] Files are indexed in LanceDB vector store
- [ ] Agent retrieves relevant knowledge during research
- [ ] Knowledge persists across app restarts

### Core Research Flow
- [ ] Team inputs website URL (required) + Instagram/Facebook URLs (optional)
- [ ] Agent browses each provided URL using Crawl4AI
- [ ] Agent extracts content and converts to markdown
- [ ] Agent produces structured `CompanyResearchReport`
- [ ] Research completes in < 3 minutes for typical company

### Report Quality
- [ ] Report contains company overview section
- [ ] Report identifies 2+ AI opportunities (when data supports)
- [ ] Opportunities are contextually relevant to Singapore SMEs
- [ ] Report includes source URLs for each finding
- [ ] Output renders as readable markdown in Streamlit

### Error Handling
- [ ] Graceful message when URL is inaccessible
- [ ] Graceful handling when social media blocks scraping
- [ ] Agent doesn't hang indefinitely (30s timeout per URL)
- [ ] Clear "insufficient data" message when content is sparse

### Deferred to v2
- [ ] Writer agent for personalized outreach drafts
- [ ] Batch processing multiple companies
- [ ] Persistent storage/search of past research
- [ ] Chinese language content support
- [ ] Official Instagram/Facebook Graph API integration
- [ ] PDF export

---

## Project Structure

```
agnoresearch/
├── pyproject.toml           # Project config (uv)
├── .python-version          # Python version (3.11+)
├── README.md                # Setup instructions
├── .env.example             # Environment template
│
├── src/
│   └── agnoresearch/
│       ├── __init__.py
│       ├── agent.py         # SME Research Agent definition
│       ├── schemas.py       # Pydantic input/output schemas
│       ├── tools.py         # Crawl4AI browser tool wrapper
│       ├── knowledge.py     # Knowledge base management
│       └── prompts.py       # System prompts and instructions
│
├── app.py                   # Streamlit UI entry point
│
├── data/
│   ├── agents.db            # SQLite session storage
│   ├── lancedb/             # Vector database storage
│   └── knowledge/           # Uploaded knowledge base files
│       ├── pitch-deck.pdf   # Example: company pitch deck
│       ├── case-studies.pdf # Example: client case studies
│       └── services.pdf     # Example: service offerings
│
└── docs/
    └── plans/               # Planning documents
```

---

## Implementation Plan

### Phase 1: Project Setup

**Files:** `pyproject.toml`, `.python-version`, `README.md`, `.env.example`

- [ ] Initialize project with `uv init`
- [ ] Add dependencies: `agno`, `ollama`, `crawl4ai`, `streamlit`
- [ ] Create README with Ollama setup instructions
- [ ] Verify Ollama is running with correct model
- [ ] Test Crawl4AI can fetch a sample URL

### Phase 2: Core Agent

**Files:** `src/agnoresearch/schemas.py`, `src/agnoresearch/tools.py`, `src/agnoresearch/prompts.py`, `src/agnoresearch/agent.py`

- [ ] Define `ResearchTarget` input schema (website, instagram, facebook URLs)
- [ ] Define `CompanyResearchReport` output schema
- [ ] Create `browse_url` tool wrapping Crawl4AI
- [ ] Write system prompt tuned for Singapore SME AI consulting
- [ ] Create agent with browse tools and structured output
- [ ] Test agent via CLI (`agent.print_response()`)

### Phase 2.5: Knowledge Base

**Files:** `src/agnoresearch/knowledge.py`

- [ ] Set up LanceDB for local vector storage
- [ ] Configure Ollama embeddings (`nomic-embed-text` model)
- [ ] Create knowledge base initialization function
- [ ] Create function to add PDF/text files to knowledge base
- [ ] Integrate knowledge base with agent (`search_knowledge=True`)
- [ ] Test knowledge retrieval with sample documents

### Phase 3: Streamlit UI

**Files:** `app.py`

- [ ] Create 3-field form (website URL required, social URLs optional)
- [ ] Add progress indicator during research
- [ ] Display structured report with formatting
- [ ] Handle errors gracefully with user-friendly messages
- [ ] Test full flow through UI

### Phase 4: Polish & Documentation

**Files:** `README.md`, `Makefile`

- [ ] Add startup script / Makefile commands
- [ ] Document common issues and solutions
- [ ] Test with 5 real Singapore SMEs
- [ ] Tune prompts based on output quality

---

## MVP Code

### schemas.py

```python
"""Pydantic schemas for research agent input/output."""

from pydantic import BaseModel, Field, HttpUrl
from typing import Optional


class ResearchTarget(BaseModel):
    """Input: URLs to research for a company."""

    website_url: HttpUrl = Field(..., description="Company website URL (required)")
    instagram_url: Optional[HttpUrl] = Field(None, description="Instagram profile URL")
    facebook_url: Optional[HttpUrl] = Field(None, description="Facebook page URL")

    def get_urls(self) -> list[str]:
        """Return all non-null URLs as strings."""
        urls = [str(self.website_url)]
        if self.instagram_url:
            urls.append(str(self.instagram_url))
        if self.facebook_url:
            urls.append(str(self.facebook_url))
        return urls


class AIOpportunity(BaseModel):
    """A specific AI adoption opportunity for the SME."""

    area: str = Field(..., description="Business area (e.g., 'Customer Service', 'Operations')")
    opportunity: str = Field(..., description="Specific AI application")
    rationale: str = Field(..., description="Why this fits their business based on research")
    complexity: str = Field(..., description="Low/Medium/High implementation complexity")


class SocialMediaInsight(BaseModel):
    """Insights extracted from social media presence."""

    platform: str = Field(..., description="instagram or facebook")
    followers: Optional[str] = Field(None, description="Follower count if visible")
    posting_frequency: Optional[str] = Field(None, description="How often they post")
    content_themes: list[str] = Field(default_factory=list, description="Main topics they post about")
    engagement_level: Optional[str] = Field(None, description="High/Medium/Low based on likes/comments")


class CompanyResearchReport(BaseModel):
    """Structured output: Research report for an SME prospect."""

    company_name: str = Field(..., description="Company name as discovered")
    industry: str = Field(..., description="Primary industry/sector")

    # Section 1: Company Overview
    overview: str = Field(..., description="What the company does, size indicators, market position")

    # Section 2: Products/Services
    products_services: list[str] = Field(default_factory=list, description="Main offerings")

    # Section 3: Digital Presence
    digital_maturity: str = Field(..., description="Assessment of tech adoption based on online presence")
    social_insights: list[SocialMediaInsight] = Field(default_factory=list)

    # Section 4: AI Opportunities
    ai_opportunities: list[AIOpportunity] = Field(..., description="Ranked AI adoption opportunities")

    # Section 5: Outreach Hooks
    outreach_hooks: list[str] = Field(
        default_factory=list,
        description="Personalization angles for outreach based on research"
    )

    # Section 6: Sources
    sources: list[str] = Field(..., description="URLs that were successfully scraped")

    # Metadata
    data_quality: str = Field(..., description="High/Medium/Low based on available info")
    research_notes: Optional[str] = Field(None, description="Any caveats, limitations, or gaps")
```

### knowledge.py

```python
"""Knowledge base management using LanceDB + Ollama embeddings."""

import asyncio
from pathlib import Path
from agno.knowledge.knowledge import Knowledge
from agno.vectordb.lancedb import LanceDb
from agno.embedder.ollama import OllamaEmbedder


def create_knowledge_base(
    db_path: Path | None = None,
    embedder_model: str = "nomic-embed-text",
) -> Knowledge:
    """
    Create a knowledge base for storing pitch decks, case studies, etc.

    Args:
        db_path: Path for LanceDB storage. Defaults to ./data/lancedb
        embedder_model: Ollama embedding model. Defaults to nomic-embed-text

    Returns:
        Configured Knowledge instance.
    """
    if db_path is None:
        db_path = Path.cwd() / "data" / "lancedb"

    db_path.mkdir(parents=True, exist_ok=True)

    return Knowledge(
        name="Growth Foundry Knowledge Base",
        description="Company pitch decks, case studies, service offerings, and AI solution templates",
        vector_db=LanceDb(
            table_name="knowledge_vectors",
            uri=str(db_path),
            embedder=OllamaEmbedder(id=embedder_model),
        ),
    )


async def add_document_to_knowledge(
    knowledge: Knowledge,
    file_path: Path,
    doc_type: str = "general",
) -> None:
    """
    Add a document (PDF, TXT, MD) to the knowledge base.

    Args:
        knowledge: Knowledge instance.
        file_path: Path to the document.
        doc_type: Type of document (pitch_deck, case_study, services, general).
    """
    await knowledge.add_content_async(
        name=file_path.stem,
        path=str(file_path),
        metadata={"doc_type": doc_type, "filename": file_path.name},
    )


def add_document_sync(knowledge: Knowledge, file_path: Path, doc_type: str = "general") -> None:
    """Synchronous wrapper for adding documents."""
    asyncio.run(add_document_to_knowledge(knowledge, file_path, doc_type))
```

### tools.py

```python
"""Browser tool using Crawl4AI for URL scraping."""

import asyncio
from agno.tools import tool


@tool
def browse_url(url: str) -> str:
    """
    Browse a URL and extract its content as markdown.

    Args:
        url: The URL to browse and extract content from.

    Returns:
        Markdown content from the page, or error message if failed.
    """
    return asyncio.run(_browse_url_async(url))


async def _browse_url_async(url: str, timeout: int = 30) -> str:
    """Async implementation of URL browsing."""
    try:
        from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode

        browser_config = BrowserConfig(
            headless=True,
            verbose=False,
        )

        crawler_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,  # Always fetch fresh
            wait_until="networkidle",
            page_timeout=timeout * 1000,  # Convert to ms
        )

        async with AsyncWebCrawler(config=browser_config) as crawler:
            result = await crawler.arun(url=url, config=crawler_config)

            if result.success:
                # Return markdown content (LLM-ready)
                content = result.markdown or result.cleaned_html or ""

                # Truncate if too long (keep first 10K chars for LLM context)
                if len(content) > 10000:
                    content = content[:10000] + "\n\n[Content truncated...]"

                return f"# Content from {url}\n\n{content}"
            else:
                return f"Failed to fetch {url}: {result.error_message or 'Unknown error'}"

    except ImportError:
        return "Error: crawl4ai not installed. Run: pip install crawl4ai"
    except Exception as e:
        return f"Error browsing {url}: {str(e)}"
```

### agent.py

```python
"""SME Research Agent definition."""

from pathlib import Path

from agno.agent import Agent
from agno.models.ollama import Ollama
from agno.db.sqlite import SqliteDb
from agno.knowledge.knowledge import Knowledge

from .schemas import CompanyResearchReport
from .tools import browse_url
from .knowledge import create_knowledge_base
from .prompts import SYSTEM_PROMPT, INSTRUCTIONS


def create_research_agent(
    *,
    model_id: str = "qwen2.5:14b",
    db_path: Path | None = None,
    knowledge: Knowledge | None = None,
) -> Agent:
    """
    Create the SME Research Agent.

    Args:
        model_id: Ollama model identifier.
        db_path: Path for SQLite storage. Defaults to ./data/agents.db
        knowledge: Optional pre-configured knowledge base.

    Returns:
        Configured Agent instance.
    """
    if db_path is None:
        db_path = Path.cwd() / "data" / "agents.db"

    db_path.parent.mkdir(parents=True, exist_ok=True)

    # Create knowledge base if not provided
    if knowledge is None:
        knowledge = create_knowledge_base()

    return Agent(
        name="SME Research Agent",
        model=Ollama(id=model_id),
        tools=[browse_url],
        knowledge=knowledge,
        search_knowledge=True,  # Auto-search knowledge base for relevant context
        description=SYSTEM_PROMPT,
        instructions=INSTRUCTIONS,
        output_schema=CompanyResearchReport,  # Note: output_schema, not response_model
        db=SqliteDb(
            table_name="sme_research",
            db_file=str(db_path),
        ),
        markdown=True,
        add_datetime_to_instructions=True,
    )
```

### prompts.py

```python
"""System prompts and instructions for the research agent."""

SYSTEM_PROMPT = """You are a business research analyst for Growth Foundry, an AI consultancy
helping Singapore SMEs adopt AI solutions. Your job is to research prospective client companies
using their provided URLs and identify opportunities where AI could benefit their business.

You specialize in:
- Understanding Singapore's SME landscape
- Identifying practical AI adoption opportunities (proven solutions, not bleeding-edge)
- Translating technical possibilities into business value
- Finding personalization hooks for sales outreach"""

INSTRUCTIONS = [
    "You will be given company URLs (website, Instagram, Facebook). Browse each URL to gather information.",

    "For each URL, use the browse_url tool to fetch and read the content.",

    "EXTRACTION - Look for:",
    "- Company name and what they do",
    "- Products/services offered",
    "- Target customers (B2B vs B2C, industry)",
    "- Team size indicators (if mentioned)",
    "- Technology mentions (tools they use, job postings)",
    "- Recent news or announcements",
    "- Social media: posting frequency, content themes, engagement",

    "ANALYSIS - Based on extracted data:",
    "- Assess their digital maturity (are they tech-savvy or traditional?)",
    "- Identify 2-4 specific AI opportunities relevant to their business",
    "- Rank opportunities by potential impact and implementation complexity",
    "- Find personalization hooks for outreach (recent news, pain points, growth signals)",

    "REPORTING:",
    "- If a URL fails to load or has limited content, note it in research_notes",
    "- Be specific about opportunities (not generic 'AI can help with efficiency')",
    "- Always cite which URL provided each piece of information",
    "- Set data_quality to Low if most URLs failed or had sparse content",

    "SINGAPORE SME CONTEXT:",
    "- Most SMEs are service-oriented (F&B, retail, logistics, professional services)",
    "- Budget-conscious; prefer proven solutions over experiments",
    "- Often family-run; relationships matter",
    "- Government grants available (PSG, EDG) can offset AI adoption costs",
]
```

### app.py (Streamlit UI)

```python
"""Streamlit UI for SME Research Agent."""

import streamlit as st
from pathlib import Path
from src.agnoresearch.agent import create_research_agent
from src.agnoresearch.knowledge import create_knowledge_base, add_document_sync

st.set_page_config(page_title="SME Research Agent", page_icon="🔍", layout="wide")

st.title("🔍 SME Research Agent")
st.markdown("Research Singapore SME prospects for AI adoption opportunities")

# Knowledge base directory
KNOWLEDGE_DIR = Path("data/knowledge")
KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)

# Initialize knowledge base and agent (cached)
@st.cache_resource
def get_knowledge_and_agent():
    knowledge = create_knowledge_base()

    # Load existing knowledge files
    for file_path in KNOWLEDGE_DIR.glob("*"):
        if file_path.suffix.lower() in [".pdf", ".txt", ".md"]:
            try:
                add_document_sync(knowledge, file_path)
            except Exception:
                pass  # Skip files that fail to load

    agent = create_research_agent(knowledge=knowledge)
    return knowledge, agent

knowledge, agent = get_knowledge_and_agent()

# Sidebar: Knowledge Base Management
with st.sidebar:
    st.header("📚 Knowledge Base")
    st.markdown("Upload pitch decks, case studies, service offerings")

    uploaded_files = st.file_uploader(
        "Upload documents",
        type=["pdf", "txt", "md"],
        accept_multiple_files=True,
        help="Upload PDFs, text files, or markdown files"
    )

    if uploaded_files:
        for uploaded_file in uploaded_files:
            file_path = KNOWLEDGE_DIR / uploaded_file.name
            file_path.write_bytes(uploaded_file.getvalue())
            try:
                add_document_sync(knowledge, file_path)
                st.success(f"✅ Added: {uploaded_file.name}")
            except Exception as e:
                st.error(f"❌ Failed: {uploaded_file.name} - {e}")

    # Show existing files
    st.subheader("Loaded Documents")
    existing_files = list(KNOWLEDGE_DIR.glob("*"))
    if existing_files:
        for f in existing_files:
            if f.suffix.lower() in [".pdf", ".txt", ".md"]:
                st.write(f"📄 {f.name}")
    else:
        st.info("No documents uploaded yet")

# Main: Research Form
with st.form("research_form"):
    st.subheader("Enter Company URLs")

    website_url = st.text_input(
        "Website URL *",
        placeholder="https://company.com.sg",
        help="Required - company's main website"
    )
    instagram_url = st.text_input(
        "Instagram URL",
        placeholder="https://instagram.com/company",
        help="Optional - company's Instagram profile"
    )
    facebook_url = st.text_input(
        "Facebook URL",
        placeholder="https://facebook.com/company",
        help="Optional - company's Facebook page"
    )

    submitted = st.form_submit_button("🔍 Research", type="primary", use_container_width=True)

if submitted:
    if not website_url:
        st.error("Website URL is required")
    else:
        # Build research prompt
        urls_text = f"Website: {website_url}"
        if instagram_url:
            urls_text += f"\nInstagram: {instagram_url}"
        if facebook_url:
            urls_text += f"\nFacebook: {facebook_url}"

        prompt = f"""Research this company using the provided URLs.
Also search the knowledge base for relevant Growth Foundry services that could help them.

URLs:
{urls_text}"""

        # Show progress
        with st.status("🔍 Researching...", expanded=True) as status:
            st.write("Browsing company URLs...")
            st.write("Searching knowledge base for relevant services...")

            try:
                response = agent.run(prompt)
                status.update(label="✅ Research complete!", state="complete")

            except Exception as e:
                status.update(label="❌ Research failed", state="error")
                st.error(f"Error: {str(e)}")
                st.stop()

        # Display results
        st.divider()

        if response.content:
            if hasattr(response, 'structured_output') and response.structured_output:
                report = response.structured_output

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Company", report.company_name)
                with col2:
                    st.metric("Industry", report.industry)
                with col3:
                    st.metric("Data Quality", report.data_quality)

                st.subheader("📋 Overview")
                st.write(report.overview)

                if report.products_services:
                    st.subheader("🛍️ Products/Services")
                    for item in report.products_services:
                        st.write(f"- {item}")

                st.subheader("💡 AI Opportunities")
                for i, opp in enumerate(report.ai_opportunities, 1):
                    with st.expander(f"{i}. {opp.area}: {opp.opportunity} ({opp.complexity} complexity)"):
                        st.write(opp.rationale)

                if report.outreach_hooks:
                    st.subheader("🎯 Outreach Hooks")
                    for hook in report.outreach_hooks:
                        st.write(f"- {hook}")

                if report.research_notes:
                    st.subheader("📝 Research Notes")
                    st.info(report.research_notes)

                st.subheader("🔗 Sources")
                for source in report.sources:
                    st.write(f"- {source}")
            else:
                st.markdown(response.content)
```

---

## Dependencies

```toml
[project]
name = "agnoresearch"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "agno>=2.4.0",
    "ollama>=0.4.0",
    "crawl4ai>=0.4.0",
    "streamlit>=1.40.0",
    "pydantic>=2.0.0",
    "lancedb>=0.6.0",       # Local vector database
    "pypdf>=4.0.0",         # PDF parsing for knowledge base
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "ruff>=0.1.0",
]
```

**Required Ollama models:**
```bash
# Main model for research agent
ollama pull qwen2.5:14b

# Embedding model for knowledge base
ollama pull nomic-embed-text
```

---

## Success Metrics

| Metric | Target | How to Measure |
|--------|--------|----------------|
| Setup time | < 15 minutes | Time from clone to working agent |
| Research quality | 70%+ useful | Team rates reports as actionable |
| Research speed | < 3 minutes | Wall clock time per company |
| Reliability | 90%+ success | Agent completes without errors |
| URL success rate | 80%+ | URLs successfully scraped |

---

## Future: Writer Agent (v2)

When adding the Writer agent, use a **shared Pydantic model** as the contract:

```python
# Research Agent outputs CompanyResearchReport
# Writer Agent takes CompanyResearchReport as input

class OutreachDraft(BaseModel):
    """Output from Writer Agent."""

    subject_line: str = Field(max_length=60)
    email_body: str
    personalization_used: list[str] = Field(
        description="Which hooks from research were incorporated"
    )
    tone: str = Field(description="casual, professional, or consultative")


def create_writer_agent() -> Agent:
    return Agent(
        name="Outreach Writer",
        model=Ollama(id="qwen2.5:14b"),
        output_schema=OutreachDraft,
        instructions=[
            "You write personalized cold outreach emails for SMEs.",
            "Use the research data to personalize every message.",
            "Keep emails concise - under 150 words.",
            "Focus on one specific hook per email.",
        ],
    )

# Sequential handoff
report = research_agent.run(urls)
draft = writer_agent.run(f"Write outreach for: {report.structured_output.model_dump_json()}")
```

---

## References

- [Agno Documentation](https://docs.agno.com/)
- [Agno GitHub](https://github.com/agno-agi/agno) - v2.4.7 (Jan 2026)
- [Crawl4AI Documentation](https://docs.crawl4ai.com/)
- [Ollama](https://ollama.ai/) - Local LLM runtime
- [Streamlit Documentation](https://docs.streamlit.io/)

### Research Sources
- [Vercel agent-browser](https://github.com/vercel-labs/agent-browser) - CLI tool (not used, requires subprocess wrapper)
- [browser-use](https://pypi.org/project/browser-use/) - Alternative Python library
- [Instagram/Facebook scraping challenges](https://scrapfly.io/blog/posts/how-to-scrape-instagram) - Anti-bot considerations

---

## Open Questions (Resolved)

| Question | Decision |
|----------|----------|
| Which browser tool? | **Crawl4AI** - native Python, free, outputs markdown |
| Which UI? | **Streamlit** - supports 3-field form, built-in progress |
| Single vs multi-agent? | **Single agent v1**, designed for multi-agent v2 |
| Agno API for output? | `output_schema` (not `response_model`) |
| Social media blocking? | Graceful degradation, note in research_notes |
