"""
Pydantic models for API requests and responses
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

# Configuration Models
class ProviderModel(BaseModel):
    id: str
    name: str
    base_url: str

class ModelInfo(BaseModel):
    id: str
    object: str = "model"
    created: Optional[int] = None
    owned_by: Optional[str] = None

class SelectedConfiguration(BaseModel):
    provider_id: str
    main_model: str
    small_model: str

class UIConfig(BaseModel):
    left_sidebar_collapsed: bool
    right_sidebar_collapsed: bool
    bottom_panel_collapsed: bool
    theme_mode: str

# Request Models
class SetAPIKeyRequest(BaseModel):
    provider_id: str
    api_key: str

class UpdateConfigRequest(BaseModel):
    provider_id: Optional[str] = None
    main_model: Optional[str] = None
    small_model: Optional[str] = None

class UpdateUIConfigRequest(BaseModel):
    left_sidebar_collapsed: Optional[bool] = None
    right_sidebar_collapsed: Optional[bool] = None
    bottom_panel_collapsed: Optional[bool] = None
    theme_mode: Optional[str] = None

class CreateProviderRequest(BaseModel):
    id: str
    name: str
    base_url: str

class UpdateProviderRequest(BaseModel):
    name: Optional[str] = None
    base_url: Optional[str] = None

# Response Models
class ConfigResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None

class ProvidersResponse(BaseModel):
    providers: List[ProviderModel]

class ModelsResponse(BaseModel):
    models: List[ModelInfo]

class CurrentConfigResponse(BaseModel):
    selected_configuration: SelectedConfiguration
    ui: UIConfig

# Chat Models
class ChatMessage(BaseModel):
    role: str  # "user", "assistant", "system"
    content: str

class ChatCompletionRequest(BaseModel):
    messages: List[ChatMessage]
    max_tokens: Optional[int] = 1000
    temperature: Optional[float] = 0.7

class ChatCompletionResponse(BaseModel):
    response: str
    model: str
    provider: str
    message_count: int