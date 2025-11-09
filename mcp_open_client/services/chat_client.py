"""
Chat client for communicating with LLM providers for completions
"""
import asyncio
import logging
from typing import List, Dict, Any, Optional
import aiohttp
from mcp_open_client.config import config_manager

logger = logging.getLogger(__name__)

class ChatClient:
    """Client for sending chat completion requests to LLM providers"""

    def __init__(self):
        self.session = None

    async def __aenter__(self):
        """Async context manager entry"""
        if not self.session:
            self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
            self.session = None

    async def create_completion(
        self,
        provider_id: str,
        model: str,
        messages: List[Dict[str, str]],
        api_key: str,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        stream: bool = False
    ) -> Optional[str]:
        """Create chat completion using provider API"""

        provider = config_manager.get_provider(provider_id)
        if not provider:
            logger.error(f"Provider {provider_id} not found")
            return None

        base_url = provider.get("base_url", "")

        try:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }

            # Prepare OpenAI-compatible request payload
            payload = {
                "model": model,
                "messages": [
                    {"role": msg["role"], "content": msg["content"]}
                    for msg in messages
                ],
                "max_tokens": max_tokens,
                "temperature": temperature,
                "stream": stream
            }

            logger.info(f"🚀 Chat request to: {base_url}/chat/completions")
            logger.info(f"📝 Model: {model}, Messages: {len(messages)}")

            async with self.session.post(
                f"{base_url}/chat/completions",
                headers=headers,
                json=payload
            ) as response:
                logger.info(f"📡 Response status: {response.status}")

                if response.status == 200:
                    data = await response.json()

                    # Extract response text from OpenAI-compatible format
                    if "choices" in data and len(data["choices"]) > 0:
                        choice = data["choices"][0]
                        if "message" in choice:
                            message = choice["message"]
                            # Try different content fields (content, reasoning, text)
                            response_text = (
                                message.get("content") or
                                message.get("reasoning") or
                                message.get("text") or
                                str(message)  # fallback to full message as string
                            )
                            if response_text:
                                logger.info(f"✅ Response received: {len(response_text)} chars")
                                return response_text

                    logger.warning(f"Unexpected response format from provider. Data: {data}")
                    return None
                else:
                    error_text = await response.text()
                    logger.error(f"Chat API error {response.status}: {error_text}")
                    return None

        except Exception as e:
            logger.error(f"Failed to create completion for {provider_id}: {e}")
            return None

    async def create_streaming_completion(
        self,
        provider_id: str,
        model: str,
        messages: List[Dict[str, str]],
        api_key: str,
        max_tokens: int = 1000,
        temperature: float = 0.7
    ):
        """Create streaming chat completion using provider API"""
        import json

        provider = config_manager.get_provider(provider_id)
        if not provider:
            logger.error(f"Provider {provider_id} not found")
            return

        base_url = provider.get("base_url", "")

        try:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }

            # Prepare OpenAI-compatible request payload with streaming
            payload = {
                "model": model,
                "messages": [
                    {"role": msg["role"], "content": msg["content"]}
                    for msg in messages
                ],
                "max_tokens": max_tokens,
                "temperature": temperature,
                "stream": True
            }

            logger.info(f"🚀 Streaming chat request to: {base_url}/chat/completions")

            async with self.session.post(
                f"{base_url}/chat/completions",
                headers=headers,
                json=payload
            ) as response:
                logger.info(f"📡 Streaming response status: {response.status}")

                if response.status == 200:
                    async for line in response.content:
                        line = line.decode('utf-8').strip()

                        # Skip empty lines and comments
                        if not line or line.startswith(':'):
                            continue

                        # Parse SSE format
                        if line.startswith('data: '):
                            data_str = line[6:]  # Remove 'data: ' prefix

                            # Check for end of stream
                            if data_str == '[DONE]':
                                break

                            try:
                                data = json.loads(data_str)

                                # Extract delta content and reasoning separately
                                if "choices" in data and len(data["choices"]) > 0:
                                    choice = data["choices"][0]
                                    if "delta" in choice:
                                        delta = choice["delta"]

                                        # Check for different content types
                                        content = delta.get("content", "")
                                        reasoning = delta.get("reasoning", "")
                                        text = delta.get("text", "")

                                        # Yield structured data with content type
                                        if reasoning:
                                            yield {"type": "reasoning", "content": reasoning}
                                        elif content:
                                            yield {"type": "content", "content": content}
                                        elif text:
                                            yield {"type": "content", "content": text}
                            except json.JSONDecodeError:
                                continue
                else:
                    error_text = await response.text()
                    logger.error(f"Streaming chat API error {response.status}: {error_text}")

        except Exception as e:
            logger.error(f"Failed to create streaming completion for {provider_id}: {e}")

# Global chat client instance
chat_client = ChatClient()