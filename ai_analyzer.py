import requests
import json
import logging
import re
import time

class AIAnalyzer:
    def __init__(self, api_key):
        self.api_key = api_key
        self.api_url = "https://api.deepseek.com/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        self.logger = logging.getLogger(__name__)
        self.max_retries = 3
        self.retry_delay = 2  # seconds

    def _create_analysis_prompt(self, complaint_text, error_message=None):
        messages = [
            {"role": "system", "content": """You are a complaint analysis expert. Your task is to analyze the complaint and respond with EXACTLY 3 numbered points for both root causes and solutions.

REQUIRED FORMAT:
{
  "root_cause": [
    "1. [First root cause]",
    "2. [Second root cause]",
    "3. [Third root cause]"
  ],
  "suggested_solution": [
    "1. [First solution]",
    "2. [Second solution]",
    "3. [Third solution]"
  ]
}

IMPORTANT:
- Each point must be concise (under 25 words)
- Always provide exactly 3 points for each section
- Keep points clear and relevant to the complaint
- Do not add any explanations or extra text
- Maintain the exact JSON structure shown above"""},
            {"role": "user", "content": f"Analyze this complaint and respond with ONLY the JSON object containing root causes and solutions:\n\n{complaint_text}"}
        ]

        # If there was an error in the previous attempt, add a message about it
        if error_message:
            messages.append({"role": "user", "content": f"Your response was incorrect. {error_message}. You MUST respond with EXACTLY the JSON object containing 3 numbered points for each section."})
        
        # Log the complete prompt for debugging
        self.logger.info("=== AI Prompt ===")
        self.logger.info("System Message:")
        self.logger.info(messages[0]["content"])
        self.logger.info("\nUser Messages:")
        for msg in messages[1:]:
            if msg["role"] == "user":
                self.logger.info(msg["content"])
        self.logger.info("===============")
        
        return messages

    def _extract_json_from_text(self, text: str) -> dict:
        """Extract analysis from text content."""
        try:
            # First, check if the response is empty or too short
            if not text or len(text.strip()) < 20:
                return {
                    "root_cause": ["1. Error: Empty response", "2. Please try again", "3. System error"],
                    "suggested_solution": ["1. Retry analysis", "2. Check input", "3. Contact support"],
                    "error": "Empty response"
                }

            # Try to parse the JSON directly first
            try:
                # Find JSON-like structure in the text
                json_match = re.search(r'\{[\s\S]*\}', text)
                if json_match:
                    parsed_json = json.loads(json_match.group(0))
                    if isinstance(parsed_json, dict) and "root_cause" in parsed_json and "suggested_solution" in parsed_json:
                        root_causes = parsed_json["root_cause"]
                        solutions = parsed_json["suggested_solution"]
                        
                        # Validate the structure
                        if (isinstance(root_causes, list) and isinstance(solutions, list) and
                            len(root_causes) == 3 and len(solutions) == 3):
                            return parsed_json
            except:
                pass

            # If JSON parsing fails, try to extract the points manually
            root_causes = []
            solutions = []
            
            # Extract root causes
            root_cause_matches = re.finditer(r'(?:1|2|3)\.\s*(.*?)(?=(?:1|2|3)\.|$)', text, re.DOTALL)
            for match in root_cause_matches:
                if len(root_causes) < 3:
                    point = match.group(1).strip()
                    if point and len(point) < 100:  # Reasonable length check
                        root_causes.append(f"{len(root_causes) + 1}. {point}")

            # Extract solutions
            solution_matches = re.finditer(r'(?:1|2|3)\.\s*(.*?)(?=(?:1|2|3)\.|$)', text, re.DOTALL)
            for match in solution_matches:
                if len(solutions) < 3:
                    point = match.group(1).strip()
                    if point and len(point) < 100:  # Reasonable length check
                        solutions.append(f"{len(solutions) + 1}. {point}")

            # Ensure we have exactly 3 points for each
            while len(root_causes) < 3:
                root_causes.append(f"{len(root_causes) + 1}. Analysis incomplete")
            while len(solutions) < 3:
                solutions.append(f"{len(solutions) + 1}. Solution pending")

            return {
                "root_cause": root_causes,
                "suggested_solution": solutions
            }

        except Exception as e:
            self.logger.error(f"Text extraction error: {str(e)}")
            return {
                "root_cause": ["1. Error in analysis", "2. System error", "3. Processing failed"],
                "suggested_solution": ["1. Retry analysis", "2. Check input", "3. Contact support"],
                "error": str(e)
            }

    def analyze_complaint(self, complaint_text):
        """Analyze a complaint and return structured analysis."""
        if not complaint_text or len(complaint_text.strip()) == 0:
            return {
                "root_cause": "Empty complaint",
                "suggested_solution": "No content to analyze",
                "importance_level": "Medium"
            }

        retry_count = 0
        last_error = None

        while retry_count < self.max_retries:
            try:
                # Make API request
                response = requests.post(
                    self.api_url,
                    headers=self.headers,
                    json={
                        "model": "deepseek-chat",
                        "messages": self._create_analysis_prompt(complaint_text, last_error),
                        "temperature": 0.4,
                        "max_tokens": 500,
                        "top_p": 0.1,
                        "stream": False
                    }
                )

                if response.status_code == 200:
                    try:
                        api_response = response.json()
                        content = api_response.get('choices', [{}])[0].get('message', {}).get('content', '')
                        
                        if not content:
                            last_error = "Empty response from AI"
                            retry_count += 1
                            time.sleep(self.retry_delay)
                            continue

                        # Log the raw response for debugging
                        self.logger.info("=== AI Response ===")
                        self.logger.info(content)
                        self.logger.info("=================")
                        
                        result = self._extract_json_from_text(content)
                        
                        # If we got a proper analysis without errors, return it
                        if "error" not in result:
                            return result
                        
                        # Otherwise, prepare for retry
                        last_error = result.get("error", "Unknown error")
                        retry_count += 1
                        time.sleep(self.retry_delay)
                        continue

                    except Exception as e:
                        last_error = f"Error processing response: {str(e)}"
                        retry_count += 1
                        time.sleep(self.retry_delay)
                        continue
                else:
                    error_msg = f"HTTP {response.status_code}"
                    try:
                        error_detail = response.json()
                        error_msg = f"{error_msg}: {json.dumps(error_detail)}"
                    except:
                        error_msg = f"{error_msg}: {response.text}"
                    
                    last_error = f"API Error: {error_msg}"
                    retry_count += 1
                    time.sleep(self.retry_delay)
                    continue

            except Exception as e:
                last_error = f"System Error: {str(e)}"
                retry_count += 1
                time.sleep(self.retry_delay)
                continue

        # If we've exhausted all retries, return the last error
        return {
            "root_cause": f"Failed after {self.max_retries} attempts",
            "suggested_solution": f"Last error: {last_error}",
            "importance_level": "Medium"
        } 