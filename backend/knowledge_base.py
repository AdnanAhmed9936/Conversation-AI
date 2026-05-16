import wikipedia
import logging
import re

logger = logging.getLogger(__name__)

def clean_response(text: str) -> str:
    """
    Removes irrelevant text, repeated phrases, and Wikipedia-style formatting.
    Improves readability and keeps responses conversational.
    """
    if not text:
        return ""
    # Remove bracketed citations like [1], [note 1]
    text = re.sub(r'\[.*?\]', '', text)
    # Remove Wikipedia headings e.g. == History ==
    text = re.sub(r'==.*?==', '', text)
    # Remove multiple spaces/newlines
    text = " ".join(text.split())
    return text.strip()

def validate_confidence(query: str, summary: str) -> bool:
    """
    Implement confidence validation.
    Checks if fetched information is relevant and rejects random list dumps.
    """
    lower_sum = summary.lower()
    
    # Reject disambiguation pages or raw lists that slipped through
    if "may refer to:" in lower_sum or "is a list of" in lower_sum or "can refer to:" in lower_sum:
        return False
        
    # Reject extremely short anomalies
    if len(summary.split()) < 3:
        return False
        
    return True

def fetch_information(query: str, intent: str = "unknown") -> dict:
    """
    Fetches summary information from Wikipedia.
    Uses Smart Search to find the best article, limits sentences based on intent,
    and applies cleaning and confidence filtering.
    """
    if not query or not query.strip():
        return {"status": "error", "message": "Empty query provided.", "data": ""}

    try:
        wikipedia.set_lang("en")
        
        # IMPLEMENT QUERY-TYPE HANDLING: Different query types produce different response styles.
        intent_lower = intent.lower()
        if "fact" in intent_lower or "short" in intent_lower or "question" in intent_lower:
            sentences = 1
        elif "definit" in intent_lower or "what is" in query.lower() or "who is" in query.lower():
            sentences = 2
        elif "explain" in intent_lower or "detail" in intent_lower or "long" in intent_lower:
            sentences = 4
        else:
            sentences = 2 # Default

        # SMART SEARCH: Find the most relevant article title first.
        # This resolves issues where query "capital of india" needed the "New Delhi" article.
        search_results = wikipedia.search(query)
        
        if not search_results:
            return {
                "status": "error",
                "message": "Sorry, I could not find a precise answer.",
                "data": ""
            }
            
        best_title = search_results[0]
        
        # KNOWLEDGE EXTRACTION IMPROVEMENT: Optimized approach using specific sentences
        raw_summary = wikipedia.summary(best_title, sentences=sentences, auto_suggest=False)
        
        # CONFIDENCE CHECKING
        if not validate_confidence(query, raw_summary):
            return {
                "status": "error",
                "message": "Sorry, I could not find a precise answer.",
                "data": ""
            }
            
        # RESPONSE CLEANING
        clean_summary = clean_response(raw_summary)
        
        return {
            "status": "success",
            "message": "Data fetched successfully.",
            "data": clean_summary
        }
        
    except wikipedia.exceptions.DisambiguationError as e:
        logger.warning(f"Disambiguation error for query '{query}'. Options: {e.options}")
        # Try to gracefully handle by picking the first suggestion
        try:
            if e.options:
                raw_summary = wikipedia.summary(e.options[0], sentences=sentences, auto_suggest=False)
                if validate_confidence(query, raw_summary):
                    return {
                        "status": "success",
                        "message": "Data fetched successfully using disambiguation fallback.",
                        "data": clean_response(raw_summary)
                    }
        except Exception:
            pass
            
        return {
            "status": "error",
            "message": "Sorry, I could not find a precise answer.",
            "data": ""
        }
            
    except wikipedia.exceptions.PageError:
        logger.warning(f"No Wikipedia page found for '{query}'.")
        return {
            "status": "error",
            "message": "Sorry, I could not find a precise answer.",
            "data": ""
        }
        
    except Exception as e:
        logger.error(f"Error fetching data from Wikipedia for '{query}': {e}")
        return {
            "status": "error",
            "message": "I'm having trouble accessing my knowledge base right now. Please try again later.",
            "data": ""
        }
