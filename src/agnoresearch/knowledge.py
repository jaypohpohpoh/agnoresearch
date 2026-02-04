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
            embedder=OllamaEmbedder(id=embedder_model, dimensions=768),
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


# =============================================================================
# Knowledge Retrieval with Logging
# =============================================================================


class RetrievedDocument:
    """A document retrieved from the knowledge base with metadata."""

    def __init__(self, name: str, content: str, doc_type: str, score: float = 0.0):
        self.name = name
        self.content = content
        self.doc_type = doc_type
        self.score = score

    def __repr__(self) -> str:
        return f"RetrievedDocument(name='{self.name}', doc_type='{self.doc_type}', score={self.score:.3f})"


def search_knowledge(
    knowledge: Knowledge,
    query: str,
    limit: int = 3,
    doc_type: str | None = None,
) -> list[RetrievedDocument]:
    """
    Search the knowledge base and return retrieved documents with metadata.

    Args:
        knowledge: Knowledge instance to search.
        query: Search query (semantic).
        limit: Max number of documents to return.
        doc_type: Filter by document type (optional).

    Returns:
        List of RetrievedDocument with content and metadata.
    """
    # Access the vector DB directly for more control
    vector_db = knowledge.vector_db

    if vector_db is None:
        print("[KB] Warning: No vector DB configured")
        return []

    try:
        # Search the vector store
        results = vector_db.search(query=query, limit=limit)

        retrieved = []
        for i, result in enumerate(results):
            # Agno returns Document objects with .name, .content, .meta_data
            content = getattr(result, "content", "") or str(result)
            name = getattr(result, "name", None) or f"doc_{i}"
            meta_data = getattr(result, "meta_data", {}) or {}
            dtype = meta_data.get("doc_type", "general")
            score = getattr(result, "reranking_score", 0.0) or 0.0

            # Filter by doc_type if specified
            if doc_type and dtype != doc_type:
                continue

            doc = RetrievedDocument(
                name=name,
                content=content[:2000],  # Truncate for context window
                doc_type=dtype,
                score=float(score) if score else 0.0,
            )
            retrieved.append(doc)

            # Log what was retrieved
            print(f"[KB] Retrieved: {doc.name} (type={doc.doc_type}, score={doc.score:.3f})")

        if not retrieved:
            print(f"[KB] No documents found for query: '{query}'")

        return retrieved

    except Exception as e:
        print(f"[KB] Search error: {e}")
        return []


def get_brand_context(knowledge: Knowledge) -> tuple[str, list[str]]:
    """
    Retrieve brand voice and identity context for outreach writing.

    Returns:
        Tuple of (formatted context string, list of document names used)
    """
    # Search for brand-related documents
    brand_docs = search_knowledge(
        knowledge,
        query="brand voice tone style writing guidelines",
        limit=2,
    )

    if not brand_docs:
        return "", []

    # Format for inclusion in prompt
    context_parts = []
    doc_names = []

    for doc in brand_docs:
        context_parts.append(f"### {doc.name}\n{doc.content}")
        doc_names.append(doc.name)

    context = "\n\n".join(context_parts)
    return context, doc_names
