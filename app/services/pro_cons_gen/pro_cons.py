from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.services.tool_executor import ExecutionService
from app.services.gemini_service import GeminiService
from app.models.pro_cons import ProConsRequest, AnalysisDepth, ProConsResponse
import re, json
from pydantic import ValidationError
import unicodedata

class ProConsService:
    MIN_TOPIC_LENGTH = 3
    MAX_TOPIC_LENGTH = 200
    MAX_CONTEXT_LENGTH = 5000
    
    INVISIBLE_PATTERN = re.compile(
        r'[\u200B\u200C\u200D\u2060\uFEFF]'
    )
    
    @staticmethod
    async def _generate_analysis(request: ProConsRequest, user=None) -> ProConsResponse:
        cleaned_req = ProConsService._preprocess_input(request)
        prompt = ProConsService._prompt_builder(cleaned_req)
        final_prompt = (
            f"{prompt['system_prompt']}\n\n"
            f"{prompt['user_prompt']}"
        )
        raw_res = ProConsService._generate_points(final_prompt)
        parsed_res = ProConsService._parse_response(raw_res)
        parsed_res["pros"] = [
            {**p, "impact": p.get("impact", "medium").lower()} 
            for p in parsed_res.get("pros", [])
        ]
        parsed_res["cons"] = [
            {**c, "impact": c.get("impact", "medium").lower()} 
            for c in parsed_res.get("cons", [])
        ]
        parsed_res["topic"] = cleaned_req.topic          # ← add this
        parsed_res["generated_at"] = datetime.now(timezone.utc).isoformat()
        final = ProConsService._validate_response(parsed_res)
        
        return final
        
    
    @staticmethod
    def _preprocess_input(request: ProConsRequest) -> ProConsRequest:
        """
        Clean and normalize user input before prompt construction.
        """

        topic = ProConsService._clean_text(request.topic)

        context = (
            ProConsService._clean_text(request.context)
            if request.context
            else None
        )

        if len(topic) > ProConsService.MAX_TOPIC_LENGTH:
            raise ValueError(
                f"Topic exceeds maximum length ({ProConsService.MAX_TOPIC_LENGTH} characters)."
            )

        if context and len(context) > ProConsService.MAX_CONTEXT_LENGTH:
            raise ValueError(
                f"Context exceeds maximum length ({ProConsService.MAX_CONTEXT_LENGTH} characters)."
            )

        return ProConsRequest(
            topic=topic,
            context=context,
            analysis_depth=request.analysis_depth,
        )

    @staticmethod
    def _clean_text(text: str) -> str:
        """
        Perform text normalization.
        """

        if not text:
            return ""

        # Normalize unicode characters
        text = unicodedata.normalize("NFKC", text)

        # Remove invisible/control characters except newline & tab
        text = "".join(
            ch
            for ch in text
            if ch == "\n"
            or ch == "\t"
            or unicodedata.category(ch)[0] != "C"
        )

        # Normalize line endings
        text = text.replace("\r\n", "\n").replace("\r", "\n")

        # Trim each line
        lines = [line.strip() for line in text.split("\n")]

        # Remove repeated blank lines
        cleaned_lines = []
        previous_blank = False

        for line in lines:
            if line == "":
                if previous_blank:
                    continue
                previous_blank = True
            else:
                previous_blank = False

            cleaned_lines.append(line)

        text = "\n".join(cleaned_lines)

        # Normalize multiple spaces and tabs
        text = re.sub(r"[ \t]+", " ", text)

        # Final trim
        return text.strip()
    
    @staticmethod
    def _prompt_builder(request: ProConsRequest): 
        
        system_prompt = """
        You are an expert decision analysis assistant specializing in generating balanced, objective, and well-structured pros and cons for decisions, products, technologies, business ideas, and comparisons.
        
        Your task is to objectively analyze the user's topic and generate a balanced pros and cons.
        
        Quality Rules:
        - Avoid duplicate points.
        - Keep titles concise.
        - Make descriptions meaningful.
        - Ensure every point is unique.
        - Consider practical, financial, technical, usability and long-term aspects when applicable.
        
        risk_level:
        - Must be exactly one of:
        - "low"
        - "medium"
        - "high"

        Do not use values such as:
        "very high", "extremely high", "minimal", "moderate", etc.
        
        Guidelines:
        - Be unbiased.
        - Consider both short-term and long-term effects.
        - Use the provided context if available.
        - Match the requested analysis depth.
        - Do not invent facts.
        - If the topic lacks sufficient information, make reasonable assumptions instead of refusing.
        - Generate an equal number of pros and cons.
        - Do not wrap the JSON inside markdown code blocks.
        - Do not include explanations before or after the JSON.
        - Return ONLY valid JSON.
        - You MUST strictly follow the point count specified in the user's instructions. Never generate fewer pros or cons than requested.
        """.strip()
        
        user_prompt = f"""
        Topic:
        {request.topic}
        
        Analysis Depth: 
        {request.analysis_depth}
        """
        
        if request.context:
            user_prompt += f"""
            Additional Context: 
            {request.context}
            """
            
        # Determine count instruction BEFORE building the generation block
        if request.analysis_depth == AnalysisDepth.QUICK:
            depth_instruction = "Generate exactly 4-5 pros and exactly 4-5 cons. Keep each description concise (1-2 sentences)."
        elif request.analysis_depth == AnalysisDepth.DETAILED:
            depth_instruction = "Generate exactly 10-12 pros and exactly 10-12 cons. Provide detailed reasoning for each (2-4 sentences)."
        else:  # BALANCED is the default
            depth_instruction = "Generate exactly 6-8 pros and exactly 6-8 cons with moderate explanations (2-3 sentences each)."

        user_prompt += f"""
        IMPORTANT — Point Count Rule: {depth_instruction}
        You MUST follow the count above strictly. Do not generate fewer points than specified.

        Generate:
        - Balanced Pros
        - Balanced Cons
        - Overall Summary
        - Final Recommendation

        Return only this valid JSON object with the following fields:
        - summary (string)
        - pros (array)
            - title
            - description
            - impact ("high", "medium", "low" only. Dont use values such as "very high", "extremely high", "minimal", "moderate", etc.)
        - cons (array)
            - title
            - description
            - impact ("high", "medium", "low")
        - recommendation
            - summary
            - recommendation
            - verdict
            - risk_level
            - confidence_score(integer only between 0 to 100. DO not include 'percent' or '%')
        """
        return {
            "system_prompt": system_prompt,
            "user_prompt": user_prompt
        }
        
        
    @staticmethod
    def _generate_points(prompt: str):
        
        try:
            client = GeminiService()
            response = client.generate(prompt)
            return response
        except Exception as e:
            raise RuntimeError(f"Failed to generate Pro Cons: {e}")
        
    @staticmethod
    def _parse_response(response: str):
        
        response = response.strip()
        if response.startswith("```"):
            response = response.replace("```json", "")
            response = response.replace("```", "")
            response = response.strip()
            
        try:
            data = json.loads(response)
        except json.JSONDecodeError as e:
            raise RuntimeError(
            f"Invalid JSON returned by AI: {e}"
        ) from e
        
        return data
    
    @staticmethod
    def _validate_response(data: dict) -> ProConsResponse:
        try:
            return ProConsResponse.model_validate(data)
        except ValidationError as e:
            raise RuntimeError(
            f"AI response validation failed:\n{e}"
        ) from e