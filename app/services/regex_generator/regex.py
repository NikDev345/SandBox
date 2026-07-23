from app.models.regex import RegexGeneratorRequest, RegexEngine, RegexMatchResult, RegexGeneratorResponse
import re, string, json
from typing import Optional,List
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
    
    patterns = [
        r"match\s+the\s+word\s+(.+)$",
        r"match\s+word\s+(.+)$",
        r"exact\s+word\s+(.+)$",
        r"exact\s+text\s+(.+)$",
        r"literal\s+string\s+(.+)$",
        r"match\s+string\s+(.+)$",
        r"match\s+text\s+(.+)$",
        r"find\s+keyword\s+(.+)$",
        r"match\s+keyword\s+(.+)$",
        r"for\s+the\s+word\s+(.+)$",
        r"for\s+word\s+(.+)$",
        r"for\s+the\s+keyword\s+(.+)$",
        r"for\s+keyword\s+(.+)$",
        r"for\s+the\s+string\s+(.+)$",
        r"for\s+string\s+(.+)$",
        r"exact\s+string\s+(.+)$",
    ]

    
    REGEX_CACHE = [
                {
                    "id": "email",
                    "aliases": [
                        "email",
                        "email address",
                        "mail",
                        "gmail",
                        "email validation",
                        "gmail validation",
                        "gmail address"
                    ],
                    "regex": {
                        "python": r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
                    },
                    "explanation": "Matches a standard email address."
                },

                {
                    "id": "phone",
                    "aliases": [
                        "phone",
                        "phone number",
                        "mobile",
                        "mobile number",
                        "indian mobile",
                        "indian phone"
                    ],
                    "regex": {
                        "python": r"^(?:\+91[- ]?)?[6-9]\d{9}$"
                    },
                    "explanation": "Matches Indian mobile numbers with optional +91."
                },

                {
                    "id": "date",
                    "aliases": [
                        "date",
                        "dates",
                        "date format",
                        "dd mm yyyy",
                        "dd/mm/yyyy",
                        "yyyy mm dd",
                        "yyyy-mm-dd"
                    ],
                    "regex": {
                        "python": r"^(?:0[1-9]|[12]\d|3[01])[/-](?:0[1-9]|1[0-2])[/-]\d{4}$"
                    },
                    "explanation": "Matches dates in DD/MM/YYYY or DD-MM-YYYY format."
                },

                {
                    "id": "url",
                    "aliases": [
                        "url",
                        "website",
                        "web address",
                        "link",
                        "https",
                        "http"
                    ],
                    "regex": {
                        "python": r"^https?://[^\s/$.?#].[^\s]*$"
                    },
                    "explanation": "Matches HTTP and HTTPS URLs."
                },

                {
                    "id": "ipv4",
                    "aliases": [
                        "ipv4",
                        "ip",
                        "ip address"
                    ],
                    "regex": {
                        "python": r"^(?:(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|1?\d?\d)$"
                    },
                    "explanation": "Matches IPv4 addresses."
                },

                {
                    "id": "uuid",
                    "aliases": [
                        "uuid",
                        "guid"
                    ],
                    "regex": {
                        "python": r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$"
                    },
                    "explanation": "Matches RFC 4122 UUIDs."
                },

                {
                    "id": "pan",
                    "aliases": [
                        "pan",
                        "pan card",
                        "pan number"
                    ],
                    "regex": {
                        "python": r"^[A-Z]{5}[0-9]{4}[A-Z]$"
                    },
                    "explanation": "Matches Indian PAN numbers."
                },

                {
                    "id": "gst",
                    "aliases": [
                        "gst",
                        "gst number",
                        "gstin"
                    ],
                    "regex": {
                        "python": r"^\d{2}[A-Z]{5}\d{4}[A-Z][1-9A-Z]Z[0-9A-Z]$"
                    },
                    "explanation": "Matches Indian GSTIN numbers."
                },

                {
                    "id": "aadhaar",
                    "aliases": [
                        "aadhaar",
                        "aadhaar number",
                        "aadhar"
                    ],
                    "regex": {
                        "python": r"^\d{4}\s?\d{4}\s?\d{4}$"
                    },
                    "explanation": "Matches Indian Aadhaar numbers."
                },

                {
                    "id": "pin_code",
                    "aliases": [
                        "pin code",
                        "postal code",
                        "zip code",
                        "pincode"
                    ],
                    "regex": {
                        "python": r"^[1-9][0-9]{5}$"
                    },
                    "explanation": "Matches Indian PIN codes."
                }
            ]
    
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
                    score = max(score, len(alias))
            
            if score > best_score:
                best_score = score
                best_entry = entry
                
        return best_entry if best_score > 0 else None
    
    @staticmethod
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
            result = json.loads(response.strip())
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
    def _validate_regex(regex: str):
        
        try:
            re.compile(regex)
            return
        except re.error as e:
            raise ValueError(
                f"Error: {e}"
            ) from e
            
    @staticmethod
    def _test_regex(regex: str, test_strings: Optional[List[str]]):
        if not test_strings:
            return None
        
        regex_result = []
        
        test = re.compile(regex)
        for string in test_strings:
            regex_result.append(
                RegexMatchResult(
                    text=string,
                    matched=test.fullmatch(string) is not None
                )
            )
        
        return regex_result
    
    @staticmethod
    def _extract_literal_text(prompt: str) -> str:
        for pattern in Regex.patterns:
            match = re.search(pattern, prompt)
            if match:
                return match.group(1).strip()

        raise ValueError("Unable to extract literal text.")
    
    @staticmethod
    def _generate_literal_regex(word: str, engine:RegexEngine) -> RegexGeneratorResponse:
        
        escaped = re.escape(word)
        
        if " " not in word:
            regex = rf"\b{escaped}\b"
        else:
            regex = escaped
            
        return RegexGeneratorResponse(
            regex=regex,
            explanation=f"Matches the literal text '{word}'.",
            source="literal",
            engine=engine
        )
        
# main function  
    @staticmethod
    def generate_regex(request: RegexGeneratorRequest) -> RegexGeneratorResponse:
        # Validate request
        request = Regex._validate_request(request)

        # Normalize prompt
        prompt = Regex._normalize_prompt(request.prompt)

        # Step 1: Determine response source
        if Regex._detect_literal_intent(prompt):
            literal = Regex._extract_literal_text(prompt)
            response = Regex._generate_literal_regex(
                literal,
                request.engine
            )

        else:
            entry = Regex._search_cache(
                prompt,
                request.engine
            )

            if entry is not None:
                response = RegexGeneratorResponse(
                    regex=entry["regex"][request.engine.value],
                    explanation=entry["explanation"],
                    source="cache",
                    engine=request.engine
                )
            else:
                response = Regex._generate_with_ai(request)

        # Step 2: Validate generated regex
        Regex._validate_regex(
            response.regex
        )

        # Step 3: Test regex (if test strings provided)
        response.matches = Regex._test_regex(
            response.regex,
            request.test_strings
        )

        return response
            