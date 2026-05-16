import random

def generate_response(intent: str, data: dict = None, user_text: str = "") -> str:
    """
    Generates a natural, conversational AI response based on the intent and Wikipedia data.
    """
    if intent is None:
        intent = "unknown"
        
    intent = intent.lower()
    user_text_lower = user_text.lower()
    
    # Override intent if it's obvious small talk
    if "name" in user_text_lower or "who are you" in user_text_lower:
        return "I am an AI assistant here to help you find factual information!"
    if "how are you" in user_text_lower:
        return "I'm just a computer program, but I'm doing great! How can I help you today?"
    if "who made you" in user_text_lower or "creator" in user_text_lower:
        return "I am an AI assistant built for a college project to demonstrate multi-agent coordination."

    # Pre-defined templates for greetings
    greeting_responses = [
        "Hello! How can I assist you today?",
        "Hi there! What would you like to know?",
        "Greetings! I'm ready to help you with your questions."
    ]
    
    # Pre-defined templates for unknown or unhandled queries
    unknown_responses = [
        "I'm not quite sure what you mean. Could you please rephrase?",
        "I didn't catch that. Could you provide more details?",
        "I'm still learning and don't have a specific answer for that right now."
    ]

    if "greet" in intent or intent == "greeting":
        return random.choice(greeting_responses)
        
    elif "small talk" in intent:
        if "name" in user_text_lower:
            return "I am an AI assistant here to help you find factual information!"
        elif "how are you" in user_text_lower:
            return "I'm just a computer program, but I'm doing great! How can I help you today?"
        elif "who made you" in user_text_lower or "creator" in user_text_lower:
            return "I am an AI assistant built for a college project to demonstrate multi-agent coordination."
        else:
            return "I am an AI assistant dedicated to answering your questions. Let me know what you'd like to learn about!"

    elif intent in ["unknown", "unclear"]:
        return random.choice(unknown_responses)
        
    else:
        # For informational or other specific queries, use the fetched data
        if isinstance(data, dict):
            status = data.get("status", "error")
            message = data.get("message", "")
            info_text = data.get("data", "")
            
            if status == "success" and info_text:
                # Direct answer, no padding
                final_response = info_text.strip()
                
                # Ensure the first letter is capitalized
                if final_response:
                    final_response = final_response[0].upper() + final_response[1:]
                    
                return final_response
            else:
                # Return the error message from the knowledge base (e.g. disambiguation or page not found)
                return message if message else random.choice(unknown_responses)
        else:
            # Fallback if data is empty or not in expected format
            return random.choice(unknown_responses)
