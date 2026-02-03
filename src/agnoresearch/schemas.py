"""Pydantic schemas for research agent input/output."""

from pydantic import BaseModel, Field, HttpUrl
from typing import Literal, Optional, ForwardRef


# =============================================================================
# Stage 1: Scraping Output (Python functions, no LLM)
# =============================================================================


class ScrapedContent(BaseModel):
    """Output from scraping a URL."""

    url: str = Field(..., description="The URL that was scraped")
    success: bool = Field(..., description="Whether scraping succeeded")
    content: str = Field(default="", description="Markdown content, max 8K chars")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    content_length: int = Field(default=0, description="Length of content in characters")


# =============================================================================
# Stage 2: Extraction Output (Simple LLM task)
# =============================================================================


class CompanyFacts(BaseModel):
    """Extracted facts from company content - NO analysis."""

    company_name: str = Field(..., description="Company name as found on website")
    industry: str = Field(..., description="Primary industry/sector")
    what_they_do: str = Field(..., description="1-2 sentences describing what they do")
    products: list[str] = Field(default_factory=list, max_length=5, description="Up to 5 products/services")
    source_url: str = Field(..., description="URL this was extracted from")


# =============================================================================
# Stage 3: Analysis Output (Simple LLM task)
# =============================================================================


class Opportunity(BaseModel):
    """A single AI opportunity suggestion."""

    area: str = Field(..., description="Business area (e.g., 'Customer Service')")
    idea: str = Field(..., description="Specific AI application (e.g., 'AI chatbot for FAQs')")
    why: str = Field(..., description="Reference to extracted data supporting this")
    complexity: Literal["Low", "Medium", "High"] = Field(..., description="Implementation complexity")


class Opportunities(BaseModel):
    """List of AI opportunities from analysis."""

    items: list[Opportunity] = Field(..., min_length=1, max_length=4, description="2-4 AI opportunities")


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


class CitedEvidence(BaseModel):
    """Evidence with mandatory source citation."""

    claim: str = Field(..., description="The factual claim or observation")
    source_url: str = Field(..., description="URL where this information was found")
    source_type: str = Field(
        ...,
        description="Type of source: website, facebook, instagram, knowledge_base"
    )
    excerpt: str = Field(
        default="",
        description="Direct quote or excerpt from the source supporting this claim"
    )


class AIOpportunity(BaseModel):
    """A specific AI adoption opportunity for the SME."""

    area: str = Field(..., description="Business area (e.g., 'Customer Service', 'Operations')")
    opportunity: str = Field(..., description="Specific AI application")
    rationale: str = Field(..., description="Why this fits their business based on research")
    complexity: str = Field(..., description="Low/Medium/High implementation complexity")
    evidence: list[CitedEvidence] = Field(
        default_factory=list,
        description="Evidence supporting this opportunity - must have at least one piece"
    )


class SocialMediaInsight(BaseModel):
    """Insights extracted from social media presence."""

    platform: str = Field(..., description="instagram or facebook")
    followers: Optional[str] = Field(None, description="Follower count if visible")
    posting_frequency: Optional[str] = Field(None, description="How often they post")
    content_themes: list[str] = Field(default_factory=list, description="Main topics they post about")
    engagement_level: Optional[str] = Field(None, description="High/Medium/Low based on likes/comments")
    source_url: str = Field(default="", description="URL this data came from")


class ResearchQuality(BaseModel):
    """Metrics about research thoroughness and data quality."""

    sources_found: int = Field(default=0, description="Total number of sources accessed")
    urls_successfully_scraped: int = Field(default=0, description="URLs that returned useful data")
    urls_failed: int = Field(default=0, description="URLs that failed or were blocked")
    evidence_pieces: int = Field(default=0, description="Total evidence citations in report")
    quality_score: str = Field(
        default="Medium",
        description="High (5+ sources, all URLs worked), Medium (3-4 sources), Low (<3 sources)"
    )


# =============================================================================
# Stage 5: Outreach Drafts Output (LLM task)
# =============================================================================


class OutreachDraft(BaseModel):
    """A single outreach message draft."""

    channel: Literal["whatsapp", "email"] = Field(..., description="Message channel")
    subject: Optional[str] = Field(default=None, description="Subject line (email only)")
    body: str = Field(..., description="Message body")
    personalization_used: str = Field(
        ..., description="What data point made this personal (e.g., 'Their logistics services')"
    )


class OutreachDrafts(BaseModel):
    """Collection of outreach drafts for WhatsApp and email."""

    whatsapp_drafts: list[OutreachDraft] = Field(
        ..., min_length=1, max_length=2, description="1-2 WhatsApp messages (short, conversational)"
    )
    email_drafts: list[OutreachDraft] = Field(
        ..., min_length=1, max_length=2, description="1-2 email drafts (professional with subject)"
    )


class CompanyResearchReport(BaseModel):
    """Structured output: Research report for an SME prospect."""

    company_name: str = Field(..., description="Company name as discovered")
    industry: str = Field(..., description="Primary industry/sector")

    # Section 1: Company Overview
    overview: str = Field(..., description="What the company does, size indicators, market position")

    # Section 2: Products/Services (with citations)
    products_services: list[str] = Field(default_factory=list, description="Main offerings")

    # Section 3: Digital Presence
    digital_maturity: str = Field(..., description="Assessment of tech adoption based on online presence")
    social_insights: list[SocialMediaInsight] = Field(default_factory=list)

    # Section 4: AI Opportunities (with evidence)
    ai_opportunities: list[AIOpportunity] = Field(
        default_factory=list,
        description="Ranked AI adoption opportunities with supporting evidence"
    )

    # Section 5: Outreach Drafts (ready-to-send messages)
    outreach_drafts: Optional["OutreachDrafts"] = Field(
        default=None,
        description="Ready-to-send WhatsApp and email drafts"
    )

    # Legacy: Outreach Hooks (kept for backward compatibility)
    outreach_hooks: list[str] = Field(
        default_factory=list,
        description="Personalization angles for outreach based on research"
    )

    # Section 6: Sources
    sources: list[str] = Field(
        default_factory=list,
        description="All URLs that were successfully accessed and provided data"
    )

    # Section 7: Research Quality
    research_quality: Optional[ResearchQuality] = Field(
        default=None,
        description="Metrics about research thoroughness"
    )

    # Metadata
    data_quality: str = Field(default="Medium", description="High/Medium/Low based on available info")
    research_notes: Optional[str] = Field(None, description="Any caveats, limitations, or gaps")
