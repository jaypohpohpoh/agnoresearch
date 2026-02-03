"""Research pipeline: orchestrates stages, validates outputs, assembles reports.

Pipeline Flow:
    URLs -> [Scraper] -> [Extractor] -> [Analyzer] -> [OutreachWriter] -> [Assembler] -> Report
                 |            |             |               |
            Validate     Validate      Validate         (optional)
"""

from typing import Optional

from .schemas import (
    ScrapedContent,
    CompanyFacts,
    Opportunities,
    Opportunity,
    CompanyResearchReport,
    AIOpportunity,
    ResearchQuality,
    OutreachDrafts,
)
from .tools import scrape_website, scrape_social, search_facebook_structured
from .agents import create_extractor_agent, create_analyzer_agent, create_outreach_agent


# =============================================================================
# Validation Functions
# =============================================================================


def validate_scrape(results: list[ScrapedContent]) -> bool:
    """At least one URL must succeed."""
    return any(r.success for r in results)


def validate_facts(facts: CompanyFacts) -> bool:
    """Must have company name and at least 1 product."""
    return bool(facts.company_name) and len(facts.products) >= 1


def validate_opportunities(opps: Opportunities) -> bool:
    """Must have at least 1 opportunity."""
    return len(opps.items) >= 1


# =============================================================================
# Stage Functions
# =============================================================================


def stage_scrape(
    website_url: str,
    instagram_url: Optional[str] = None,
    facebook_url: Optional[str] = None,
    company_name: Optional[str] = None,
) -> list[ScrapedContent]:
    """
    Stage 1: Data Collection (Python functions, no LLM).

    Fetches raw content from URLs with retry logic.
    """
    results = []

    # Always scrape website
    website_result = scrape_website(website_url)
    results.append(website_result)

    # Scrape Instagram if provided
    if instagram_url:
        instagram_result = scrape_social(instagram_url)
        results.append(instagram_result)

    # Handle Facebook - use search if direct URL fails or use company name
    if facebook_url:
        facebook_result = scrape_social(facebook_url)
        results.append(facebook_result)

        # If Facebook scrape failed and we have company name, try search
        if not facebook_result.success and company_name:
            search_result = search_facebook_structured(company_name)
            results.append(search_result)
    elif company_name:
        # No Facebook URL but have company name - search for them
        search_result = search_facebook_structured(company_name)
        results.append(search_result)

    return results


def stage_extract(scrape_results: list[ScrapedContent], model_id: str = "qwen2.5:14b") -> Optional[CompanyFacts]:
    """
    Stage 2: Extraction (Simple LLM task).

    Extracts facts from content - NO analysis.
    """
    # Get successful website content
    successful_content = [r for r in scrape_results if r.success and r.content]

    if not successful_content:
        return None

    # Use the first successful result (prioritize website)
    primary_content = successful_content[0]

    # Build extraction prompt
    prompt = f"""Extract company facts from this content:

{primary_content.content}

Source URL: {primary_content.url}
"""

    agent = create_extractor_agent(model_id=model_id)
    response = agent.run(prompt)

    if response and response.content:
        return response.content

    return None


def stage_analyze(facts: CompanyFacts, model_id: str = "qwen2.5:14b") -> Optional[Opportunities]:
    """
    Stage 3: Analysis (Simple LLM task).

    Suggests AI opportunities based on extracted facts.
    """
    prompt = f"""Based on these extracted company facts, suggest 2-4 AI opportunities:

Company: {facts.company_name}
Industry: {facts.industry}
What they do: {facts.what_they_do}
Products/Services: {', '.join(facts.products)}
Source: {facts.source_url}

Remember:
- Reference specific data from the facts in your 'why' field
- Focus on proven AI solutions (chatbots, automation, forecasting)
- Prefer Low/Medium complexity for budget-conscious SMEs
"""

    agent = create_analyzer_agent(model_id=model_id)
    response = agent.run(prompt)

    if response and response.content:
        return response.content

    return None


def stage_outreach(
    facts: CompanyFacts,
    opps: Opportunities,
    model_id: str = "qwen2.5:14b",
) -> Optional[OutreachDrafts]:
    """
    Stage 5: Outreach Writing (LLM task).

    Generates personalized WhatsApp and email drafts based on research.
    """
    # Get the best opportunity to highlight
    best_opp = opps.items[0] if opps.items else None

    prompt = f"""Write outreach messages for this company:

Company: {facts.company_name}
Industry: {facts.industry}
What they do: {facts.what_they_do}
Products/Services: {', '.join(facts.products)}

Best AI Opportunity: {best_opp.area} - {best_opp.idea if best_opp else 'General AI consultation'}
Why it fits: {best_opp.why if best_opp else 'Could benefit from AI adoption'}

Write personalized outreach:
1. 1-2 WhatsApp messages (short, friendly, 50-100 words each)
2. 1-2 Email drafts (professional but warm, 100-200 words with subject line)

Make them personal by referencing their specific business details.
Sign off from Growth Foundry with a soft CTA (happy to chat, book a call).
"""

    agent = create_outreach_agent(model_id=model_id)
    response = agent.run(prompt)

    if response and response.content:
        return response.content

    return None


def assemble_report(
    facts: Optional[CompanyFacts],
    opps: Optional[Opportunities],
    scrape_results: list[ScrapedContent],
    outreach_drafts: Optional[OutreachDrafts] = None,
) -> CompanyResearchReport:
    """
    Stage 4: Assembler (Python function, no LLM).

    Combines outputs into final CompanyResearchReport.
    Computes metrics PROGRAMMATICALLY (not self-reported).
    """
    # Compute REAL metrics
    successful_scrapes = [s for s in scrape_results if s.success]
    failed_scrapes = [s for s in scrape_results if not s.success]

    # Build research notes
    notes = []
    for s in failed_scrapes:
        notes.append(f"Failed to scrape {s.url}: {s.error}")

    research_notes = "\n".join(notes) if notes else None

    # Handle case where extraction failed
    if not facts:
        return CompanyResearchReport(
            company_name="Unknown",
            industry="Unknown",
            overview="Could not extract company information from provided URLs.",
            products_services=[],
            digital_maturity="Unknown",
            ai_opportunities=[],
            sources=[s.url for s in successful_scrapes],
            research_quality=ResearchQuality(
                sources_found=len(scrape_results),
                urls_successfully_scraped=len(successful_scrapes),
                urls_failed=len(failed_scrapes),
                evidence_pieces=0,
                quality_score="Low",
            ),
            data_quality="Low",
            research_notes=research_notes or "Extraction failed - no content could be processed.",
        )

    # Convert opportunities to AIOpportunity format
    ai_opportunities = []
    if opps:
        for opp in opps.items:
            ai_opportunities.append(
                AIOpportunity(
                    area=opp.area,
                    opportunity=opp.idea,
                    rationale=opp.why,
                    complexity=opp.complexity,
                    evidence=[],  # Evidence is embedded in rationale via 'why' field
                )
            )

    # Compute quality score
    if len(successful_scrapes) >= 3:
        quality_score = "High"
    elif len(successful_scrapes) >= 2:
        quality_score = "Medium"
    else:
        quality_score = "Low"

    return CompanyResearchReport(
        company_name=facts.company_name,
        industry=facts.industry,
        overview=facts.what_they_do,
        products_services=facts.products,
        digital_maturity="Medium",  # Conservative default
        ai_opportunities=ai_opportunities,
        outreach_drafts=outreach_drafts,
        outreach_hooks=[],  # Legacy field
        sources=[s.url for s in successful_scrapes],
        research_quality=ResearchQuality(
            sources_found=len(scrape_results),
            urls_successfully_scraped=len(successful_scrapes),
            urls_failed=len(failed_scrapes),
            evidence_pieces=len(ai_opportunities),
            quality_score=quality_score,
        ),
        data_quality=quality_score,
        research_notes=research_notes,
    )


# =============================================================================
# Main Pipeline
# =============================================================================


def run_pipeline(
    website_url: str,
    instagram_url: Optional[str] = None,
    facebook_url: Optional[str] = None,
    model_id: str = "qwen2.5:14b",
) -> CompanyResearchReport:
    """
    Run the full research pipeline.

    Args:
        website_url: Company website URL (required)
        instagram_url: Instagram profile URL (optional)
        facebook_url: Facebook page URL (optional)
        model_id: Ollama model to use for LLM stages

    Returns:
        CompanyResearchReport with research results

    Pipeline stages:
        1. Scrape: Fetch content from URLs
        2. Extract: Pull facts from content (LLM)
        3. Analyze: Suggest AI opportunities (LLM)
        4. Outreach: Write personalized drafts (LLM)
        5. Assemble: Build final report (Python)
    """
    # Stage 1: Scrape
    scrape_results = stage_scrape(
        website_url=website_url,
        instagram_url=instagram_url,
        facebook_url=facebook_url,
    )

    # Validation checkpoint 1
    if not validate_scrape(scrape_results):
        return assemble_report(facts=None, opps=None, scrape_results=scrape_results)

    # Stage 2: Extract
    facts = stage_extract(scrape_results, model_id=model_id)

    # Validation checkpoint 2
    if not facts or not validate_facts(facts):
        return assemble_report(facts=facts, opps=None, scrape_results=scrape_results)

    # Now we have company name - try Facebook search if we don't have Facebook content
    fb_results = [r for r in scrape_results if "facebook" in r.url.lower()]
    if not any(r.success for r in fb_results):
        # Search for Facebook presence using extracted company name
        fb_search = search_facebook_structured(facts.company_name)
        scrape_results.append(fb_search)

    # Stage 3: Analyze
    opps = stage_analyze(facts, model_id=model_id)

    # Validation checkpoint 3 (soft - we can still return partial report)
    if not opps or not validate_opportunities(opps):
        opps = None

    # Stage 4: Outreach (only if we have facts and opportunities)
    outreach_drafts = None
    if facts and opps:
        outreach_drafts = stage_outreach(facts, opps, model_id=model_id)

    # Stage 5: Assemble
    return assemble_report(
        facts=facts,
        opps=opps,
        scrape_results=scrape_results,
        outreach_drafts=outreach_drafts,
    )


# =============================================================================
# CLI for testing
# =============================================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m src.agnoresearch.pipeline <website_url> [instagram_url] [facebook_url]")
        sys.exit(1)

    website = sys.argv[1]
    instagram = sys.argv[2] if len(sys.argv) > 2 else None
    facebook = sys.argv[3] if len(sys.argv) > 3 else None

    print(f"Running pipeline for: {website}")
    print("=" * 60)

    report = run_pipeline(
        website_url=website,
        instagram_url=instagram,
        facebook_url=facebook,
    )

    print("\nRESULT:")
    print("=" * 60)
    print(f"Company: {report.company_name}")
    print(f"Industry: {report.industry}")
    print(f"Overview: {report.overview}")
    print(f"Products: {report.products_services}")
    print(f"AI Opportunities: {len(report.ai_opportunities)}")
    for i, opp in enumerate(report.ai_opportunities, 1):
        print(f"  {i}. {opp.area}: {opp.opportunity} ({opp.complexity})")
    print(f"Quality: {report.data_quality}")
    print(f"Sources: {report.sources}")
    if report.research_notes:
        print(f"Notes: {report.research_notes}")
