"""Simple, focused agents for the research pipeline."""

from agno.agent import Agent
from agno.models.ollama import Ollama

from .schemas import CompanyFacts, Opportunities, OutreachDrafts
from .prompts import (
    EXTRACTOR_SYSTEM_PROMPT,
    EXTRACTOR_INSTRUCTIONS,
    ANALYZER_SYSTEM_PROMPT,
    ANALYZER_INSTRUCTIONS,
    OUTREACH_SYSTEM_PROMPT,
    OUTREACH_INSTRUCTIONS,
)


def create_extractor_agent(model_id: str = "qwen2.5:14b") -> Agent:
    """
    Create the CompanyExtractor agent.

    Purpose: Extract facts from content - NO analysis.
    Input: Website markdown content
    Output: CompanyFacts (5 fields)
    """
    return Agent(
        name="Company Extractor",
        model=Ollama(id=model_id),
        description=EXTRACTOR_SYSTEM_PROMPT,
        instructions=EXTRACTOR_INSTRUCTIONS,
        output_schema=CompanyFacts,
        markdown=True,
    )


def create_analyzer_agent(model_id: str = "qwen2.5:14b") -> Agent:
    """
    Create the OpportunityAnalyzer agent.

    Purpose: Suggest AI opportunities based on extracted facts.
    Input: CompanyFacts
    Output: Opportunities (list of 2-4)
    """
    return Agent(
        name="Opportunity Analyzer",
        model=Ollama(id=model_id),
        description=ANALYZER_SYSTEM_PROMPT,
        instructions=ANALYZER_INSTRUCTIONS,
        output_schema=Opportunities,
        markdown=True,
    )


def create_outreach_agent(model_id: str = "qwen2.5:14b") -> Agent:
    """
    Create the OutreachWriter agent.

    Purpose: Write personalized outreach messages based on research.
    Input: CompanyFacts + Opportunities
    Output: OutreachDrafts (WhatsApp + Email)
    """
    return Agent(
        name="Outreach Writer",
        model=Ollama(id=model_id),
        description=OUTREACH_SYSTEM_PROMPT,
        instructions=OUTREACH_INSTRUCTIONS,
        output_schema=OutreachDrafts,
        markdown=True,
    )


# =============================================================================
# Test functions for development
# =============================================================================


def test_extractor():
    """Test the extractor agent with sample content."""
    sample_content = """
    # Content from https://example.com.sg

    ## About Us
    Example Singapore Pte Ltd is a leading provider of logistics solutions in Singapore.
    We specialize in last-mile delivery for e-commerce businesses.

    ## Our Services
    - Same-day delivery
    - Warehouse fulfillment
    - Cross-border shipping to Malaysia and Indonesia
    - Real-time tracking

    ## Contact
    123 Logistics Road, Singapore 123456
    """

    agent = create_extractor_agent()
    response = agent.run(f"Extract company facts from this content:\n\n{sample_content}")

    print("Extractor Test Result:")
    print(response.content)
    return response.content


def test_analyzer():
    """Test the analyzer agent with sample facts."""
    from .schemas import CompanyFacts

    sample_facts = CompanyFacts(
        company_name="Example Singapore Pte Ltd",
        industry="Logistics",
        what_they_do="Provides last-mile delivery and warehouse fulfillment for e-commerce businesses in Singapore.",
        products=["Same-day delivery", "Warehouse fulfillment", "Cross-border shipping", "Real-time tracking"],
        source_url="https://example.com.sg",
    )

    agent = create_analyzer_agent()
    prompt = f"""Based on these extracted company facts, suggest 2-4 AI opportunities:

Company: {sample_facts.company_name}
Industry: {sample_facts.industry}
What they do: {sample_facts.what_they_do}
Products/Services: {', '.join(sample_facts.products)}
"""

    response = agent.run(prompt)

    print("Analyzer Test Result:")
    print(response.content)
    return response.content


if __name__ == "__main__":
    print("=" * 60)
    print("Testing Extractor Agent")
    print("=" * 60)
    test_extractor()

    print("\n" + "=" * 60)
    print("Testing Analyzer Agent")
    print("=" * 60)
    test_analyzer()
