"""
Provider API client for fetching real model lists from LLM providers
"""
import asyncio
import logging
from typing import List, Dict, Any, Optional
import aiohttp
from mcp_open_client.config import config_manager

logger = logging.getLogger(__name__)

class ProviderClient:
    """Client for communicating with LLM provider APIs"""

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

    async def fetch_provider_models(self, provider_id: str, api_key: str) -> List[Dict[str, Any]]:
        """Fetch models from any OpenAI-compatible provider"""
        if not api_key:
            logger.warning(f"No API key provided for {provider_id}")
            return []

        provider = config_manager.get_provider(provider_id)
        if not provider:
            logger.error(f"Provider {provider_id} not found")
            return []

        base_url = provider.get("base_url", "")

        try:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }

            logger.info(f"🔗 Making API call to: {base_url}/models")
            async with self.session.get(f"{base_url}/models", headers=headers) as response:
                logger.info(f"📡 API response status: {response.status}")

                if response.status == 200:
                    data = await response.json()
                    models_data = data.get("data", [])
                    logger.info(f"🎯 API returned {len(models_data)} models")

                    # Return models as-is from the API
                    models = []
                    for model in models_data:
                        models.append({
                            "id": model.get("id", ""),
                            "object": model.get("object", "model"),
                            "created": model.get("created"),
                            "owned_by": model.get("owned_by", ""),
                        })

                    return models
                else:
                    error_text = await response.text()
                    logger.error(f"API error {response.status}: {error_text}")
                    return []

        except Exception as e:
            logger.error(f"Failed to fetch models for {provider_id}: {e}")
            return []

# Global provider client instance
provider_client = ProviderClient()