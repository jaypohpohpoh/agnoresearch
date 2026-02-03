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
from .tools import scrape_website, scrape_social, search_facebook_structured, search_google_reviews
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
    location: Optional[str] = None,
) -> list[ScrapedContent]:
    """
    Stage 1: Data Collection (Python functions, no LLM).

    Fetches raw content from URLs with retry logic.
    Now includes review search for personalization data.
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

    # Search for reviews if we have company name (gold for personalization)
    if company_name:
        review_result = search_google_reviews(company_name, location or "")
        results.append(review_result)

    return results


def stage_extract(scrape_results: list[ScrapedContent], model_id: str = "gpt-oss:20b") -> Optional[CompanyFacts]:
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


def stage_analyze(facts: CompanyFacts, model_id: str = "gpt-oss:20b") -> Optional[Opportunities]:
    """
    Stage 3: Analysis (LLM task).

    Suggests AI opportunities AND generates conversation starters for outreach.
    """
    prompt = f"""Based on these extracted company facts, suggest 2-4 AI opportunities
AND generate 2-3 conversation starters for outreach:

Company: {facts.company_name}
Industry: {facts.industry}
What they do: {facts.what_they_do}
Products/Services: {', '.join(facts.products)}
Source: {facts.source_url}

For AI opportunities:
- Reference specific data from the facts in your 'why' field
- Focus on proven AI solutions (chatbots, automation, forecasting)
- Prefer Low/Medium complexity

For conversation_starters (IMPORTANT for outreach personalization):
- Generate 2-3 hooks based on the research
- Each needs: topic, hook_text (a genuine question), data_point (supporting fact)
- These will be used to write personalized outreach messages

Set recommended_hook to the best type: 'rating_praise', 'growth_signal', 'industry_question', or 'specific_service'
"""

    agent = create_analyzer_agent(model_id=model_id)
    response = agent.run(prompt)

    if response and response.content:
        return response.content

    return None


def stage_outreach(
    facts: CompanyFacts,
    opps: Opportunities,
    review_content: Optional[str] = None,
    model_id: Optional[str] = None,
) -> Optional[OutreachDrafts]:
    """
    Stage 5: Outreach Writing (LLM task).

    Generates personalized WhatsApp and email drafts based on research.
    Uses conversation_starters from analysis for better hooks.
    """
    # Format conversation starters if available
    starters_text = ""
    if opps.conversation_starters:
        starters_text = "\n## Conversation Starters (use these as hooks)\n"
        for starter in opps.conversation_starters:
            starters_text += f"- [{starter.topic}] {starter.hook_text}\n"
            starters_text += f"  Data point: {starter.data_point}\n"

    # Get recommended hook type
    hook_type = opps.recommended_hook or "industry_question"

    # Format review info if available
    review_text = ""
    if review_content:
        review_text = f"\n## Review Data\n{review_content[:500]}\n"

    prompt = f"""Write FIRST-CONTACT outreach messages for this company.

## Company Research
Company: {facts.company_name}
Industry: {facts.industry}
What they do: {facts.what_they_do}
Products/Services: {', '.join(facts.products)}
{review_text}
{starters_text}

## Recommended Hook Type: {hook_type}

## Task
Write personalized outreach that starts a conversation (NOT a pitch):

1. WhatsApp (80-120 words): Observation → Question → Soft-connect
2. Email (150-200 words with subject): Observation → Insight → Question → Soft-connect

Use specific details from the research above. The recipient should NOT know what you're selling.
Sign off with "— JP"
"""

    # Use default model if not specified (Sonnet for outreach)
    agent = create_outreach_agent(model_id=model_id) if model_id else create_outreach_agent()
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
    company_name: Optional[str] = None,
    location: Optional[str] = None,
    model_id: Optional[str] = None,
) -> CompanyResearchReport:
    """
    Run the full research pipeline.

    Args:
        website_url: Company website URL (required)
        instagram_url: Instagram profile URL (optional)
        facebook_url: Facebook page URL (optional)
        company_name: Company name (optional, extracted from website if not provided)
        location: Location for review search (optional)
        model_id: Model to use for LLM stages (default: gpt-oss:20b)

    Returns:
        CompanyResearchReport with research results

    Pipeline stages:
        1. Scrape: Fetch content from URLs + reviews
        2. Extract: Pull facts from content (LLM)
        3. Analyze: Suggest AI opportunities + conversation hooks (LLM)
        4. Outreach: Write personalized drafts (LLM)
        5. Assemble: Build final report (Python)
    """
    # Stage 1: Scrape (includes review search if company_name provided)
    scrape_results = stage_scrape(
        website_url=website_url,
        instagram_url=instagram_url,
        facebook_url=facebook_url,
        company_name=company_name,
        location=location,
    )

    # Validation checkpoint 1
    if not validate_scrape(scrape_results):
        return assemble_report(facts=None, opps=None, scrape_results=scrape_results)

    # Stage 2: Extract
    extract_model = model_id or "gpt-oss:20b"
    facts = stage_extract(scrape_results, model_id=extract_model)

    # Validation checkpoint 2
    if not facts or not validate_facts(facts):
        return assemble_report(facts=facts, opps=None, scrape_results=scrape_results)

    # Now we have company name - search for additional data if not already done
    fb_results = [r for r in scrape_results if "facebook" in r.url.lower()]
    if not any(r.success for r in fb_results):
        fb_search = search_facebook_structured(facts.company_name)
        scrape_results.append(fb_search)

    # Search for reviews if we didn't have company name earlier
    review_results = [r for r in scrape_results if "reviews" in r.url.lower()]
    if not review_results:
        review_search = search_google_reviews(facts.company_name, location or "")
        scrape_results.append(review_search)

    # Stage 3: Analyze (generates conversation_starters and recommended_hook)
    opps = stage_analyze(facts, model_id=extract_model)

    # Validation checkpoint 3 (soft - we can still return partial report)
    if not opps or not validate_opportunities(opps):
        opps = None

    # Stage 4: Outreach (only if we have facts and opportunities)
    # Uses Sonnet by default for better writing quality
    outreach_drafts = None
    if facts and opps:
        # Get review content for personalization
        review_content = None
        for r in scrape_results:
            if "reviews" in r.url.lower() and r.success:
                review_content = r.content
                break

        outreach_drafts = stage_outreach(facts, opps, review_content=review_content)

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
    import argparse
    import warnings

    # Suppress unclosed socket warnings from Ollama client (harmless on exit)
    warnings.filterwarnings("ignore", category=ResourceWarning, message="unclosed.*socket")

    parser = argparse.ArgumentParser(description="SME Research Pipeline")
    parser.add_argument("website_url", help="Company website URL")
    parser.add_argument("--instagram", help="Instagram profile URL")
    parser.add_argument("--facebook", help="Facebook page URL")
    parser.add_argument("--company", help="Company name (for review search)")
    parser.add_argument("--location", help="Location (for review search)")
    parser.add_argument("--model", default=None, help="Model ID (default: Claude Haiku)")

    args = parser.parse_args()

    print(f"Running pipeline for: {args.website_url}")
    print("=" * 60)

    report = run_pipeline(
        website_url=args.website_url,
        instagram_url=args.instagram,
        facebook_url=args.facebook,
        company_name=args.company,
        location=args.location,
        model_id=args.model,
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

    # Outreach Drafts
    if report.outreach_drafts:
        print("\n" + "=" * 60)
        print("OUTREACH DRAFTS:")
        print("=" * 60)
        print("\nWhatsApp:")
        for i, draft in enumerate(report.outreach_drafts.whatsapp_drafts, 1):
            print(f"\n--- Draft {i} ---")
            print(draft.body)
            print(f"(Personalized: {draft.personalization_used})")

        print("\nEmail:")
        for i, draft in enumerate(report.outreach_drafts.email_drafts, 1):
            print(f"\n--- Draft {i} ---")
            if draft.subject:
                print(f"Subject: {draft.subject}")
            print(draft.body)
            print(f"(Personalized: {draft.personalization_used})")
