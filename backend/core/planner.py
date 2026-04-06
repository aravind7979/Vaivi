import json
import google.generativeai as genai

text_model = genai.GenerativeModel('gemini-2.5-flash-lite')

def plan_task(processed_input, chat_history) -> dict:
    """
    A fast intent classification and planning step.
    Determines if RAG or vision processing is actually required based on query.
    """
    query = processed_input.get("user_query", "")
    has_screen = bool(processed_input.get("screen_summary", ""))
    
    # Simple heuristic routing for low latency if query is very short or specific.
    # We will use an LLM call to classify intent strictly.
    prompt = f"""
Given the user query, determine the intent and requirements for the task.
Output ONLY a raw JSON object with no markdown formatting or backticks.
Schema:
{{
    "intent": "qa" | "summarize" | "debug" | "action" | "explain",
    "requires_rag": true/false,
    "requires_vision": true/false
}}

User Query: {query}
Has Screen Context Provided: {str(has_screen).lower()}
"""
    try:
        response = text_model.generate_content(prompt)
        text = response.text.replace("```json", "").replace("```", "").strip()
        plan = json.loads(text)
        
        # Override vision requirement if no screen context is even possible
        if not has_screen:
            plan["requires_vision"] = False
            
        return plan
    except Exception as e:
        print(f"Planner failed or failed to parse JSON: {e}")
        # Default safe fallback
        return {
            "intent": "qa",
            "requires_rag": True,
            "requires_vision": has_screen
        }
