"""
Configuration API routes
"""
import logging
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException
from mcp_open_client.config import config_manager
from mcp_open_client.server.models import (
    ConfigResponse,
    ProvidersResponse,
    ModelsResponse,
    CurrentConfigResponse,
    SetAPIKeyRequest,
    UpdateConfigRequest,
    UpdateUIConfigRequest,
    ProviderModel,
    ModelInfo,
    SelectedConfiguration,
    UIConfig
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/config", tags=["configuration"])

@router.get("/", response_model=CurrentConfigResponse)
async def get_current_config():
    """Get current application configuration"""
    try:
        config = config_manager.get_config()
        selected = config.get('selected_configuration', {})
        ui = config.get('ui', {})

        # Ensure max_tokens has a default value if missing
        if 'max_tokens' not in selected:
            selected['max_tokens'] = 1000

        return CurrentConfigResponse(
            selected_configuration=SelectedConfiguration(**selected),
            ui=UIConfig(**ui)
        )
    except Exception as e:
        logger.error(f"Failed to get current config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/providers", response_model=ProvidersResponse)
async def get_providers():
    """Get list of available providers"""
    try:
        providers = config_manager.get_providers()

        # Remove encrypted API keys from response for security
        safe_providers = []
        for provider in providers:
            safe_provider = provider.copy()
            safe_provider['api_key_encrypted'] = None
            # Add flag to indicate if API key is set
            safe_provider['has_api_key'] = bool(provider.get('api_key_encrypted'))
            safe_providers.append(safe_provider)

        return ProvidersResponse(providers=safe_providers)
    except Exception as e:
        logger.error(f"Failed to get providers: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/providers/{provider_id}/models", response_model=ModelsResponse)
async def get_provider_models(provider_id: str):
    """Get models for a specific provider from its API"""
    try:
        provider = config_manager.get_provider(provider_id)
        if not provider:
            raise HTTPException(status_code=404, detail=f"Provider {provider_id} not found")

        # Fetch models directly from provider API
        models = await config_manager.fetch_provider_models(provider_id)

        if not models:
            return ModelsResponse(models=[])

        # Convert to ModelInfo format (simple)
        model_infos = [
            ModelInfo(
                id=model.get("id", ""),
                object=model.get("object", "model"),
                created=model.get("created"),
                owned_by=model.get("owned_by", "")
            ) for model in models
        ]

        return ModelsResponse(models=model_infos)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get models for provider {provider_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/providers/{provider_id}/api-key", response_model=ConfigResponse)
async def set_provider_api_key(provider_id: str, request: SetAPIKeyRequest):
    """Set API key for a provider"""
    try:
        if request.provider_id != provider_id:
            raise HTTPException(status_code=400, detail="Provider ID mismatch")

        provider = config_manager.get_provider(provider_id)
        if not provider:
            raise HTTPException(status_code=404, detail=f"Provider {provider_id} not found")

        success = config_manager.set_provider_api_key(provider_id, request.api_key)

        if not success:
            raise HTTPException(status_code=500, detail="Failed to set API key")

        return ConfigResponse(
            success=True,
            message=f"API key set successfully for {provider_id}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to set API key for provider {provider_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/providers/{provider_id}/api-key/status")
async def get_api_key_status(provider_id: str):
    """Check if API key is set for a provider"""
    try:
        provider = config_manager.get_provider(provider_id)
        if not provider:
            raise HTTPException(status_code=404, detail=f"Provider {provider_id} not found")

        has_key = bool(provider.get('api_key_encrypted'))
        return {"has_api_key": has_key}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to check API key status for provider {provider_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/selected", response_model=ConfigResponse)
async def update_selected_config(request: UpdateConfigRequest):
    """Update selected configuration (provider, models)"""
    try:
        update_data = {}

        if request.provider_id is not None:
            provider = config_manager.get_provider(request.provider_id)
            if not provider:
                raise HTTPException(status_code=400, detail=f"Provider {request.provider_id} not found")
            update_data['provider_id'] = request.provider_id

        if request.main_model is not None:
            update_data['main_model'] = request.main_model

        if request.small_model is not None:
            update_data['small_model'] = request.small_model

        if request.max_tokens is not None:
            update_data['max_tokens'] = request.max_tokens

        success = config_manager.update_selected_config(**update_data)

        if not success:
            raise HTTPException(status_code=500, detail="Failed to update configuration")

        return ConfigResponse(
            success=True,
            message="Configuration updated successfully",
            data=update_data
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update selected config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/ui", response_model=ConfigResponse)
async def update_ui_config(request: UpdateUIConfigRequest):
    """Update UI configuration"""
    try:
        update_data = {}

        if request.left_sidebar_collapsed is not None:
            update_data['left_sidebar_collapsed'] = request.left_sidebar_collapsed

        if request.right_sidebar_collapsed is not None:
            update_data['right_sidebar_collapsed'] = request.right_sidebar_collapsed

        if request.bottom_panel_collapsed is not None:
            update_data['bottom_panel_collapsed'] = request.bottom_panel_collapsed

        if request.theme_mode is not None:
            update_data['theme_mode'] = request.theme_mode

        success = config_manager.update_ui_config(**update_data)

        if not success:
            raise HTTPException(status_code=500, detail="Failed to update UI configuration")

        return ConfigResponse(
            success=True,
            message="UI configuration updated successfully",
            data=update_data
        )
    except Exception as e:
        logger.error(f"Failed to update UI config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reset", response_model=ConfigResponse)
async def reset_config():
    """Reset configuration to defaults"""
    try:
        # This could be implemented to reset to default config
        # For now, just return success
        return ConfigResponse(
            success=True,
            message="Configuration reset functionality not yet implemented"
        )
    except Exception as e:
        logger.error(f"Failed to reset config: {e}")
        raise HTTPException(status_code=500, detail=str(e))