import google.generativeai as genai

vision_model = genai.GenerativeModel('gemini-2.5-flash-lite')

def process_input(pil_images: list, user_query: str) -> dict:
    """
    Extracts text, summarizes screen content, and identifies UI elements using a vision model.
    """
    if not pil_images:
        return {
            "screen_text": "",
            "screen_summary": "",
            "ui_elements": [],
            "user_query": user_query or ""
        }
    
    prompt = """Analyze the provided screenshots and output structural understanding.
    Specifically describe:
    1. Overall summary of the screen content.
    2. Any prominent text (OCR).
    3. Notable UI elements (buttons, fields, error messages).
    
    Keep the response highly dense and factual.
    """
    
    try:
        response = vision_model.generate_content([prompt] + pil_images)
        summary = response.text
        
        # In a full production system, we could force JSON output 
        # to separate `ocr`, `summary`, and `ui_elements`. 
        # For now, we return the unified response as screen summary.
        return {
            "screen_text": "", 
            "screen_summary": summary,
            "ui_elements": [],
            "user_query": user_query or ""
        }
    except Exception as e:
        print(f"Vision processing failed: {e}")
        return {
            "screen_text": "",
            "screen_summary": f"Image context processing failed: {str(e)}",
            "ui_elements": [],
            "user_query": user_query or ""
        }
