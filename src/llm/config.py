"""
LLM Service Configuration and Management.
Handles OpenAI API setup, retries, and cost tracking.
"""
from typing import Optional, Dict, Any, List
import time
from functools import wraps

from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

from src.utils.config import get_settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class LLMConfig:
    """
    LLM configuration and management singleton.
    Handles model initialization, retry logic, and cost tracking.
    """
    
    _instance: Optional["LLMConfig"] = None
    _llm: Optional[ChatOpenAI] = None
    
    # Token cost tracking (approximate, update based on actual pricing)
    TOKEN_COSTS = {
        "gpt-4-turbo-preview": {"input": 0.01 / 1000, "output": 0.03 / 1000},
        "gpt-4": {"input": 0.03 / 1000, "output": 0.06 / 1000},
        "gpt-3.5-turbo": {"input": 0.0005 / 1000, "output": 0.0015 / 1000},
    }
    
    def __new__(cls) -> "LLMConfig":
        """Ensure only one instance exists (singleton pattern)."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize LLM configuration."""
        if not hasattr(self, '_initialized'):
            self.settings = get_settings()
            self.total_input_tokens = 0
            self.total_output_tokens = 0
            self.total_cost = 0.0
            self._initialized = True
    
    def get_llm(
        self,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        streaming: bool = False
    ) -> ChatOpenAI:
        """
        Get or create an LLM instance.
        
        Args:
            model: Model name (uses config default if None)
            temperature: Temperature setting (uses config default if None)
            max_tokens: Max tokens to generate (no limit if None)
            streaming: Enable streaming responses
            
        Returns:
            Configured ChatOpenAI instance
            
        Example:
            >>> llm_config = LLMConfig()
            >>> llm = llm_config.get_llm(temperature=0.7)
        """
        model = model or self.settings.openai_model
        temperature = temperature if temperature is not None else self.settings.openai_temperature
        
        logger.info(f"Initializing LLM: {model} (temp={temperature}, streaming={streaming})")
        
        try:
            llm = ChatOpenAI(
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                openai_api_key=self.settings.openrouter_api_key, # FOR OPENROUTER USE  openai_api_key -> openrouter_api_key 
                openai_api_base="https://openrouter.ai/api/v1", # FOR OPENROUTER USE THIS BASE URL
                streaming=streaming,
                request_timeout=60,
                max_retries=3
            )
            
            return llm
            
        except Exception as e:
            logger.error(f"Failed to initialize LLM: {e}", exc_info=True)
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(Exception),
        reraise=True
    )
    def invoke_with_retry(
        self,
        messages: List[BaseMessage],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> AIMessage:
        """
        Invoke LLM with automatic retry logic.
        
        Args:
            messages: List of messages to send
            model: Model name (optional)
            temperature: Temperature setting (optional)
            max_tokens: Max tokens to generate (optional)
            
        Returns:
            AI response message
            
        Raises:
            Exception: If all retries fail
        """
        llm = self.get_llm(model=model, temperature=temperature, max_tokens=max_tokens)
        
        start_time = time.time()
        try:
            response = llm.invoke(messages)
            elapsed = time.time() - start_time
            
            # Track tokens and cost
            if hasattr(response, 'response_metadata'):
                usage = response.response_metadata.get('token_usage', {})
                input_tokens = usage.get('prompt_tokens', 0)
                output_tokens = usage.get('completion_tokens', 0)
                
                self.total_input_tokens += input_tokens
                self.total_output_tokens += output_tokens
                
                # Calculate cost
                model_name = model or self.settings.openai_model
                if model_name in self.TOKEN_COSTS:
                    costs = self.TOKEN_COSTS[model_name]
                    cost = (input_tokens * costs['input']) + (output_tokens * costs['output'])
                    self.total_cost += cost
                    
                    logger.debug(
                        f"LLM invocation: {input_tokens} in + {output_tokens} out = ${cost:.4f} "
                        f"(total: ${self.total_cost:.4f}) in {elapsed:.2f}s"
                    )
            
            return response
            
        except Exception as e:
            logger.error(f"LLM invocation failed: {e}", exc_info=True)
            raise
    
    async def ainvoke_with_retry(
        self,
        messages: List[BaseMessage],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> AIMessage:
        """
        Async version of invoke_with_retry.
        
        Args:
            messages: List of messages to send
            model: Model name (optional)
            temperature: Temperature setting (optional)
            max_tokens: Max tokens to generate (optional)
            
        Returns:
            AI response message
        """
        llm = self.get_llm(model=model, temperature=temperature, max_tokens=max_tokens)
        
        start_time = time.time()
        try:
            response = await llm.ainvoke(messages)
            elapsed = time.time() - start_time
            
            # Track tokens and cost (same as sync version)
            if hasattr(response, 'response_metadata'):
                usage = response.response_metadata.get('token_usage', {})
                input_tokens = usage.get('prompt_tokens', 0)
                output_tokens = usage.get('completion_tokens', 0)
                
                self.total_input_tokens += input_tokens
                self.total_output_tokens += output_tokens
                
                model_name = model or self.settings.openai_model
                if model_name in self.TOKEN_COSTS:
                    costs = self.TOKEN_COSTS[model_name]
                    cost = (input_tokens * costs['input']) + (output_tokens * costs['output'])
                    self.total_cost += cost
                    
                    logger.debug(f"LLM async invocation: ${cost:.4f} in {elapsed:.2f}s")
            
            return response
            
        except Exception as e:
            logger.error(f"LLM async invocation failed: {e}", exc_info=True)
            raise
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """
        Get current usage statistics.
        
        Returns:
            Dictionary with token counts and costs
        """
        return {
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_tokens": self.total_input_tokens + self.total_output_tokens,
            "total_cost": round(self.total_cost, 4),
            "average_cost_per_call": (
                round(self.total_cost / max(1, self.total_input_tokens // 1000), 4)
            )
        }
    
    def reset_usage_stats(self) -> None:
        """Reset usage statistics to zero."""
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cost = 0.0
        logger.info("Usage statistics reset")


# Global instance
llm_config = LLMConfig()


def get_llm(
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    streaming: bool = False
) -> ChatOpenAI:
    """
    Get an LLM instance (convenience function).
    
    Args:
        model: Model name
        temperature: Temperature setting
        max_tokens: Max tokens to generate
        streaming: Enable streaming
        
    Returns:
        ChatOpenAI instance
    """
    return llm_config.get_llm(
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        streaming=streaming
    )


def invoke_llm(
    messages: List[BaseMessage],
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None
) -> AIMessage:
    """
    Invoke LLM with retry logic (convenience function).
    
    Args:
        messages: List of messages
        model: Model name
        temperature: Temperature setting
        max_tokens: Max tokens
        
    Returns:
        AI response
    """
    return llm_config.invoke_with_retry(
        messages=messages,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens
    )


async def ainvoke_llm(
    messages: List[BaseMessage],
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None
) -> AIMessage:
    """
    Async invoke LLM with retry logic (convenience function).
    
    Args:
        messages: List of messages
        model: Model name
        temperature: Temperature setting
        max_tokens: Max tokens
        
    Returns:
        AI response
    """
    return await llm_config.ainvoke_with_retry(
        messages=messages,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens
    )