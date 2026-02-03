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

    # Section 5: Outreach Hooks
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
