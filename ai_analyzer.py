import requests
import json
import logging

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

    def analyze_complaint(self, complaint_text):
        try:
            # Prepare the messages for the API
            messages = [
                {
                    "role": "system",
                    "content": "Analyze medical supply complaints. Output in JSON format with two fields:\n- root_cause: Clear description of the issue\n- suggested_solution: Steps to resolve the issue"
                },
                {
                    "role": "user",
                    "content": complaint_text
                }
            ]

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
                    
                    # Try to extract JSON from the content
                    try:
                        # Find JSON-like content between curly braces
                        json_start = content.find('{')
                        json_end = content.rfind('}') + 1
                        
                        if json_start != -1 and json_end != -1:
                            json_content = content[json_start:json_end]
                            analysis = json.loads(json_content)
                        else:
                            # If no JSON found, create a structured response
                            return {
                                "root_cause": "Invalid Response Format",
                                "suggested_solution": "The AI response did not contain valid JSON. Please try again."
                            }

                    except json.JSONDecodeError:
                        # If JSON parsing fails, create a structured error response
                        self.logger.error(f"Failed to parse JSON from content: {content}")
                        return {
                            "root_cause": "JSON Parsing Error",
                            "suggested_solution": "Failed to parse the AI response as JSON. Please try again."
                        }

                    # Validate the response has required fields
                    if not isinstance(analysis, dict) or 'root_cause' not in analysis or 'suggested_solution' not in analysis:
                        return {
                            "root_cause": "Invalid Response Structure",
                            "suggested_solution": f"Response missing required fields. Got: {str(analysis)[:200]}"
                        }

                    return analysis

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