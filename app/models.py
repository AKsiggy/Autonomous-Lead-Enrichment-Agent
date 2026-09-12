from typing import Optional

from pydantic import BaseModel, Field


class ContactPoint(BaseModel):
    email: str
    context: Optional[str] = None


class TeamMember(BaseModel):
    name: str
    role: Optional[str] = None
    linkedin_url: Optional[str] = None


class CompanyIntelligence(BaseModel):
    domain: str
    company_overview: str = Field(
        description="Exactly two concise sentences describing the company."
    )
    target_audience_icp: str
    contact_points: list[ContactPoint] = Field(default_factory=list)
    key_leadership_team: list[TeamMember] = Field(default_factory=list)
    data_confidence_score: float = Field(ge=0.0, le=1.0)


class ScrapedPage(BaseModel):
    url: str
    title: str
    text: str
    emails: list[str] = Field(default_factory=list)
    linkedin_urls: list[str] = Field(default_factory=list)

class CrawlResult(BaseModel):
    domain: str
    pages: list[ScrapedPage] = Field(default_factory=list)
    discovered_urls: list[str] = Field(default_factory=list)
    
class DomainContext(BaseModel):
    domain: str
    pages: list[ScrapedPage] = Field(default_factory=list)
    discovered_urls: list[str] = Field(default_factory=list)
