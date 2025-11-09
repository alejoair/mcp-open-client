# Sistema de Configuración

## Visión General

El sistema de configuración de MCP Open Client está centralizado en `ConfigManager`, que maneja toda la configuración de la aplicación, incluyendo providers, API keys, configuración de UI y configuración seleccionada.

## ConfigManager - Gestor Central

### 📄 Ubicación
`mcp_open_client/config/config_manager.py`

### 🏗️ Arquitectura

#### Inicialización
```python
class ConfigManager:
    def __init__(self):
        self.config_dir = Path(__file__).parent
        self.config_file = self.config_dir / "app_config.json"
        self.key_file = self.config_dir / ".encryption_key"
        self._config: Dict[str, Any] = {}
        self._cipher_suite: Optional[Fernet] = None
```

#### Instancia Global
```python
# Al final del archivo
config_manager = ConfigManager()
```

### 🔐 Sistema de Encriptación

#### Generación Automática de Claves
- **Archivo**: `.encryption_key` (auto-generado)
- **Algoritmo**: Fernet (criptografía simétrica)
- **Permisos**: 600 (solo lectura/escritura para el owner)

#### Métodos de Encriptación
```python
def encrypt_value(self, value: str) -> Optional[str]
def decrypt_value(self, encrypted_value: str) -> Optional[str]
```

## Estructura de Configuración

### 📄 app_config.json

```json
{
  "app": {
    "name": "MCP Open Client",
    "version": "1.0.0",
    "theme": "terminal-dark"
  },
  "providers": [
    {
      "id": "cerebras",
      "name": "Cerebras",
      "base_url": "https://api.cerebras.ai/v1",
      "api_key_encrypted": "encrypted_key_here"
    },
    {
      "id": "openai",
      "name": "OpenAI",
      "base_url": "https://api.openai.com/v1",
      "api_key_encrypted": null
    }
  ],
  "selected_configuration": {
    "provider_id": "cerebras",
    "main_model": "zai-glm-4.6",
    "small_model": "gpt-oss-120b"
  },
  "ui": {
    "left_sidebar_collapsed": false,
    "right_sidebar_collapsed": false,
    "bottom_panel_collapsed": true,
    "theme_mode": "dark"
  },
  "mcp": {
    "servers": [],
    "tools": [],
    "resources": []
  }
}
```

## Gestión de Providers

### 🔧 Funcionalidades

#### Obtener Providers
```python
def get_providers(self) -> List[Dict[str, Any]]
def get_provider(self, provider_id: str) -> Optional[Dict[str, Any]]
```

#### Agregar Provider
```python
def add_provider(self, provider_data: Dict[str, Any]) -> bool
```
**Campos requeridos**: `id`, `name`, `base_url`

#### Actualizar Provider
```python
def update_provider(self, provider_id: str, updates: Dict[str, Any]) -> bool
```
**Campos permitidos**: `name`, `base_url`, `api_key_encrypted`

#### Eliminar Provider
```python
def remove_provider(self, provider_id: str) -> bool
```

### 🔑 Gestión de API Keys

#### Configurar API Key
```python
def set_provider_api_key(self, provider_id: str, api_key: str) -> bool
```
- Encripta automáticamente la API key
- Actualiza el provider en la configuración
- Persiste cambios inmediatamente

#### Obtener API Key
```python
def get_provider_api_key(self, provider_id: str) -> Optional[str]
```
- Desencripta automáticamente la API key
- Retorna `None` si no existe o falla la desencriptación

## Configuración Seleccionada

### 🎯 Propósito
Define qué provider y modelos están actualmente seleccionados para uso.

### 📊 Estructura
```python
{
    "provider_id": str,     # ID del provider activo
    "main_model": str,      # Modelo principal para chat
    "small_model": str      # Modelo pequeño/rápido (futuro uso)
}
```

### 🔧 Métodos
```python
def get_selected_config(self) -> Dict[str, Any]
def update_selected_config(self, **kwargs) -> bool
```

**Campos permitidos**: `provider_id`, `main_model`, `small_model`

## Configuración de UI

### 🎨 Estado de Interface

#### Configuración UI
```python
{
    "left_sidebar_collapsed": bool,
    "right_sidebar_collapsed": bool,
    "bottom_panel_collapsed": bool,
    "theme_mode": str  # "dark" | "light"
}
```

#### Métodos
```python
def get_ui_config(self) -> Dict[str, Any]
def update_ui_config(self, **kwargs) -> bool
```

## Providers por Defecto

### 🏭 Inicialización Automática

Cuando no hay providers configurados, se inicializan automáticamente:

```python
def initialize_default_providers(self) -> bool
```

#### Providers Incluidos
1. **OpenAI**
   - ID: `openai`
   - Base URL: `https://api.openai.com/v1`
   - API Key: No configurada

2. **Anthropic**
   - ID: `anthropic`
   - Base URL: `https://api.anthropic.com/v1`
   - API Key: No configurada

3. **Cerebras**
   - ID: `cerebras`
   - Base URL: `https://api.cerebras.ai/v1`
   - API Key: No configurada

## Persistencia y Carga

### 💾 Gestión de Archivo

#### Carga de Configuración
```python
def load_config(self) -> bool
```
- Crea archivo por defecto si no existe
- Carga configuración existente
- Valida estructura e integridad

#### Guardado de Configuración
```python
def save_config(self) -> bool
```
- Guarda inmediatamente tras cualquier cambio
- Formato JSON con indentación
- Codificación UTF-8

### 🔄 Auto-Persistencia
Todos los métodos de modificación (`add_provider`, `update_selected_config`, etc.) llaman automáticamente a `save_config()`.

## Configuración MCP

### 🔮 Preparación para Futuro

```python
"mcp": {
    "servers": [],      # Servidores MCP configurados
    "tools": [],        # Herramientas MCP disponibles
    "resources": []     # Recursos MCP disponibles
}
```

**Estado**: Estructura preparada pero no implementada.

## Métodos de Utilidad

### 🛠️ Helpers

#### Validación
```python
def get_config(self) -> Dict[str, Any]  # Configuración completa
def get_default_config(self) -> Dict[str, Any]  # Configuración por defecto
```

#### Logging
- Logs informativos para cambios exitosos
- Logs de error para fallos de operación
- No registra información sensible (API keys)

## Consideraciones de Seguridad

### 🔒 Protección de API Keys
- **Encriptación**: Todas las API keys se almacenan encriptadas
- **Clave segura**: Archivo `.encryption_key` con permisos 600
- **No logs**: Las API keys nunca aparecen en logs
- **Memoria**: Desencriptación solo cuando es necesario

### 🚫 Validación
- **Campos permitidos**: Solo se aceptan campos predefinidos en actualizaciones
- **Tipos de datos**: Validación automática de tipos
- **IDs únicos**: Prevención de providers duplicados

## Uso Típico

### 🔄 Flujo de Configuración

1. **Inicialización**: `ConfigManager()` se crea automáticamente
2. **Carga**: Se carga configuración existente o se crea por defecto
3. **Uso**: Otros componentes acceden vía `config_manager` global
4. **Modificación**: Cambios se persisten automáticamente
5. **Acceso**: Frontend consume configuración vía API REST