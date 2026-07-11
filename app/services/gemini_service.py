import os
import re
from dotenv import load_dotenv
from google import genai
from google.genai import types
import json
import config
from config import GEMINI_MODEL

class GeminiService:
    """
    Service responsible for communicating with the Google Gemini API.

    Falls back to a lightweight local summarizer when no GEMINI_API_KEY is configured,
    allowing end-to-end tests to run locally without external API access.
    """

    def __init__(self):
        api_key = config.GEMINI_API_KEY

        if api_key:
            self.client = genai.Client(api_key=api_key)
            self._use_mock = False
        else:
            self.client = None
            self._use_mock = True

    def generate(self, prompt: str) -> str:
        """
        Generate a response from Gemini or a local fallback.
        """
        if self._use_mock:
            # Extract only the source text from between the delimiters
            # that PromptEngine always wraps it in:
            #   Source Text:\n--------------------\n<text>\n--------------------
            match = re.search(
                r'Source Text:\s*-{10,}\s*(.*?)\s*-{10,}',
                prompt,
                re.DOTALL,
            )
            if match:
                source = match.group(1).strip()
            else:
                # Fallback: use the last non-empty block of the prompt
                # (avoids returning instruction lines)
                blocks = [b.strip() for b in prompt.split('\n\n') if b.strip()]
                source = blocks[-1] if blocks else prompt.strip()

            sentences = re.split(r'(?<=[.!?])\s+', source)
            if len(sentences) <= 3:
                return ' '.join(sentences).strip()
            return ' '.join(sentences[:3]).strip()

        try:
            response = self.client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
            )
            return response.text.strip()

        except Exception as e:
            raise RuntimeError(f"Gemini API Error: {str(e)}")
          
    async def generate_code_review(self, batch, local_report, dependency_graph):
        """
        Generic Gemini generation.
        Used by Code Reviewer, SQL Generator,
        Regex Generator, Unit Test Generator, etc.
        """
        if self._use_mock:
          return {
              "model": "mock",
              "batch_files": batch["files"],
              "review": {}
          }
        def filter_local_report(local_report, batch_files):

          filtered = {}

          batch_files = set(batch_files)

          for key, value in local_report.items():

              if isinstance(value, list):

                  filtered[key] = []

                  for item in value:

                      files = {
                          item.get("file"),
                          item.get("file1"),
                          item.get("file2"),
                          item.get("filename"),
                      }

                      files.discard(None)

                      if files & batch_files:
                          filtered[key].append(item)

              elif isinstance(value, dict):

                  filename = value.get("filename")

                  if filename is None or filename in batch_files:
                      filtered[key] = value

              else:
                  filtered[key] = value

          return filtered
        
        filtered_local_report = filter_local_report(
            local_report,
            batch["files"]
        )

        filtered_dependency_graph = {
            file: dependency_graph.get(file, [])
            for file in batch["files"]
        }
        
        system_prompt = """
You are a senior software engineer reviewing part of a software project.

Input:
- Code chunks
- Dependency graph
- Local static analysis

The local analysis is already complete and should be treated as the source of truth.

Do NOT repeat:
- Syntax errors
- Security findings
- Duplicate code findings
- Complexity analysis
- Dependency analysis
- File statistics
- Project structure analysis

Analyze only the supplied code.

Focus only on:
1. Logic bugs
2. Performance issues
3. Readability and maintainability
4. Best practice violations
5. Refactoring opportunities
6. Unit test suggestions


Rules:
- Explain each issue in maximum 5-10 words STRICTLY..
- Provide exactly one actionable suggestion for each issue.
- Do not repeat similar findings.
- If no issue exists for a category, return an empty array.
- Do not include markdown.
- Return only valid JSON.

Return a JSON object with these keys:

{
 
  "logic_bugs": [
    {
      "file": "",
      "line": '',
      "severity": "",
      "issue": "",
      "suggestion": ""
    }
  ],

  "performance": [
    {
      "file": "",
      "line": '',
      "severity": "",
      "issue": "",
      "suggestion": ""
    }
  ],

  "readability": [],
  "best_practices": [],
  "refactoring": [],
  "unit_tests": []

}

Maximum findings:

Logic Bugs: 5
Performance: 5
Readability: 5
Best Practices: 5
Refactoring: 5
Unit Tests: 5

Give the top and most critical findings so that i should not exceed the maximum findings limit
"""

        '''
        Here We will not send full project or full source code to AI, as it will massively
        increase the API cost. What we will do is first we will filter the important files
        from the project based on the score calculated. The score is calculated based on
        various factors like dependency grpah, functions, etc.
        Then from the filtered_files Eg: [main.py, api.py, auth.py]
        We will modified the code to functions and classes. That means each file is 
        combination of functions and classes
        Eg auth.py -> login() + create_token()
        It will remove uncessary lines 
        Then we will not send every files to AI, we will create batches from filtered files
        Each batch will consist of 2-3 files(for eg)
        
        Gemini will recieve only system prompt, current batch[from batches], filtered 
        local report and dependecy graph, instead of whole project. It will reduce API
        cost massively
        
        Then we will merge the response of all batches into one response and return it to 
        frontend....
        '''
        ai_chunks = [
            {
                "file": chunk["file"],
                "code": chunk["code"]
            }
            for chunk in batch["chunks"]
        ]

        ai_dependencies = filtered_dependency_graph

        ai_report = {}

        for section, findings in filtered_local_report.items():

            if not findings:
                continue

            if isinstance(findings, list):

                ai_report[section] = []

                for item in findings:

                    summary = {}

                    for key in (
                        "file",
                        "filename",
                        "severity",
                        "title",
                        "issue",
                        "line",
                    ):
                        if key in item:
                            summary[key] = item[key]

                    if summary:
                        ai_report[section].append(summary)

            else:
              if findings:
                  ai_report[section] = findings
                  
        ai_report = {
            key: value
            for key, value in ai_report.items()
            if value
        }
                
        prompt = json.dumps(
              {
                  "code": ai_chunks,
                  "dependencies": ai_dependencies,
                  "local_analysis": ai_report,
              },
              ensure_ascii=False,
              separators=(",",":")
          )
        
        try:
            response = await self.client.aio.models.generate_content(
                model=GEMINI_MODEL,
                contents=[system_prompt, prompt],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.2,
                    max_output_tokens=10000
                )
            )
            text = response.text.strip()

            print("\n========== GEMINI RESPONSE ==========")
            print(text)
            print("=====================================\n")

            if text.startswith("```"):
                text = (
                    text.replace("```json", "")
                        .replace("```", "")
                        .strip()
                )

            try:
                review = json.loads(text)
            except json.JSONDecodeError as e:
                raise RuntimeError(
                    f"Gemini returned invalid JSON:\n{text}"
                ) from e

            return {
                "model": config.GEMINI_MODEL,
                "batch_files": batch["files"],
                "review": review,
            }

        except Exception as e:
            raise RuntimeError(f"Gemini api error: {e}")