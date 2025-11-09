"""
Provider management for LLM providers
"""
import json
import time
import logging
from typing import Dict, List, Optional, Any
from .encryption import EncryptionManager

logger = logging.getLogger(__name__)

class ProviderManager:
    """Manages LLM provider configurations"""

    def __init__(self, config_data: Dict[str, Any], encryption_manager: EncryptionManager):
        self._config = config_data
        self._encryption = encryption_manager

    def get_providers(self) -> List[Dict[str, Any]]:
        """Get list of available providers"""
        return self._config.get('providers', [])

    def get_provider(self, provider_id: str) -> Optional[Dict[str, Any]]:
        """Get specific provider configuration"""
        for provider in self.get_providers():
            if provider.get('id') == provider_id:
                return provider
        return None

    def get_provider_models(self, provider_id: str, model_type: str = None) -> List[Dict[str, Any]]:
        """Get models for a specific provider"""
        provider = self.get_provider(provider_id)
        if not provider:
            return []

        models = provider.get('models', [])
        if model_type:
            models = [m for m in models if m.get('type') == model_type]

        return models

    def add_provider(self, provider_data: Dict[str, Any]) -> bool:
        """Add a new provider to configuration"""
        required_fields = ['id', 'name', 'base_url']
        for field in required_fields:
            if field not in provider_data:
                logger.error(f"Missing required field '{field}' for provider")
                return False

        # Check if provider already exists
        for existing_provider in self.get_providers():
            if existing_provider.get('id') == provider_data['id']:
                logger.error(f"Provider {provider_data['id']} already exists")
                return False

        # Set defaults for optional fields
        provider = {
            'id': provider_data['id'],
            'name': provider_data['name'],
            'base_url': provider_data['base_url'],
            'api_key_encrypted': provider_data.get('api_key_encrypted'),
            'models': provider_data.get('models', [])
        }

        self._config.setdefault('providers', []).append(provider)
        logger.info(f"Added provider: {provider['id']}")
        return True

    def remove_provider(self, provider_id: str) -> bool:
        """Remove a provider from configuration"""
        providers = self._config.get('providers', [])
        original_count = len(providers)

        self._config['providers'] = [p for p in providers if p.get('id') != provider_id]

        if len(self._config['providers']) < original_count:
            # Clear selection if removing the selected provider
            selected = self._config.get('selected_configuration', {})
            if selected.get('provider_id') == provider_id:
                selected.update({
                    'provider_id': '',
                    'main_model': '',
                    'small_model': ''
                })

            logger.info(f"Removed provider: {provider_id}")
            return True

        logger.warning(f"Provider {provider_id} not found")
        return False

    def update_provider(self, provider_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing provider"""
        for provider in self._config.get('providers', []):
            if provider.get('id') == provider_id:
                # Update only allowed fields
                allowed_fields = ['name', 'base_url', 'models', 'api_key_encrypted']
                for field, value in updates.items():
                    if field in allowed_fields:
                        provider[field] = value

                logger.info(f"Updated provider: {provider_id}")
                return True

        logger.error(f"Provider {provider_id} not found for update")
        return False

    def set_provider_api_key(self, provider_id: str, api_key: str) -> bool:
        """Set and encrypt API key for provider"""
        provider = self.get_provider(provider_id)
        if not provider:
            return False

        encrypted_key = self._encryption.encrypt_value(api_key)
        if encrypted_key is None:
            logger.error("Failed to encrypt API key")
            return False

        # Find and update provider in config
        for i, p in enumerate(self._config['providers']):
            if p.get('id') == provider_id:
                self._config['providers'][i]['api_key_encrypted'] = encrypted_key
                break

        return True

    def get_provider_api_key(self, provider_id: str) -> Optional[str]:
        """Get decrypted API key for provider"""
        provider = self.get_provider(provider_id)
        if not provider:
            return None

        encrypted_key = provider.get('api_key_encrypted')
        if not encrypted_key:
            return None

        return self._encryption.decrypt_value(encrypted_key)

    def update_provider_models(self, provider_id: str, models: List[Dict[str, Any]]) -> bool:
        """Update models for a provider"""
        for provider in self._config.get('providers', []):
            if provider.get('id') == provider_id:
                provider['models'] = models
                provider['last_model_fetch'] = json.dumps({
                    "timestamp": int(time.time()),
                    "count": len(models)
                })
                logger.info(f"Updated {len(models)} models for provider {provider_id}")
                return True

        logger.error(f"Provider {provider_id} not found for model update")
        return False

    def get_provider_models_cache_status(self, provider_id: str) -> Dict[str, Any]:
        """Get cache status for provider models"""
        provider = self.get_provider(provider_id)
        if not provider:
            return {"cached": False, "timestamp": None, "count": 0}

        cache_info = provider.get('last_model_fetch')
        if not cache_info:
            return {"cached": False, "timestamp": None, "count": len(provider.get('models', []))}

        try:
            cache_data = json.loads(cache_info)
            return {
                "cached": True,
                "timestamp": cache_data.get('timestamp'),
                "count": cache_data.get('count', 0),
                "age_hours": (int(time.time()) - cache_data.get('timestamp', 0)) / 3600
            }
        except:
            return {"cached": False, "timestamp": None, "count": len(provider.get('models', []))}

    def initialize_default_providers(self) -> bool:
        """Initialize default providers if none exist"""
        if self.get_providers():
            return True  # Already have providers

        default_providers = [
            {
                "id": "openai",
                "name": "OpenAI",
                "base_url": "https://api.openai.com/v1",
                "api_key_encrypted": None,
                "models": []
            },
            {
                "id": "anthropic",
                "name": "Anthropic",
                "base_url": "https://api.anthropic.com/v1",
                "api_key_encrypted": None,
                "models": []
            },
            {
                "id": "cerebras",
                "name": "Cerebras",
                "base_url": "https://api.cerebras.ai/v1",
                "api_key_encrypted": None,
                "models": []
            },
            {
                "id": "groq",
                "name": "Groq",
                "base_url": "https://api.groq.com/openai/v1",
                "api_key_encrypted": None,
                "models": []
            }
        ]

        for provider in default_providers:
            self.add_provider(provider)

        logger.info("Initialized default providers")
        return True