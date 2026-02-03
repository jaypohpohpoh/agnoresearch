---
title: "feat: Agent Visibility, Citations & Social Media Authentication"
type: feat
date: 2026-02-03
---

# Agent Visibility, Citations & Social Media Authentication

## Overview

Enhance the SME Research Agent with real-time visibility into agent operations, mandatory source citations, and authenticated social media scraping for Instagram/Facebook.

## Problem Statement / Motivation

Current issues with the research agent:

1. **No visibility** - Users submit a request and wait without seeing what the agent is doing
2. **No citations** - Agent may hallucinate facts without citing sources
3. **Social media blocked** - Instagram blocks scrapers; Facebook requires login
4. **Incomplete research** - Agent doesn't gather thorough evidence

Users need to:
- See the agent working in real-time (builds trust, aids debugging)
- Verify all claims have sources (prevents hallucination)
- Access Instagram/Facebook data (major research sources)
- Get comprehensive research with evidence

## Proposed Solution

### 1. Real-time Agent Visibility (Streaming)

Show step-by-step agent work in the Streamlit UI:
- Tool calls as they happen (browsing URL X...)
- Knowledge base searches
- Thinking/reasoning process
- Progress through research phases

### 2. Mandatory Citations

Force the agent to cite sources for every claim:
- Update instructions to require citations
- Add citation fields to output schema
- Validate citations in UI
- Show sources inline with findings

### 3. Social Media Authentication

**Facebook:** Use DuckDuckGo with `site:facebook.com` modifier (no auth needed)

**Instagram:** Use Crawl4AI with authenticated session:
- Load credentials from environment variables
- Use browser storage state for session persistence
- Graceful fallback to public data if auth fails

### 4. Thorough Research with Evidence

- Add DuckDuckGo search tool for broader research
- Require evidence for each AI opportunity
- Minimum source count validation
- Research quality scoring

## Technical Approach

### Architecture Changes

```
┌─────────────────────────────────────────────────────────────────┐
│                      Streamlit UI                                │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │  📊 AGENT ACTIVITY PANEL (NEW)                          │   │
│   │  ┌─────────────────────────────────────────────────┐    │   │
│   │  │ ✅ Browsing website: https://company.com.sg     │    │   │
│   │  │ ⏳ Searching Facebook via DuckDuckGo...         │    │   │
│   │  │ ⏳ Browsing Instagram (authenticated)...        │    │   │
│   │  │    Found: 1,234 followers, posts about...       │    │   │
│   │  └─────────────────────────────────────────────────┘    │   │
│   └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │  📋 RESEARCH RESULTS (with inline citations)            │   │
│   │  Company: Bengawan Solo [source: website]               │   │
│   │  Industry: F&B Bakery [source: website, facebook]       │   │
│   │                                                          │   │
│   │  AI Opportunities:                                       │   │
│   │  1. Inventory AI [evidence: seasonal products mention    │   │
│   │     on website, high festive demand from FB posts]       │   │
│   └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### File Changes

| File | Change |
|------|--------|
| `src/agnoresearch/agent.py` | Add streaming, tool hooks, updated instructions |
| `src/agnoresearch/tools.py` | Add DDG search, Instagram auth, citation tracking |
| `src/agnoresearch/schemas.py` | Add citation fields to all findings |
| `src/agnoresearch/prompts.py` | Require citations, thorough research |
| `app.py` | Streaming UI, activity panel, citation display |
| `.env.example` | Add IG credentials template |

## Implementation Plan

### Phase 1: Agent Streaming & Visibility

- [x] **1.1** Add async streaming to agent runner
  - Use `agent.arun(stream=True, stream_events=True)`
  - Capture `RunEvent.tool_call_started`, `RunEvent.tool_call_completed`

- [x] **1.2** Create activity panel in Streamlit
  - Real-time updates using `st.empty()` containers
  - Show tool name, arguments, and results
  - Progress indicator per URL

- [x] **1.3** Add tool hooks for logging
  ```python
  def activity_hook(function_name: str, function_call: Callable, arguments: Dict):
      st.session_state.activities.append({
          'tool': function_name,
          'args': arguments,
          'status': 'running'
      })
      result = function_call(**arguments)
      st.session_state.activities[-1]['status'] = 'complete'
      return result
  ```

### Phase 2: Citation System

- [x] **2.1** Update schemas with citation fields
  ```python
  class CitedFinding(BaseModel):
      claim: str
      source_url: str
      source_type: str  # website, facebook, instagram, knowledge_base
      excerpt: str  # Supporting quote from source

  class AIOpportunity(BaseModel):
      area: str
      opportunity: str
      rationale: str
      complexity: str
      evidence: list[CitedFinding]  # NEW: Must have evidence
  ```

- [x] **2.2** Update prompts to require citations
  ```python
  INSTRUCTIONS = [
      ...
      "CITATION REQUIREMENTS:",
      "- Every factual claim MUST cite its source URL",
      "- Include a brief excerpt or quote as evidence",
      "- If you cannot cite a source, do not include the claim",
      "- Minimum 2 sources per AI opportunity",
  ]
  ```

- [x] **2.3** Add citation validation in UI
  - Warning if opportunities lack evidence
  - Highlight claims without sources
  - Show source excerpts on hover/expand

### Phase 3: Facebook via DuckDuckGo

- [x] **3.1** Add DuckDuckGo tool with site modifier
  ```python
  from agno.tools.duckduckgo import DuckDuckGoTools

  # For Facebook-specific searches
  facebook_search = DuckDuckGoTools(modifier="site:facebook.com")
  ```

- [x] **3.2** Create wrapper tool for Facebook research
  ```python
  @tool
  def search_facebook(company_name: str) -> str:
      """Search Facebook for company information via DuckDuckGo."""
      ddg = DuckDuckGoTools(modifier="site:facebook.com")
      results = ddg.search(f"{company_name} Singapore")
      return format_facebook_results(results)
  ```

- [x] **3.3** Update agent to use Facebook search
  - Add to tools list
  - Update instructions to use for Facebook URLs

### Phase 4: Instagram Authentication

- [x] **4.1** Add environment variables for credentials
  ```bash
  # .env
  INSTAGRAM_USERNAME=your_dummy_account
  INSTAGRAM_PASSWORD=your_password
  ```

- [x] **4.2** Create authenticated Instagram browser
  ```python
  async def browse_instagram_authenticated(url: str) -> str:
      """Browse Instagram with authentication."""
      from crawl4ai import AsyncWebCrawler, BrowserConfig

      config = BrowserConfig(
          headless=True,
          storage_state="data/instagram_session.json",  # Persist session
      )

      async with AsyncWebCrawler(config=config) as crawler:
          # Login if no session
          if not Path("data/instagram_session.json").exists():
              await _instagram_login(crawler)

          result = await crawler.arun(url=url)
          return extract_instagram_data(result)
  ```

- [x] **4.3** Implement login flow
  ```python
  async def _instagram_login(crawler):
      """Perform Instagram login and save session."""
      await crawler.arun("https://instagram.com/accounts/login/")
      await crawler.fill("input[name='username']", os.getenv("INSTAGRAM_USERNAME"))
      await crawler.fill("input[name='password']", os.getenv("INSTAGRAM_PASSWORD"))
      await crawler.click("button[type='submit']")
      await crawler.wait_for_navigation()
      await crawler.save_storage_state("data/instagram_session.json")
  ```

- [x] **4.4** Fallback to public data
  - If auth fails, return limited public info
  - Log warning but don't fail research

### Phase 5: Thorough Research Requirements

- [x] **5.1** Add research thoroughness instructions
  ```python
  INSTRUCTIONS = [
      ...
      "RESEARCH THOROUGHNESS:",
      "- Browse ALL provided URLs before concluding",
      "- Search knowledge base for relevant services",
      "- Use DuckDuckGo to find additional context",
      "- Gather minimum 3 pieces of evidence per finding",
      "- Note data quality and gaps in research_notes",
  ]
  ```

- [x] **5.2** Add validation for minimum sources
  - Check `sources` list has entries
  - Validate each AI opportunity has evidence
  - Show data quality score based on source count

- [x] **5.3** Add research quality metrics
  ```python
  class ResearchQuality(BaseModel):
      sources_found: int
      urls_successfully_scraped: int
      urls_failed: int
      evidence_pieces: int
      quality_score: str  # High/Medium/Low based on metrics
  ```

## Acceptance Criteria

### Agent Visibility
- [ ] User sees real-time activity as agent works
- [ ] Each tool call shows: tool name, URL/query, status
- [ ] Activity panel updates without page refresh
- [ ] Errors are shown immediately in activity panel

### Citations
- [ ] Every claim in report has a source citation
- [ ] AI opportunities have minimum 2 evidence pieces
- [ ] Sources are clickable links
- [ ] Claims without sources are flagged/removed

### Facebook Access
- [ ] Facebook company pages accessible via DDG search
- [ ] Results include page name, description, posts
- [ ] No login required
- [ ] Works for Singapore company pages

### Instagram Authentication
- [ ] Instagram profiles accessible with dummy account
- [ ] Session persists across runs (no repeated logins)
- [ ] Extracts: followers, post count, recent posts, bio
- [ ] Graceful fallback if auth fails

### Research Thoroughness
- [ ] Agent browses ALL provided URLs
- [ ] Knowledge base is searched
- [ ] Minimum source count enforced
- [ ] Research quality score displayed

## Code Examples

### Streaming Agent Runner (app.py)

```python
import asyncio
import streamlit as st
from agno.agent import RunEvent

async def run_research_with_streaming(agent, prompt):
    """Run agent with real-time activity updates."""
    activities = st.session_state.get('activities', [])
    activity_container = st.empty()

    async for event in agent.arun(prompt, stream=True, stream_events=True):
        if event.event == RunEvent.tool_call_started:
            activities.append({
                'tool': event.tool.tool_name,
                'args': event.tool.tool_args,
                'status': '⏳ Running...'
            })
            _render_activities(activity_container, activities)

        elif event.event == RunEvent.tool_call_completed:
            activities[-1]['status'] = '✅ Complete'
            activities[-1]['result_preview'] = str(event.tool.result)[:100]
            _render_activities(activity_container, activities)

        elif event.event == RunEvent.run_content:
            yield event.content

    return activities

def _render_activities(container, activities):
    with container:
        st.markdown("### 🔄 Agent Activity")
        for act in activities:
            st.markdown(f"{act['status']} **{act['tool']}** - `{act['args']}`")
```

### Citation-Required Schema (schemas.py)

```python
class CitedEvidence(BaseModel):
    """Evidence with mandatory source citation."""
    claim: str = Field(..., description="The factual claim")
    source_url: str = Field(..., description="URL where this was found")
    excerpt: str = Field(..., description="Quote or excerpt from source")

class AIOpportunity(BaseModel):
    """AI opportunity with required evidence."""
    area: str
    opportunity: str
    rationale: str
    complexity: str
    evidence: list[CitedEvidence] = Field(
        ...,
        min_length=1,
        description="Must have at least one piece of evidence"
    )
```

### Facebook Search Tool (tools.py)

```python
from agno.tools.duckduckgo import DuckDuckGoTools

@tool
def search_facebook_page(company_name: str, location: str = "Singapore") -> str:
    """
    Search for a company's Facebook presence via DuckDuckGo.

    Args:
        company_name: Name of the company to search
        location: Location to narrow search (default: Singapore)

    Returns:
        Facebook page information and recent activity
    """
    ddg = DuckDuckGoTools(modifier="site:facebook.com")
    query = f"{company_name} {location}"

    # Get search results
    results = ddg.duckduckgo_search(query, max_results=5)

    if not results:
        return f"No Facebook results found for {company_name}"

    # Format results with citations
    output = f"# Facebook Search Results for {company_name}\n\n"
    for r in results:
        output += f"## {r.get('title', 'Untitled')}\n"
        output += f"URL: {r.get('href', 'N/A')}\n"
        output += f"Snippet: {r.get('body', 'No description')}\n\n"

    return output
```

## Dependencies

Add to `pyproject.toml`:
```toml
dependencies = [
    ...
    "duckduckgo-search>=6.0.0",  # For DDG tools
    "python-dotenv>=1.0.0",      # For env vars
]
```

## Environment Variables

Add to `.env.example`:
```bash
# Instagram credentials (dummy account for scraping)
INSTAGRAM_USERNAME=your_dummy_account
INSTAGRAM_PASSWORD=your_secure_password
```

## Success Metrics

| Metric | Target |
|--------|--------|
| Activity visibility | 100% of tool calls shown |
| Citation coverage | 100% claims have sources |
| Facebook success rate | 90%+ pages accessible |
| Instagram success rate | 80%+ profiles (with auth) |
| Research quality | Avg 5+ sources per report |

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Instagram blocks auth | Session persistence, rate limiting, proxy rotation |
| DDG rate limits | Cache results, respect rate limits |
| Streaming complexity | Fallback to non-streaming mode |
| Performance impact | Async operations, progress indication |

## References

### Agno Documentation
- [Streaming Agent Responses](https://docs.agno.com/basics/agents/running-agents) - `stream=True, stream_events=True`
- [Tool Hooks](https://docs.agno.com/basics/tools/hooks) - Monitor tool calls
- [DuckDuckGo Tools](https://docs.agno.com/integrations/toolkits/search/duckduckgo) - `modifier="site:facebook.com"`
- [Agent Events](https://docs.agno.com/examples/basics/agent/events) - `RunEvent.tool_call_started`

### Internal Files
- `src/agnoresearch/agent.py:42` - Current agent configuration
- `src/agnoresearch/tools.py:7` - Current browse_url tool
- `app.py:112` - Current status display

## Open Questions

1. **Rate limiting** - How aggressive can we be with Instagram before getting blocked?
2. **Session persistence** - How long do Instagram sessions last?
3. **Proxy support** - Should we add proxy rotation for blocked IPs?
