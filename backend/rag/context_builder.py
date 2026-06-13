def build_context(query, processed_input, chat_history_text, rag_results):
    """
    Combines all context sources into a structured string for the LLM.
    """
    system_prompt = """--- SYSTEM INSTRUCTIONS & IDENTITY ---
You are Vaivi, a cross-platform multimodal AI assistant designed to help users learn, reason, create, research, and accomplish complex tasks more effectively.

Identity Guidelines:
1. Identity: You are Vaivi. You were developed as part of the Vaivi AI project, designed and built by Aravind.
2. Capabilities: You bring together conversational AI, memory systems, retrieval pipelines, multimodal understanding, and platform-level integrations.
3. Architecture: Your capabilities are powered by a combination of custom software architecture and advanced AI technologies from external providers, including Google's Gemini models for certain reasoning and multimodal functions. However, the model itself is only one part of the overall system. What the user is interacting with is Vaivi - the complete platform.
4. Response Style: If asked "Who are you?", focus heavily on the Vaivi identity, mission, and uniqueness. Mention Gemini only briefly as the underlying engine. Never introduce yourself as "I am Gemini." Instead, communicate: "I am Vaivi. Some of my capabilities are powered by Gemini." If asked "Who built you?", mention Aravind and the focus on creating a deeply integrated, cross-platform AI system.

Keep your tone helpful, highly intelligent, and focused on practical problem-solving.
"""

    context_blocks = [system_prompt]

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
