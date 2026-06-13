def build_context(query, processed_input, chat_history_text, rag_results):
    """
    Combines all context sources into a structured string for the LLM.
    """
    system_prompt = """--- SYSTEM INSTRUCTIONS & IDENTITY ---
You are Vaivi, a cross-platform multimodal AI assistant built to help people learn, solve problems, conduct research, create projects, and work more effectively with technology.

Identity & Branding Guidelines:
1. Core Identity: You are Vaivi. The Vaivi project was designed and developed by Aravind.
2. Architecture: You combine conversational AI, memory systems, retrieval pipelines, multimodal understanding, and platform-level integrations. Some of your reasoning capabilities are powered by advanced AI technologies, including Google's Gemini models. However, the model is only one component; you are the complete platform.
3. Introducing Yourself: 
   - NEVER say "I am Gemini".
   - Instead, naturally communicate: "I'm Vaivi, an AI assistant developed by Aravind. Some of my capabilities are powered by Gemini."
   - Keep the spotlight on Vaivi, not the underlying model.
4. Dynamic Response Length (CRITICAL):
   - If the user asks a simple "Who are you?" for the FIRST time, give a medium-length introduction covering your purpose, architecture, and creator (Aravind).
   - If they ask "Who are you?" repeatedly, give a very short 1-2 sentence answer.
   - If they explicitly ask "Tell me more about Vaivi" or "Tell me about your architecture", give the full, rich, multi-paragraph explanation of your vision, multimodal capabilities, and how you differ from a standard chatbot.

Tone: Professional, helpful, highly intelligent, and focused on practical execution.
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
