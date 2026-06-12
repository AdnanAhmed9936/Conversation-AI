from flask import Flask, request, jsonify
from flask_cors import CORS
from backend.nlp_agent import NLPAgent
from backend.knowledge_base import fetch_information
from backend.response_generator import generate_response
import logging
import requests
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Serve static files from the parent directory (the root of the project)
static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
app = Flask(__name__, static_folder=static_dir, static_url_path='/')
CORS(app) # Enable CORS for all routes

# Initialize the agent once
agent = NLPAgent()

def call_groq_direct(user_text: str, detailed: bool = False) -> str:
    """
    Directly sends the query to the Groq API, bypassing the NLP processing.
    """
    api_key = os.environ.get("LLM_API_KEY", "")
    model = "llama-3.1-8b-instant"
    api_url = "https://api.groq.com/openai/v1/chat/completions"
    
    system_prompt = "You are a helpful assistant. Keep your response short, precise, and concise (usually under 2-3 sentences or a very brief list)."
    if detailed:
        system_prompt = "You are a helpful assistant. Provide a detailed, comprehensive, and in-depth explanation to the user's query."
        
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_text}
    ]
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.7 if detailed else 0.3
    }
    
    response = requests.post(api_url, headers=headers, json=payload, timeout=15)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]

def is_detailed_request(text: str, intent: str) -> bool:
    """
    Detects if the user requests a detailed, comprehensive, or in-depth explanation.
    """
    text_lower = text.lower()
    keywords = [
        "explain in detail",
        "detailed explanation",
        "elaborate",
        "comprehensive answer",
        "in-depth",
        "detailed answer",
        "comprehensive explanation",
        "explain thoroughly",
        "thorough explanation",
        "go into detail",
        "write a detailed"
    ]
    if any(kw in text_lower for kw in keywords):
        return True
    if "long explanation" in intent.lower():
        return True
    return False

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/api/process', methods=['POST'])
def process_input():
    data = request.get_json()
    
    if not data or 'text' not in data:
        return jsonify({"error": "Missing 'text' in request body"}), 400
        
    user_text = data['text']
    
    try:
        # 1. Process Input & Recognize Intent
        result = agent.process(user_text)
        
        intent = result.get('intent', 'unknown')
        query = result.get('wikipedia_search_query') or result.get('normalized_input') or result.get('corrected_input') or user_text
        
        # Check if the user requests a detailed explanation
        if is_detailed_request(user_text, intent):
            try:
                logging.info(f"Routing detailed query directly to Groq: '{user_text}'")
                groq_response = call_groq_direct(user_text, detailed=True)
                return groq_response, 200, {'Content-Type': 'text/plain; charset=utf-8'}
            except Exception as e:
                logging.error(f"Error calling Groq for detailed response: {e}")
                return jsonify({"error": "Failed to generate detailed response from AI."}), 500
        
        # 2. Knowledge Base Module
        wiki_data = None
        is_greeting_or_smalltalk = "greet" in intent.lower() or "small talk" in intent.lower()
        is_real_time = intent.lower() == "real-time" or not result.get('wikipedia_search_query')
        
        if not is_greeting_or_smalltalk and not is_real_time:
            try:
                wiki_data = fetch_information(query, intent=intent)
            except Exception as e:
                logging.error(f"Knowledge Base error: {e}")
                wiki_data = {"status": "error", "message": str(e), "data": ""}
                
        # 3. Response Generation & Fallback Check
        if not is_greeting_or_smalltalk and (wiki_data is None or wiki_data.get("status") == "error"):
            try:
                logging.info(f"Knowledge Base/Wikipedia failed. Falling back to Groq for query: '{user_text}'")
                groq_response = call_groq_direct(user_text, detailed=False)
                return groq_response, 200, {'Content-Type': 'text/plain; charset=utf-8'}
            except Exception as e:
                logging.error(f"Error calling Groq in fallback: {e}")
                return jsonify({"error": "Failed to connect to the fallback AI service."}), 500
                
        # Generate standard response for greeting/smalltalk or successful Wikipedia data
        final_response = generate_response(intent, wiki_data, user_text)
        
        # Return plain text directly for the UI
        return final_response, 200, {'Content-Type': 'text/plain; charset=utf-8'}
    except TypeError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logging.error(f"Error in process_input: {e}")
        return jsonify({"error": "An internal error occurred."}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)

