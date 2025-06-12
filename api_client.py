import asyncio
import logging
import time
from typing import Dict, List, Optional, Union, Any
import openai
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("APIClient")

class APIClientError(Exception):
    """Base exception class for APIClient errors"""
    pass

class APIClient:
    """
    Client for interacting with OpenAI-compatible APIs.
    
    Features:
    - Configurable base URL, API key, and model
    - Methods for listing models and calling chat completions
    - Robust error handling with detailed error messages
    - Automatic retries with exponential backoff
    - Comprehensive logging
    - Async support for non-blocking operations
    """
    
    def __init__(
        self, 
        base_url: str = "https://192.168.58.111:8123/v1", 
        api_key: str = "", 
        model: str = "claude-3-5-sonnet",
        max_retries: int = 10,
        timeout: float = 60.0
    ):
        """
        Initialize the API client.
        
        Args:
            base_url: Base URL of the API (default: OpenAI's API)
            api_key: API key for authentication
            model: Default model to use for completions
            max_retries: Maximum number of retries for failed requests
            timeout: Timeout for operations in seconds
        """
        self.base_url = base_url
        self.api_key = api_key
        self.model = model
        self.max_retries = max_retries
        self.timeout = timeout
        self._client = None
        
        # Initialize the client
        self._initialize_client()
        
        logger.info(f"Initialized APIClient with base URL: {base_url}")
    
    def _initialize_client(self):
        """Initialize the OpenAI client with current settings"""
        self._client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=self.timeout,
            max_retries=self.max_retries
        )
    
    async def close(self):
        """Close the API client session"""
        # The AsyncOpenAI client handles session cleanup automatically
        # but we'll set it to None to be explicit
        self._client = None
        logger.info("Closed API client session")
    
    def set_base_url(self, base_url: str):
        """Set the base URL for the API"""
        self.base_url = base_url
        self._initialize_client()
        logger.info(f"Set base URL to: {base_url}")
    
    def set_api_key(self, api_key: str):
        """Set the API key for authentication"""
        self.api_key = api_key
        self._initialize_client()
        logger.info("Updated API key")
    
    def set_model(self, model: str):
        """Set the default model for completions"""
        self.model = model
        logger.info(f"Set default model to: {model}")
    
    async def list_models(self) -> List[Dict[str, Any]]:
        """
        Get a list of available models from the API.
        
        Returns:
            List of model objects with their properties
            
        Raises:
            APIClientError: If the request fails
        """
        try:
            logger.info("Fetching available models")
            response = await self._client.models.list()
            models = response.data
            logger.info(f"Retrieved {len(models)} models")
            return [model.model_dump() for model in models]
        except openai.OpenAIError as e:
            error_msg = f"Error listing models: {str(e)}"
            logger.error(error_msg)
            raise APIClientError(error_msg) from e
        except Exception as e:
            error_msg = f"Unexpected error listing models: {str(e)}"
            logger.error(error_msg)
            raise APIClientError(error_msg) from e
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        frequency_penalty: Optional[float] = None,
        presence_penalty: Optional[float] = None,
        stop: Optional[Union[str, List[str]]] = None,
        stream: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create a chat completion using the API.
        
        Args:
            messages: List of message objects with role and content
            model: Model to use (defaults to self.model if not provided)
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum number of tokens to generate
            top_p: Nucleus sampling parameter
            frequency_penalty: Frequency penalty parameter
            presence_penalty: Presence penalty parameter
            stop: Stop sequences
            stream: Whether to stream the response
            **kwargs: Additional parameters to pass to the API
            
        Returns:
            Chat completion response
            
        Raises:
            APIClientError: If the request fails
        """
        try:
            model_to_use = model or self.model
            logger.info(f"Creating chat completion with model: {model_to_use}")
            
            # Prepare parameters, filtering out None values
            params = {
                "model": model_to_use,
                "messages": messages,
                "temperature": temperature,
                "stream": stream,
                **{k: v for k, v in {
                    "max_tokens": max_tokens,
                    "top_p": top_p,
                    "frequency_penalty": frequency_penalty,
                    "presence_penalty": presence_penalty,
                    "stop": stop,
                    **kwargs
                }.items() if v is not None}
            }
            
            # Handle streaming responses
            if stream:
                logger.info("Streaming mode requested")
                stream_resp = await self._client.chat.completions.create(**params)
                # In a real implementation, you would process the stream
                # For now, we'll just return a placeholder
                return {"choices": [{"message": {"content": "Streaming response placeholder"}}]}
            
            # Handle regular responses
            response = await self._client.chat.completions.create(**params)
            
            logger.info("Chat completion successful")
            # Convert to dict for consistent return type
            return response.model_dump()
            
        except openai.OpenAIError as e:
            error_msg = f"OpenAI API error in chat completion: {str(e)}"
            logger.error(error_msg)
            raise APIClientError(error_msg) from e
        except Exception as e:
            error_msg = f"Unexpected error in chat completion: {str(e)}"
            logger.error(error_msg)
            raise APIClientError(error_msg) from e