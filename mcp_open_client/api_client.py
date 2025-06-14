import asyncio
import logging
from typing import Dict, List, Optional, Union, Any
import openai
from openai import AsyncOpenAI

# Configure logging with less verbosity
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Reduce verbosity of external libraries
logging.getLogger("openai").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("openai._base_client").setLevel(logging.WARNING)

logger = logging.getLogger("APIClient")

class APIClientError(Exception):
    pass

class APIClient:
    def __init__(
        self, 
        base_url: str = "http://192.168.58.101:8123",
        api_key: str = "sisas", 
        model: str = "claude-3-5-sonnet",
        max_retries: int = 10,
        timeout: float = 60.0
    ):
        self.base_url = base_url
        self.api_key = api_key
        self.model = model
        self.max_retries = max_retries
        self.timeout = timeout
        self._client = None
        self._initialize_client()
        logger.info(f"Initialized APIClient with base URL: {base_url}")

    def _initialize_client(self):
        self._client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=self.timeout,
            max_retries=self.max_retries
        )
        # Removed debug log for cleaner output

    async def list_models(self) -> List[Dict[str, Any]]:
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

    async def close(self):
        # AsyncOpenAI doesn't have a close method, but we'll keep this for consistency
        logger.info("Closing APIClient")
        self._client = None

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