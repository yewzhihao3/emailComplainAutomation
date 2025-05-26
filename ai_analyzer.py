import requests
import json
import logging
import re

class AIAnalyzer:
    def __init__(self, api_key):
        self.api_key = api_key
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://localhost:5000",
            "X-Title": "Complaint Analysis System"
        }
        self.logger = logging.getLogger(__name__)

    def _create_analysis_prompt(self, complaint_text):
        return [
            {"role": "system", "content": """Analyze medical supply complaints. Output in JSON format with two fields:
- root_cause: Clear description of the issue
- suggested_solution: Steps to resolve the issue"""},
            {"role": "user", "content": complaint_text},
            {"role": "assistant", "content": "I will analyze the complaint and provide a response in JSON format with root_cause and suggested_solution."},
            {"role": "user", "content": "Please provide your analysis in JSON format."}
        ]

    def _extract_json_from_text(self, text: str) -> dict:
        """Extract JSON from text content using multiple strategies."""
        # Strategy 1: Find the most promising JSON-like structure
        try:
            # Look for content between the most outer curly braces
            matches = re.findall(r'\{[^{]*"root_cause"[^}]*"suggested_solution"[^}]*\}', text)
            for match in matches:
                try:
                    data = json.loads(match)
                    if isinstance(data, dict) and 'root_cause' in data and 'suggested_solution' in data:
                        return data
                except json.JSONDecodeError:
                    continue

            # Strategy 2: Try to find the largest JSON structure
            matches = re.findall(r'\{[^}]+\}', text)
            for match in sorted(matches, key=len, reverse=True):
                try:
                    data = json.loads(match)
                    if isinstance(data, dict) and 'root_cause' in data and 'suggested_solution' in data:
                        return data
                except json.JSONDecodeError:
                    continue

            # Strategy 3: Extract fields directly
            root_cause_match = re.search(r'"root_cause"\s*:\s*"([^"]*)"', text)
            solution_match = re.search(r'"suggested_solution"\s*:\s*"([^"]*)"', text)
            
            if root_cause_match and solution_match:
                return {
                    "root_cause": root_cause_match.group(1),
                    "suggested_solution": solution_match.group(1)
                }

            raise ValueError("No valid JSON structure found")
            
        except Exception as e:
            self.logger.error(f"JSON extraction error: {str(e)}")
            raise ValueError(f"Failed to extract JSON: {str(e)}")

    def analyze_complaint(self, complaint_text):
        try:
            # Prepare the messages for the API
            messages = self._create_analysis_prompt(complaint_text)

            # Make API request
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json={
                    "model": "deepseek/deepseek-v3-base:free",
                    "messages": messages,
                    "temperature": 0.1,
                    "max_tokens": 500,
                    "top_p": 0.1,
                    "stream": False
                }
            )

            if response.status_code == 200:
                try:
                    api_response = response.json()
                    content = api_response.get('choices', [{}])[0].get('message', {}).get('content', '')
                    
                    try:
                        return self._extract_json_from_text(content)
                    except ValueError:
                        # If JSON extraction fails, try to create a structured response from the content
                        lines = content.split('\n')
                        root_cause = ""
                        solution = ""
                        
                        for line in lines:
                            line = line.strip()
                            if "root cause" in line.lower() or "root_cause" in line.lower():
                                root_cause = line.split(":", 1)[1].strip() if ":" in line else line
                            elif "solution" in line.lower():
                                solution = line.split(":", 1)[1].strip() if ":" in line else line
                        
                        if root_cause and solution:
                            return {
                                "root_cause": root_cause,
                                "suggested_solution": solution
                            }
                        
                        return {
                            "root_cause": "Parsing Error",
                            "suggested_solution": "Could not extract structured data from the AI response. Original response: " + content[:200]
                        }

                except Exception as e:
                    self.logger.error(f"Error processing response: {str(e)}")
                    return {
                        "root_cause": "Processing Error",
                        "suggested_solution": f"Error processing API response: {str(e)}"
                    }
            else:
                error_msg = f"HTTP {response.status_code}"
                try:
                    error_detail = response.json()
                    error_msg = f"{error_msg}: {json.dumps(error_detail)}"
                except:
                    error_msg = f"{error_msg}: {response.text}"
                
                self.logger.error(f"API Error: {error_msg}")
                return {
                    "root_cause": "API Error",
                    "suggested_solution": f"Error calling AI API: {error_msg}"
                }

        except Exception as e:
            self.logger.error(f"System Error: {str(e)}")
            return {
                "root_cause": "System Error",
                "suggested_solution": f"Error processing complaint: {str(e)}"
            } 