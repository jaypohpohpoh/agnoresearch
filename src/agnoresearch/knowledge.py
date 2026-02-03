"""Knowledge base management using LanceDB + Ollama embeddings."""

import asyncio
from pathlib import Path
from agno.knowledge.knowledge import Knowledge
from agno.vectordb.lancedb import LanceDb
from agno.knowledge.embedder.ollama import OllamaEmbedder


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
