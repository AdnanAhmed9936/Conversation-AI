from flask import Flask, request, jsonify
from flask_cors import CORS
from nlp_agent import NLPAgent
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
        result = agent.process(user_text)
        return jsonify(result), 200
    except TypeError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": "An internal error occurred."}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
