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
    max_tokens: int = 1000

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
    max_tokens: Optional[int] = None

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

# Tool Models
class ToolFunction(BaseModel):
    name: str
    description: str
    parameters: Dict[str, Any]

class Tool(BaseModel):
    type: str = "function"
    function: ToolFunction

class ToolCall(BaseModel):
    id: str
    type: str = "function"
    function: Dict[str, Any]  # {"name": str, "arguments": str}

class ToolResult(BaseModel):
    tool_call_id: str
    name: str
    content: str
    status: str = "success"  # "success", "error"
    execution_time: Optional[float] = None

# Chat Models
class ChatMessage(BaseModel):
    role: str  # "user", "assistant", "system", "tool"
    content: Optional[str] = None
    tool_calls: Optional[List[ToolCall]] = None
    tool_call_id: Optional[str] = None  # For tool result messages
    name: Optional[str] = None  # Tool name for tool messages

class ChatCompletionRequest(BaseModel):
    messages: List[ChatMessage]
    max_tokens: Optional[int] = 1000
    temperature: Optional[float] = 0.7
    tools: Optional[List[Tool]] = None
    tool_choice: Optional[str] = "auto"  # "auto", "none", "required", or specific tool

class ChatCompletionResponse(BaseModel):
    response: str
    model: str
    provider: str
    message_count: int
    tool_calls: Optional[List[ToolCall]] = None
    tool_results: Optional[List[ToolResult]] = None