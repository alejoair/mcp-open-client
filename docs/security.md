# Seguridad

## Visión General

MCP Open Client implementa múltiples capas de seguridad para proteger datos sensibles, especialmente API keys de proveedores LLM. La arquitectura de seguridad está diseñada siguiendo mejores prácticas de la industria.

---

## 🔐 Encriptación de API Keys

### Sistema de Encriptación

#### Algoritmo Utilizado
- **Cryptography Library**: `cryptography` (Fernet)
- **Algoritmo**: AES 128 en modo CBC con HMAC SHA-256
- **Key Derivation**: Claves generadas automáticamente usando `Fernet.generate_key()`

#### Implementación
```python
from cryptography.fernet import Fernet

class ConfigManager:
    def _init_encryption(self):
        """Inicialización segura de encriptación"""
        if self.key_file.exists():
            # Cargar clave existente
            with open(self.key_file, 'rb') as f:
                key = f.read()
        else:
            # Generar nueva clave
            key = Fernet.generate_key()
            with open(self.key_file, 'wb') as f:
                f.write(key)
            # Permisos restrictivos (600)
            os.chmod(self.key_file, 0o600)

        self._cipher_suite = Fernet(key)
```

### Gestión de Claves

#### Archivo de Clave
- **Ubicación**: `mcp_open_client/config/.encryption_key`
- **Permisos**: `600` (solo lectura/escritura para el owner)
- **Generación**: Automática en primer inicio
- **Rotación**: Manual (requiere re-encriptación de datos)

#### Operaciones Seguras
```python
def encrypt_value(self, value: str) -> Optional[str]:
    """Encripta un valor sensible"""
    if not self._cipher_suite or not value:
        return None

    try:
        encrypted_bytes = self._cipher_suite.encrypt(value.encode('utf-8'))
        return encrypted_bytes.decode('utf-8')
    except Exception as e:
        logger.error(f"Encryption failed: {e}")
        return None

def decrypt_value(self, encrypted_value: str) -> Optional[str]:
    """Desencripta un valor sensible"""
    if not self._cipher_suite or not encrypted_value:
        return None

    try:
        decrypted_bytes = self._cipher_suite.decrypt(encrypted_value.encode('utf-8'))
        return decrypted_bytes.decode('utf-8')
    except Exception as e:
        logger.error(f"Decryption failed: {e}")
        return None
```

---

## 🛡️ Protección de Datos Sensibles

### API Key Lifecycle

#### Recepción desde Frontend
```python
@router.post("/api/config/providers/{provider_id}/api-key")
async def set_provider_api_key(provider_id: str, request: SetAPIKeyRequest):
    """
    1. API key llega en texto plano vía HTTPS
    2. Se encripta inmediatamente
    3. Nunca se almacena en texto plano
    4. Se persiste encriptada en JSON
    """
    api_key = request.api_key  # ⚠️ Único momento en texto plano

    # Encriptación inmediata
    success = config_manager.set_provider_api_key(provider_id, api_key)

    # API key sale de scope inmediatamente
    del api_key
```

#### Uso en Requests
```python
def get_provider_api_key(self, provider_id: str) -> Optional[str]:
    """
    1. Se desencripta solo cuando es necesaria
    2. Se usa inmediatamente en HTTP request
    3. Sale de memoria después del uso
    """
    provider = self.get_provider(provider_id)
    encrypted_key = provider.get('api_key_encrypted')

    if not encrypted_key:
        return None

    # Desencriptación temporal
    return self.decrypt_value(encrypted_key)

# Uso en ChatClient
api_key = config_manager.get_provider_api_key(provider_id)
headers = self.get_provider_headers(provider_id, api_key)
# api_key sale de scope después del request
```

### Logging Seguro

#### Políticas de Logging
```python
# ✅ Logging seguro
logger.info(f"Updated provider: {provider_id}")
logger.info(f"API key configured for provider: {provider_id}")

# ❌ NUNCA hacer esto
# logger.info(f"API key: {api_key}")  # Exposición en logs
# logger.debug(f"Headers: {headers}") # Puede contener API key
```

#### Log Sanitization
```python
def sanitize_log_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Sanitiza datos para logging seguro"""
    sanitized = data.copy()

    # Campos a ofuscar
    sensitive_fields = ['api_key', 'authorization', 'x-api-key']

    for field in sensitive_fields:
        if field in sanitized:
            sanitized[field] = "***REDACTED***"

    return sanitized
```

---

## 🌐 Seguridad de Red

### HTTPS/TLS

#### Comunicación Frontend-Backend
```javascript
// Frontend siempre usa HTTPS en producción
const apiBase = process.env.NODE_ENV === 'production'
    ? 'https://your-domain.com/api'
    : 'http://localhost:8007/api';
```

#### Comunicación Backend-Providers
```python
# Configuración de cliente HTTP seguro
async def create_completion(self, provider_id: str, api_key: str, ...):
    headers = {
        'Authorization': f'Bearer {api_key}',
        'User-Agent': 'MCP-Open-Client/1.0.0',
        # Nunca se incluye API key en URL o query params
    }

    # Solo HTTPS para providers externos
    if not provider_base_url.startswith('https://'):
        raise SecurityError("Only HTTPS allowed for external providers")
```

### CORS Configuration

#### Configuración Segura
```python
# app.py - Configuración CORS restrictiva
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8007"],  # Solo origen específico
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# En producción se configuraría con el dominio real:
# allow_origins=["https://your-domain.com"]
```

---

## 🔒 Seguridad del Frontend

### Input Sanitization

#### Sanitización de Mensajes
```javascript
// ChatInput.js - Sanitización básica
handleSend = () => {
    const { message } = this.state;
    const sanitizedMessage = this.sanitizeInput(message);

    if (!sanitizedMessage.trim()) return;

    this.props.onSendMessage(sanitizedMessage);
}

sanitizeInput = (input) => {
    // Limitar longitud
    if (input.length > 10000) {
        input = input.substring(0, 10000);
    }

    // Escapar HTML básico
    return input
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .trim();
}
```

#### Validación de API Keys
```javascript
// LeftBar.js - Validación de formato
validateApiKey = (apiKey) => {
    // Verificar formato básico (no contenido)
    if (!apiKey || apiKey.length < 10) {
        return { valid: false, message: 'API key too short' };
    }

    // Detectar patrones sospechosos
    if (apiKey.includes('javascript:') || apiKey.includes('<script>')) {
        return { valid: false, message: 'Invalid characters detected' };
    }

    return { valid: true };
}
```

### XSS Prevention

#### Safe Rendering
```javascript
// ChatWindow.js - Renderizado seguro
renderMessageContent = (message) => {
    // Usar textContent en lugar de innerHTML
    return React.createElement('div', {
        className: 'message-content'
    }, message.content); // React escapa automáticamente

    // ❌ NUNCA hacer esto:
    // dangerouslySetInnerHTML: { __html: message.content }
}
```

#### Content Security Policy (Headers)
```python
# En FastAPI - Headers de seguridad
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)

    # CSP básico
    response.headers["Content-Security-Policy"] = \
        "default-src 'self'; " \
        "script-src 'self' 'unsafe-inline'; " \
        "style-src 'self' 'unsafe-inline'"

    # Otros headers de seguridad
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"

    return response
```

---

## 🛠️ Seguridad en Tool Execution

### Simulación Segura

#### Restricciones en ToolSimulator
```python
class ToolSimulator:
    async def calculate(self, expression: str) -> str:
        """Calculadora con validación de seguridad"""

        # Whitelist de caracteres permitidos
        allowed_chars = set('0123456789+-*/()._ \t')
        if not all(c in allowed_chars for c in expression):
            return "Error: Invalid characters in expression"

        # Blacklist de operaciones peligrosas
        dangerous_operations = ['import', 'exec', '__', 'eval', 'open']
        if any(op in expression.lower() for op in dangerous_operations):
            return "Error: Unsafe operation detected"

        # Limitar longitud
        if len(expression) > 100:
            return "Error: Expression too long"

        try:
            # Usar eval con restricciones (solo en simulación)
            result = eval(expression, {"__builtins__": {}}, {})
            return f"Result: {result}"
        except Exception as e:
            return f"Error: {str(e)}"
```

#### Sandboxing Preparation
```python
# Preparación para sandboxing real
class SecureToolExecutor:
    def __init__(self):
        self.allowed_tools = {
            'calculate', 'get_current_time',
            'search_web', 'get_weather'
        }

    async def execute_tool(self, name: str, arguments: str) -> Dict[str, Any]:
        # Validar herramienta permitida
        if name not in self.allowed_tools:
            raise SecurityError(f"Tool '{name}' not allowed")

        # Validar argumentos JSON
        try:
            args = json.loads(arguments)
        except json.JSONDecodeError:
            raise SecurityError("Invalid JSON arguments")

        # Rate limiting
        await self.check_rate_limit()

        # Timeout
        return await asyncio.wait_for(
            self.execute_safely(name, args),
            timeout=30.0
        )
```

---

## 📊 Auditing y Monitoring

### Security Logging

#### Eventos de Seguridad
```python
class SecurityLogger:
    @staticmethod
    def log_api_key_configured(provider_id: str, user_ip: str):
        logger.info(
            f"API key configured for provider '{provider_id}' from IP {user_ip}",
            extra={
                'event_type': 'api_key_configured',
                'provider_id': provider_id,
                'user_ip': user_ip,
                'timestamp': datetime.utcnow().isoformat()
            }
        )

    @staticmethod
    def log_failed_decryption(provider_id: str):
        logger.warning(
            f"Failed to decrypt API key for provider '{provider_id}'",
            extra={
                'event_type': 'decryption_failure',
                'provider_id': provider_id,
                'timestamp': datetime.utcnow().isoformat()
            }
        )

    @staticmethod
    def log_suspicious_tool_request(tool_name: str, arguments: str):
        logger.warning(
            f"Suspicious tool request: {tool_name}",
            extra={
                'event_type': 'suspicious_tool_request',
                'tool_name': tool_name,
                'arguments_hash': hashlib.sha256(arguments.encode()).hexdigest()[:16]
            }
        )
```

### Rate Limiting

#### Request Rate Limiting
```python
from collections import defaultdict, deque
import time

class RateLimiter:
    def __init__(self):
        self.requests = defaultdict(deque)  # IP -> deque of timestamps
        self.limit = 100  # requests per hour
        self.window = 3600  # 1 hour

    def is_allowed(self, client_ip: str) -> bool:
        now = time.time()
        client_requests = self.requests[client_ip]

        # Remove old requests
        while client_requests and client_requests[0] < now - self.window:
            client_requests.popleft()

        # Check limit
        if len(client_requests) >= self.limit:
            return False

        # Add current request
        client_requests.append(now)
        return True

# Middleware
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host

    if not rate_limiter.is_allowed(client_ip):
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded"}
        )

    return await call_next(request)
```

---

## 🔐 Mejores Prácticas Implementadas

### Principios de Seguridad

#### Defense in Depth
1. **Encriptación**: API keys encriptadas at rest
2. **Transport Security**: HTTPS obligatorio
3. **Input Validation**: Sanitización en múltiples capas
4. **Access Control**: Rate limiting y validación
5. **Logging**: Auditing de eventos de seguridad

#### Principle of Least Privilege
- API keys solo se desencriptan cuando es necesario
- Herramientas limitadas a conjunto seguro
- Permisos de archivo restrictivos
- CORS configurado específicamente

#### Fail Securely
```python
# Ejemplo de fallo seguro
def get_provider_api_key(self, provider_id: str) -> Optional[str]:
    try:
        encrypted_key = provider.get('api_key_encrypted')
        return self.decrypt_value(encrypted_key)
    except Exception as e:
        # Log error pero no exponer detalles
        logger.error(f"Failed to retrieve API key for {provider_id}")
        return None  # Fallo seguro - no API key
```

### Security Checklist

#### ✅ Implementado
- [x] Encriptación de API keys con Fernet
- [x] Permisos de archivo restrictivos (600)
- [x] HTTPS para comunicación externa
- [x] Input sanitization básica
- [x] Logging seguro (no API keys)
- [x] CORS configurado
- [x] Headers de seguridad
- [x] Tool execution con validación

#### 🚧 Recomendaciones Futuras
- [ ] Key rotation automática
- [ ] Rate limiting por usuario
- [ ] Tool execution sandboxing completo
- [ ] Auditing dashboard
- [ ] Intrusion detection
- [ ] Multi-factor authentication
- [ ] Session management
- [ ] Database encryption (cuando se implemente)

---

## ⚠️ Consideraciones de Despliegue

### Producción

#### Variables de Entorno
```bash
# Variables de entorno para producción
ENVIRONMENT=production
API_BASE_URL=https://your-domain.com/api
CORS_ORIGINS=https://your-domain.com
LOG_LEVEL=INFO
ENCRYPTION_KEY_PATH=/secure/path/.encryption_key
```

#### File Permissions
```bash
# Permisos de archivos en producción
chmod 600 .encryption_key
chmod 644 app_config.json
chmod 700 config/
```

#### Reverse Proxy
```nginx
# nginx.conf - Configuración segura
server {
    listen 443 ssl;
    server_name your-domain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";

    location / {
        proxy_pass http://localhost:8007;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```