"""
Configuration Manager for MCP Open Client
Handles global app configuration, encryption, and persistence
"""
import json
import os
import time
import logging
from typing import Dict, List, Optional, Any
from cryptography.fernet import Fernet
from pathlib import Path

logger = logging.getLogger(__name__)

class ConfigManager:
    """Global configuration manager with encryption support"""

    def __init__(self):
        self.config_dir = Path(__file__).parent
        self.config_file = self.config_dir / "app_config.json"
        self.key_file = self.config_dir / ".encryption_key"
        self._config: Dict[str, Any] = {}
        self._cipher_suite: Optional[Fernet] = None

        # Initialize encryption and load config
        self._init_encryption()
        self.load_config()
        self.initialize_default_providers()

    def _init_encryption(self):
        """Initialize encryption key"""
        try:
            if self.key_file.exists():
                # Load existing key
                with open(self.key_file, 'rb') as f:
                    key = f.read()
            else:
                # Generate new key
                key = Fernet.generate_key()
                with open(self.key_file, 'wb') as f:
                    f.write(key)
                # Set restrictive permissions (600)
                os.chmod(self.key_file, 0o600)

            self._cipher_suite = Fernet(key)
            logger.info("Encryption initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize encryption: {e}")
            self._cipher_suite = None

    def encrypt_value(self, value: str) -> Optional[str]:
        """Encrypt a string value"""
        if not self._cipher_suite or not value:
            return None

        try:
            encrypted_bytes = self._cipher_suite.encrypt(value.encode())
            return encrypted_bytes.decode()
        except Exception as e:
            logger.error(f"Failed to encrypt value: {e}")
            return None

    def decrypt_value(self, encrypted_value: str) -> Optional[str]:
        """Decrypt a string value"""
        if not self._cipher_suite or not encrypted_value:
            return None

        try:
            decrypted_bytes = self._cipher_suite.decrypt(encrypted_value.encode())
            return decrypted_bytes.decode()
        except Exception as e:
            logger.error(f"Failed to decrypt value: {e}")
            return None

    def load_config(self) -> bool:
        """Load configuration from JSON file"""
        try:
            if not self.config_file.exists():
                logger.warning("Config file not found, using defaults")
                self._config = self._get_default_config()
                self.save_config()
                return True

            with open(self.config_file, 'r', encoding='utf-8') as f:
                self._config = json.load(f)

            logger.info("Configuration loaded successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            self._config = self._get_default_config()
            return False

    def save_config(self) -> bool:
        """Save configuration to JSON file"""
        try:
            # Ensure config directory exists
            self.config_dir.mkdir(exist_ok=True)

            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)

            logger.info("Configuration saved successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            return False

    def get_config(self) -> Dict[str, Any]:
        """Get complete configuration"""
        return self._config.copy()

    def get_providers(self) -> List[Dict[str, Any]]:
        """Get list of available providers"""
        return self._config.get('providers', [])

    def get_provider(self, provider_id: str) -> Optional[Dict[str, Any]]:
        """Get specific provider configuration"""
        for provider in self.get_providers():
            if provider.get('id') == provider_id:
                return provider
        return None


    def get_selected_config(self) -> Dict[str, Any]:
        """Get current selected configuration"""
        return self._config.get('selected_configuration', {})

    def set_provider_api_key(self, provider_id: str, api_key: str) -> bool:
        """Set and encrypt API key for provider"""
        provider = self.get_provider(provider_id)
        if not provider:
            return False

        encrypted_key = self.encrypt_value(api_key)
        if encrypted_key is None:
            logger.error("Failed to encrypt API key")
            return False

        # Find and update provider in config
        for i, p in enumerate(self._config['providers']):
            if p.get('id') == provider_id:
                self._config['providers'][i]['api_key_encrypted'] = encrypted_key
                break

        return self.save_config()

    def get_provider_api_key(self, provider_id: str) -> Optional[str]:
        """Get decrypted API key for provider"""
        provider = self.get_provider(provider_id)
        if not provider:
            return None

        encrypted_key = provider.get('api_key_encrypted')
        if not encrypted_key:
            return None

        return self.decrypt_value(encrypted_key)

    def update_selected_config(self, **kwargs) -> bool:
        """Update selected configuration"""
        selected = self._config.setdefault('selected_configuration', {})

        for key, value in kwargs.items():
            if key in ['provider_id', 'main_model', 'small_model']:
                selected[key] = value

        return self.save_config()

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
            'api_key_encrypted': provider_data.get('api_key_encrypted')
        }

        self._config.setdefault('providers', []).append(provider)
        logger.info(f"Added provider: {provider['id']}")
        return self.save_config()

    def remove_provider(self, provider_id: str) -> bool:
        """Remove a provider from configuration"""
        providers = self._config.get('providers', [])
        original_count = len(providers)

        self._config['providers'] = [p for p in providers if p.get('id') != provider_id]

        if len(self._config['providers']) < original_count:
            # Clear selection if removing the selected provider
            selected = self.get_selected_config()
            if selected.get('provider_id') == provider_id:
                self.update_selected_config(provider_id="", main_model="", small_model="")

            logger.info(f"Removed provider: {provider_id}")
            return self.save_config()

        logger.warning(f"Provider {provider_id} not found")
        return False

    def update_provider(self, provider_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing provider"""
        for provider in self._config.get('providers', []):
            if provider.get('id') == provider_id:
                # Update only allowed fields
                allowed_fields = ['name', 'base_url', 'api_key_encrypted']
                for field, value in updates.items():
                    if field in allowed_fields:
                        provider[field] = value

                logger.info(f"Updated provider: {provider_id}")
                return self.save_config()

        logger.error(f"Provider {provider_id} not found for update")
        return False

    def initialize_default_providers(self) -> bool:
        """Initialize default providers if none exist"""
        if self.get_providers():
            return True  # Already have providers

        default_providers = [
            {
                "id": "openai",
                "name": "OpenAI",
                "base_url": "https://api.openai.com/v1",
                "api_key_encrypted": None
            },
            {
                "id": "anthropic",
                "name": "Anthropic",
                "base_url": "https://api.anthropic.com/v1",
                "api_key_encrypted": None
            },
            {
                "id": "cerebras",
                "name": "Cerebras",
                "base_url": "https://api.cerebras.ai/v1",
                "api_key_encrypted": None
            },
            {
                "id": "groq",
                "name": "Groq",
                "base_url": "https://api.groq.com/openai/v1",
                "api_key_encrypted": None
            }
        ]

        for provider in default_providers:
            self.add_provider(provider)

        logger.info("Initialized default providers")
        return True

    def update_ui_config(self, **kwargs) -> bool:
        """Update UI configuration"""
        ui_config = self._config.setdefault('ui', {})

        for key, value in kwargs.items():
            if key in ['left_sidebar_collapsed', 'right_sidebar_collapsed',
                      'bottom_panel_collapsed', 'theme_mode']:
                ui_config[key] = value

        return self.save_config()

    async def fetch_provider_models(self, provider_id: str) -> List[Dict[str, Any]]:
        """Fetch models from provider API"""
        try:
            logger.info(f"🔄 Fetching models for provider: {provider_id}")
            provider = self.get_provider(provider_id)
            if not provider:
                logger.error(f"Provider {provider_id} not found")
                return []

            api_key = self.get_provider_api_key(provider_id)
            if not api_key:
                logger.warning(f"No API key found for {provider_id}")
                return []

            logger.info(f"✅ API key found for {provider_id}, fetching models from API...")

            # Import here to avoid circular dependencies
            from mcp_open_client.services.provider_client import provider_client

            async with provider_client:
                models = await provider_client.fetch_provider_models(provider_id, api_key)

            logger.info(f"📨 Received {len(models) if models else 0} models from {provider_id} API")
            return models

        except Exception as e:
            logger.error(f"Failed to fetch models for {provider_id}: {e}")
            return []

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration structure"""
        return {
            "app": {
                "name": "MCP Open Client",
                "version": "1.0.0",
                "theme": "terminal-dark"
            },
            "providers": [],
            "selected_configuration": {
                "provider_id": "",
                "main_model": "",
                "small_model": ""
            },
            "ui": {
                "left_sidebar_collapsed": False,
                "right_sidebar_collapsed": False,
                "bottom_panel_collapsed": True,
                "theme_mode": "dark"
            },
            "mcp": {
                "servers": [],
                "tools": [],
                "resources": []
            }
        }

# Global configuration instance
config_manager = ConfigManager()