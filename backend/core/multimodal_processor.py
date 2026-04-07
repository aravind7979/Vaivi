import google.generativeai as genai
import base64
import io
from PIL import Image

def process_input(screenshot_base64: str = None, user_query: str = ""):
    """
    Separates perception from reasoning.
    Extracts structured knowledge (OCR, summaries) from the screen.
    """
    result = {
        "screen_text": "",
        "screen_summary": "",
        "ui_elements": [],
        "user_query": user_query
    }

    if not screenshot_base64:
        return result

    try:
        # Decode base64 
        if "," in screenshot_base64:
            screenshot_base64 = screenshot_base64.split(",")[1]
            
        img_data = base64.b64decode(screenshot_base64)
        img = Image.open(io.BytesIO(img_data))
        
        vision_model = genai.GenerativeModel('gemini-2.5-flash-lite')
        
        prompt = """
        Analyze this screenshot concisely.
        1. Summarize what is on the screen (context).
        2. Extract any important readable text, code, or terminal output.
        3. List key UI elements (buttons, menus, errors).
        """
        
        response = vision_model.generate_content([prompt, img])
        result["screen_summary"] = response.text
        
        # We store the raw base64 as well in case the orchestrator needs to pass it to the final LLM
        result["screenshot_base64"] = screenshot_base64
        
    except Exception as e:
        print(f"Vision processing error: {e}")
        
    return result
