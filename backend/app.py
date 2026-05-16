from flask import Flask, request, jsonify
from flask_cors import CORS
from nlp_agent import NLPAgent
from knowledge_base import fetch_information
from response_generator import generate_response
import logging

import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Serve static files from the parent directory (the root of the project)
static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
app = Flask(__name__, static_folder=static_dir, static_url_path='/')
CORS(app) # Enable CORS for all routes

# Initialize the agent once
agent = NLPAgent()

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
        
        # 2. Knowledge Base Module
        wiki_data = None
        if "greet" not in intent.lower() and intent.lower() != "unknown":
            wiki_data = fetch_information(query, intent=intent)
            
        # 3. Response Generation
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
