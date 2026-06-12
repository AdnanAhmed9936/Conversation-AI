import os
import json
import logging
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

class NLPAgent:
    def __init__(self):
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
        self.api_key = os.environ.get("LLM_API_KEY", "")
        self.model = "llama-3.1-8b-instant"
        self.timeout = 15

    def build_prompt(self, user_text: str) -> list:
        system_instruction = (
            "You are an expert NLP preprocessing agent. Your task is to clean and normalize user input. "
            "You must analyze the COMPLETE query, paying careful attention to all words, context modifiers (such as time like 'today', 'latest', 'current', 'now', or locations, or other qualifiers), rather than just the first keyword. "
            "You must correct spelling, fix grammar, normalize the sentence, and detect the user's intent. "
            "Identify the user's intent from the full query context. "
            "If the query asks for real-time, current, live information, weather, or current events (e.g., 'news today', 'weather in London', 'latest movies'), "
            "classify the intent as 'real-time' and set 'wikipedia_search_query' to null. "
            "Crucially, for factual/definition queries, extract the best 'wikipedia_search_query' which is the exact Wikipedia article title that would directly answer the user's prompt (e.g. if user asks 'capital of india', the best article is 'New Delhi'. If 'who is elon musk', the article is 'Elon Musk'. If 'capital of France', the best article is 'Paris'). "
            "You MUST respond ONLY with a valid, raw JSON object and no surrounding text, markdown formatting, or explanations. "
            "The JSON MUST exactly match this schema:\n"
            "{\n"
            '  "original_input": "<the exact original user text>",\n'
            '  "corrected_input": "<the text with corrected spelling and grammar>",\n'
            '  "normalized_input": "<lowercase, punctuation-stripped, and standardized version of the text>",\n'
            '  "intent": "<short string: MUST be either \\"factual\\", \\"definition\\", \\"greeting\\", \\"small talk\\", \\"long explanation\\", or \\"real-time\\">",\n'
            '  "wikipedia_search_query": "<the exact Wikipedia article title to search for, or null if it cannot be answered by static Wikipedia articles, e.g. for real-time/live/opinion/weather/current queries>",\n'
            '  "confidence": <a float between 0.0 and 1.0 representing intent confidence>,\n'
            '  "errors_detected": {\n'
            '    "spelling": <true/false>,\n'
            '    "grammar": <true/false>,\n'
            '    "clarity": <true/false>\n'
            "  }\n"
            "}\n"
        )
        # Using standard chat format messages
        messages = [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": f"User input to process: \"{user_text}\""}
        ]
        return messages

    def call_llm_api(self, messages: list) -> str:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.0,
            "response_format": { "type": "json_object" } # Using JSON mode
        }
        
        try:
            logger.info(f"Sending request to LLM API ({self.api_url}) using model: {self.model}")
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=self.timeout)
            response.raise_for_status()
            
            # The standard OpenAI format returns the response in choices[0].message.content
            return response.json().get("choices", [{}])[0].get("message", {}).get("content", "")
            
        except requests.exceptions.Timeout:
            logger.error(f"Request to LLM service timed out after {self.timeout} seconds.")
            raise RuntimeError("LLM service timeout.")
        except requests.exceptions.RequestException as e:
            logger.error(f"Request to LLM service failed: {e}")
            raise RuntimeError(f"LLM service connection error: {e}")

    def parse_response(self, raw_response: str, original_input: str) -> dict:
        try:
            parsed_data = json.loads(raw_response)
            required_keys = ["original_input", "corrected_input", "normalized_input", "intent", "wikipedia_search_query", "confidence", "errors_detected"]
            for key in required_keys:
                if key not in parsed_data:
                    parsed_data[key] = None
            if not isinstance(parsed_data.get("errors_detected"), dict):
                parsed_data["errors_detected"] = {"spelling": False, "grammar": False, "clarity": False}
            return parsed_data
        except json.JSONDecodeError:
            logger.error(f"Failed to parse LLM response as JSON. Raw response: {raw_response}")
            return {
                "original_input": original_input,
                "corrected_input": original_input,
                "normalized_input": original_input.lower().strip(),
                "intent": "unknown",
                "wikipedia_search_query": original_input.lower().strip(),
                "confidence": 0.0,
                "errors_detected": {"spelling": False, "grammar": False, "clarity": False},
                "system_error": "Failed to parse LLM response"
            }

    def process(self, user_text: str) -> dict:
        messages = self.build_prompt(user_text)
        raw_response = self.call_llm_api(messages)
        return self.parse_response(raw_response, user_text)
