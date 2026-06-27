"""Infrastructure adapter for LLM API integration.

This module provides a concrete HTTP client that communicates with the EvoMap
API Gateway. It adheres to the use case LLMClientProtocol without using any
third-party libraries like `requests` or provider-specific SDKs.
"""

import json
import urllib.error
import urllib.request
from typing import Optional


class EvoMapClient:
    """HTTP client for the EvoMap API Gateway."""

    API_URL = "https://api.evomap.ai/v1/chat/completions"
    MODEL = "evomap-gemini-3.1-pro-preview"

    def __init__(self, api_key: str) -> None:
        """Initialize the client.
        
        Args:
            api_key: The developer's EvoMap API key.
        """
        self.api_key = api_key.strip()

    def generate_completion(self, system_prompt: str, user_prompt: str) -> str:
        """Send a prompt to the EvoMap LLM and return the textual response.
        
        Uses the standard library `urllib` to ensure zero external dependencies.
        Wraps network interactions in robust error handling to prevent stack
        traces from leaking to the CLI user.
        """
        payload = {
            "model": self.MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            # Use a slightly lower temperature for technical documentation
            "temperature": 0.2,
        }
        
        data = json.dumps(payload).encode("utf-8")
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        
        req = urllib.request.Request(
            url=self.API_URL, 
            data=data, 
            headers=headers, 
            method="POST"
        )

        try:
            with urllib.request.urlopen(req, timeout=60.0) as response:
                response_body = response.read().decode("utf-8")
                response_data = json.loads(response_body)
                
                # Assumes OpenAI-compatible response schema
                return response_data["choices"][0]["message"]["content"]
                
        except urllib.error.HTTPError as e:
            if e.code == 401:
                return "> **Error:** Unauthorized. Please check your EvoMap API key."
            elif e.code == 429:
                return "> **Error:** Rate limit exceeded. Please try again later."
            else:
                return f"> **API Error:** Received status code {e.code} from EvoMap."
                
        except urllib.error.URLError as e:
            return f"> **Network Error:** Failed to reach EvoMap API. ({e.reason})"
            
        except TimeoutError:
            return "> **Timeout Error:** The request to EvoMap took too long."
            
        except (KeyError, json.JSONDecodeError):
            return "> **Parsing Error:** Received an unexpected response format from EvoMap."