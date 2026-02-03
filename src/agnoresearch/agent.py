"""SME Research Agent definition."""

from pathlib import Path

from agno.agent import Agent
from agno.models.ollama import Ollama
from agno.db.sqlite import SqliteDb
from agno.knowledge.knowledge import Knowledge

from .schemas import CompanyResearchReport
from .tools import browse_url, search_facebook, browse_instagram
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
        tools=[browse_url, search_facebook, browse_instagram],
        knowledge=knowledge,
        search_knowledge=True,
        description=SYSTEM_PROMPT,
        instructions=INSTRUCTIONS,
        output_schema=CompanyResearchReport,
        db=SqliteDb(db_file=str(db_path)),
        markdown=True,
        add_datetime_to_context=True,
    )
