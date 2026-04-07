def build_context(query, processed_input, chat_history_text, rag_results):
    """
    Combines all context sources into a structured string for the LLM.
    """
    context_blocks = []

    if rag_results:
        rag_text = "--- KNOWLEDGE BASE CONTEXT ---\n"
        for i, res in enumerate(rag_results):
            rag_text += f"Fact {i+1} (Source: {res['source']}): {res['text']}\n"
        context_blocks.append(rag_text)

    if processed_input.get("screen_text") or processed_input.get("screen_summary"):
        screen_text = "--- SCREEN CONTEXT ---\n"
        if processed_input.get("screen_summary"):
            screen_text += f"Screen Insight: {processed_input['screen_summary']}\n"
        if processed_input.get("screen_text"):
            screen_text += f"Visible Text: {processed_input['screen_text']}\n"
        context_blocks.append(screen_text)

    if chat_history_text:
        context_blocks.append(f"--- RECENT CHAT HISTORY ---\n{chat_history_text}")

    context_blocks.append(f"--- USER QUERY ---\n{query}")

    return "\n\n".join(context_blocks)
