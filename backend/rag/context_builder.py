from .rag_retriever import retrieve

def build_context(query: str, screen_data: dict, memory_messages: list, requires_rag: bool = True) -> dict:
    """
    Fuses multiple sources of context: memory, screen perception, and RAG knowledge base.
    """
    rag_context_text = ""
    sources = []

    # 1. Fetch RAG context conditionally
    if requires_rag and query:
        retrieved_chunks = retrieve(query, top_k=3)
        if retrieved_chunks:
            lines = []
            for idx, chunk in enumerate(retrieved_chunks):
                domain = chunk["metadata"].get("domain", "General")
                lines.append(f"Source [{idx+1}] ({domain}): {chunk['text']}")
                sources.append(chunk["metadata"])
            rag_context_text = "\n\n".join(lines)

    # 2. Extract Screen Context
    screen_context_text = ""
    if screen_data:
        summary = screen_data.get("screen_summary", "")
        screen_text = screen_data.get("screen_text", "")
        if summary or screen_text:
            screen_context_text = f"Screen Summary: {summary}\nScreen Text: {screen_text}"

    # 3. Format Conversation Memory Context
    memory_context_text = ""
    if memory_messages:
        lines = []
        for msg in memory_messages:
            lines.append(f"{msg['role'].capitalize()}: {msg['content']}")
        memory_context_text = "\n".join(lines)

    return {
        "rag_context": rag_context_text,
        "screen_context": screen_context_text,
        "memory_context": memory_context_text,
        "sources": sources
    }
