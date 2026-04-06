import google.generativeai as genai
from .multimodal_processor import process_input
from .planner import plan_task
from .actions import get_suggested_actions
from rag.context_builder import build_context

text_model = genai.GenerativeModel('gemini-2.5-flash-lite')

def construct_prompt(plan: dict, context: dict, query: str) -> str:
    """
    Dynamically builds the final LLM prompt based on the plan and context.
    Enforces format constraints specifically for math.
    """
    prompt_lines = [
        "You are Vaivi, an intelligent, multimodal Copilot assistant.",
        "Your goal is to be incredibly helpful, clear, and concise.",
        "",
        "CRITICAL INSTRUCTION FOR MATH FORMULAS:",
        "Math formulas MUST NOT be output in LaTeX format (e.g., no \\frac or \\sqrt).",
        "Instead, output math as plain human-readable text. For example: '(-b ± √(b² - 4ac)) / (2a)'.",
        "This is a strict requirement to prevent UI crashes.",
        ""
    ]
    
    if plan.get("requires_rag") and context.get("rag_context"):
        prompt_lines.append("=== KNOWLEDGE BASE CONTEXT ===")
        prompt_lines.append(context["rag_context"])
        prompt_lines.append("")
        
    if plan.get("requires_vision") and context.get("screen_context"):
        prompt_lines.append("=== SCREEN PERCEPTION CONTEXT ===")
        prompt_lines.append(context["screen_context"])
        prompt_lines.append("")
        
    if context.get("memory_context"):
        prompt_lines.append("=== RECENT CONVERSATION HISTORY ===")
        prompt_lines.append(context["memory_context"])
        prompt_lines.append("")
        
    prompt_lines.append("=== USER QUERY ===")
    prompt_lines.append(query)
    
    return "\n".join(prompt_lines)

def route_and_answer(query: str, pil_images: list, chat_history: list):
    """
    The main Copilot Orchestration Pipeline.
    """
    # Step 1: Multimodal Processing
    processed = process_input(pil_images, query)
    
    # Step 2: Intent & Task Planning
    plan = plan_task(processed, chat_history)
    
    # Step 3: Context Building (Conditional RAG & memory fusion)
    context = build_context(
        query=query, 
        screen_data=processed, 
        memory_messages=chat_history, 
        requires_rag=plan.get("requires_rag", True)
    )
    
    # Step 4: Prompt Construction
    final_prompt = construct_prompt(plan, context, query)
    
    # Step 5: Execute Model
    try:
        response = text_model.generate_content(final_prompt)
        ai_response = response.text
    except Exception as e:
        ai_response = f"I'm sorry, I encountered an error during response generation: {str(e)}"
        
    # Step 6: Post-process actions
    actions = get_suggested_actions(plan.get("intent", "qa"), query)
    
    return {
        "response": ai_response,
        "debug_info": {
            "intent": plan.get("intent", "unknown"),
            "rag_used": bool(context.get("rag_context")),
            "vision_used": plan.get("requires_vision", False),
            "sources": context.get("sources", []),
            "suggested_actions": actions
        }
    }
