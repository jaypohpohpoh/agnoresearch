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
    ai_opportunities: list[AIOpportunity] = Field(default_factory=list, description="Ranked AI adoption opportunities")

    # Section 5: Outreach Hooks
    outreach_hooks: list[str] = Field(
        default_factory=list,
        description="Personalization angles for outreach based on research"
    )

    # Section 6: Sources
    sources: list[str] = Field(default_factory=list, description="URLs that were successfully scraped")

    # Metadata
    data_quality: str = Field(default="Medium", description="High/Medium/Low based on available info")
    research_notes: Optional[str] = Field(None, description="Any caveats, limitations, or gaps")
