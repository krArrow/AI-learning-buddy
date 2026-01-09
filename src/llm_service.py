"""
LLM Service - Abstraction for all LLM calls
Uses OpenAI API (industry standard for GenAI applications)
"""

import os
from typing import Optional
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class LLMService:
    """
    Handles all interactions with the LLM.
    Keeps API details isolated from business logic.
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        """
        Initialize LLM service
        
        Args:
            api_key: OpenAI API key (if None, reads from OPENAI_API_KEY env var)
            model: Model to use (default: gpt-4o-mini for cost efficiency)
        """
        #using openrouter api key to access gpt-4o-mini

        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        # print("API KEY : ",self.api_key)
        if not self.api_key:
            raise ValueError(
                "OpenAI API key not found. Set OPENAI_API_KEY environment variable "
                "or pass api_key parameter."
            )
        
        self.client = OpenAI(
                        api_key=self.api_key)
                        # base_url="https://openrouter.ai/api/v1")
        self.model = model
    
    def generate(self, prompt: str, temperature: float = 0.7, max_tokens: int = 2000) -> str:
        """
        Generate a response from the LLM
        
        Args:
            prompt: The prompt to send
            temperature: Creativity (0=deterministic, 1=creative)
            max_tokens: Maximum response length
            
        Returns:
            Generated text response
            
        Raises:
            Exception: If API call fails
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert learning advisor helping people achieve their learning goals through structured, personalized plans."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return response.choices[0].message.content.strip()
        
        except Exception as e:
            raise Exception(f"LLM generation failed: {str(e)}")
    
    def generate_roadmap(self, prompt: str) -> str:
        """Generate learning roadmap (Prompt 1)"""
        # Lower temperature for more structured output
        return self.generate(prompt, temperature=0.5, max_tokens=1500)
    
    def generate_tasks(self, prompt: str) -> str:
        """Generate daily tasks (Prompt 2)"""
        return self.generate(prompt, temperature=0.6, max_tokens=1500)
    
    def adapt_tasks(self, prompt: str) -> str:
        """Adapt tasks based on progress (Prompt 3)"""
        return self.generate(prompt, temperature=0.7, max_tokens=1500)


# Singleton instance (optional pattern for simple apps)
_llm_service = None

def get_llm_service(api_key: Optional[str] = None) -> LLMService:
    """Get or create LLM service instance"""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService(api_key=api_key)
    return _llm_service


clss = LLMService()