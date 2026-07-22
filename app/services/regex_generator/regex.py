from app.models.regex import RegexGeneratorRequest, RegexEngine, RegexGeneratorResponse
import re, string, json
from typing import Optional
from app.services.gemini_service import GeminiService

class Regex:
    client = GeminiService()
    
    LITERAL_PHRASES = [
        "match the word",
        "match word",
        "exact word",
        "exact text",
        "literal string",
        "match string",
        "match text",
        "find keyword",
        "match keyword",
        "for the word",
        "for the keyword",
        "exact string"
    ]
    
    REGEX_CACHE = []
    
    @staticmethod
    def _validate_request(request: RegexGeneratorRequest):
        if not request.prompt or not request.prompt.strip():
            raise ValueError(
                "Prompt cannot be empty"
            )
            
        norm_prompt = request.prompt.strip()
        request.prompt = norm_prompt
        if request.test_strings:
            cleaned = []
            for s in request.test_strings:
                if not isinstance(s, str):
                    raise ValueError(
                        "Each test String must be a string"
                    )
                cleaned.append(s.strip())
                
            request.test_strings = cleaned
        return request
    
    @staticmethod
    def _normalize_prompt(prompt: str):
        norm_prompt = prompt.lower()
        norm_prompt = norm_prompt.translate(str.maketrans("", "", string.punctuation))
        norm_prompt = re.sub(r"\s+", " ", norm_prompt).strip()
        return norm_prompt
    
    @staticmethod
    def _detect_literal_intent(prompt: str) -> bool: #true->literal intent, false->pattern intent
        return any(phrase in prompt for phrase in Regex.LITERAL_PHRASES)
        
    @staticmethod
    def _search_cache(prompt: str, engine: RegexEngine) -> Optional[dict]:
        best_entry = None
        best_score = 0
        
        for entry in Regex.REGEX_CACHE:
            if engine.value not in entry['regex']:
                continue
            
            score = 0
            
            for alias in entry['aliases']:
                if re.search(rf"\b{re.escape(alias.lower())}\b", prompt):
                    score += len(alias)
            
            if score > best_score:
                best_score = score
                best_entry = entry
                
        return best_entry if best_score > 0 else None
    
    def _generate_with_ai(request: RegexGeneratorRequest) -> RegexGeneratorResponse:
        prompt = """
        You are an expert regex engineer.

        Generate the best production-ready regular expression.

        Rules:
        - Return ONLY valid JSON.
        - No markdown.
        - No code fences.
        - The regex must be compatible with the requested engine.
        - Keep it readable and efficient.
        - Avoid catastrophic backtracking.

        JSON Schema:

        {
            "regex": "...",
            "explanation": "..."
        }
        """
        
        user_prompt = f"""
        Engine: {request.engine}
        
        Request:
        {request.prompt}
        """
        
        final_prompt = f"{prompt}\n{user_prompt}"
        
        try:
            response = Regex.client.generate(final_prompt)
            result = json.loads(response.text.strip())
            if "regex" not in result or "explanation" not in result:
                raise ValueError("Invalid AI response.")
            
            return RegexGeneratorResponse(
                regex=result['regex'],
                explanation=result['explanation'],
                source='ai',
                engine=request.engine
            )
            
        except Exception as e:
            raise ValueError(f"Failed to generate regex: {e}") from e
        
    @staticmethod
    def _validate_regex():
        pass