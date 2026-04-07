import time
import google.generativeai as genai
from core.multimodal_processor import process_input
from core.planner import plan_task
from core.memory import build_chat_history
from core.actions import suggest_actions
from rag.context_builder import build_context
from rag.rag_retriever import get_retriever

model = None
vision_model = None

def get_models():
    global model, vision_model
    if model is None:
        model = genai.GenerativeModel('gemini-2.5-flash-lite')
        vision_model = genai.GenerativeModel('gemini-2.5-flash-lite')
    return model, vision_model

def route_and_answer(user_query: str, screenshot_base64: str, db_messages: list):
    """
    The main Orchestrator for the pipeline.
    """
    times = {}
    
    # 1. Memory Processing
    t0 = time.time()
    chat_history_text = build_chat_history(db_messages)
    times["memory"] = int((time.time() - t0) * 1000)

    # 2. Multimodal Processing (Perception)
    t0 = time.time()
    processed = process_input(screenshot_base64, user_query)
    times["perception"] = int((time.time() - t0) * 1000)

    # 3. Planning
    t0 = time.time()
    plan = plan_task(processed, chat_history_text)
    times["planning"] = int((time.time() - t0) * 1000)

    # 4. RAG Retrieval (Conditional)
    t0 = time.time()
    rag_results = []
    if plan.get("requires_rag") and user_query:
        rag_results = get_retriever().retrieve(user_query, top_k=3)
    times["retrieval"] = int((time.time() - t0) * 1000)

    # 5. Context Building
    t0 = time.time()
    final_prompt = build_context(user_query, processed, chat_history_text, rag_results)
    
    # Strictly ensure human-readable maths in system instructions
    final_prompt = "INSTRUCTION: Provide math formulas in plain human-readable text (e.g. `(-b ± √(b² - 4ac)) / (2a)`) and NEVER in LaTeX.\n\n" + final_prompt
    times["context_fusion"] = int((time.time() - t0) * 1000)

    # 6. Final LLM Inference
    t0 = time.time()
    text_model, vis_model = get_models()
    
    try:
        if processed.get("screenshot_base64") and plan.get("requires_vision"):
            # If we need the raw vision output directly beyond the processor's summary
            import io
            import base64
            from PIL import Image
            img_data = base64.b64decode(processed["screenshot_base64"])
            img = Image.open(io.BytesIO(img_data))
            response = vis_model.generate_content([final_prompt, img])
        else:
            response = text_model.generate_content(final_prompt)
            
        ai_response_text = response.text
    except Exception as e:
        ai_response_text = f"Error generating response: {e}"
        
    times["llm"] = int((time.time() - t0) * 1000)

    # 7. Post-processing Action scaffolding
    actions = suggest_actions(plan, ai_response_text)

    # 8. Formatting output structured for the client
    structured_output = {
        "response": ai_response_text,
        "actions": actions,
        "debug_metrics": {
            "intent": plan.get("intent"),
            "rag_used": plan.get("requires_rag"),
            "vision_used": plan.get("requires_vision"),
            "latency_ms": times
        }
    }

    return structured_output
