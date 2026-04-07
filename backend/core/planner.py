import json
import google.generativeai as genai
import os

model = None

def get_model():
    global model
    if model is None:
        model = genai.GenerativeModel('gemini-2.5-flash-lite')
    return model

def plan_task(processed_input, chat_history_text):
    """
    Classify user intent and decide what pipeline components to activate.
    """
    query = processed_input.get("user_query", "")
    if not query:
        return {
            "intent": "qa",
            "requires_rag": False,
            "requires_vision": bool(processed_input.get("screen_summary") or processed_input.get("screen_text")),
            "response_type": "text"
        }

    prompt = f"""
    Analyze the user's query and recent chat history to determine the intent and required tools.
    
    Query: "{query}"
    
    Output JSON with the following boolean and string fields:
    - intent: one of ["qa", "summarize", "debug", "action", "explain"]
    - requires_rag: True if the query asks about general knowledge, facts, concepts, or system documentation.
    - requires_vision: True if the query asks about something on the screen, an image, code currently visible, or UI elements.
    - response_type: "text", "structured", or "suggestion"
    
    Return ONLY raw JSON, no markdown blocks.
    """
    
    try:
        response = get_model().generate_content(prompt)
        text = response.text.replace("```json", "").replace("```", "").strip()
        plan = json.loads(text)
        
        # Ensure fallback defaults
        if "requires_vision" not in plan:
            plan["requires_vision"] = bool(processed_input.get("screen_summary"))
            
        return plan
    except Exception as e:
        print(f"Planner error: {e}")
        # Safe fallback
        return {
            "intent": "qa",
            "requires_rag": True,
            "requires_vision": True,
            "response_type": "text"
        }
