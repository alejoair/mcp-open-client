# Arquitectura del Frontend

## Visión General

El frontend del MCP Open Client está construido con **React clásico** (class components) y utiliza **Ant Design** para algunos componentes UI. Su arquitectura está diseñada como una aplicación de escritorio terminal con múltiples paneles configurables.

## 🎨 Diseño Visual

### Terminal Theme
```css
:root {
    --terminal-bg: #1e1e1e;           /* Fondo principal */
    --terminal-bg-light: #2d2d2d;     /* Fondo claro */
    --terminal-text: #d4d4d4;         /* Texto principal */
    --terminal-text-bright: #ffffff;   /* Texto destacado */
    --terminal-text-muted: #969696;   /* Texto atenuado */
    --terminal-green: #4ec9b0;        /* Verde terminal */
    --terminal-cyan: #9cdcfe;         /* Cyan terminal */
    --terminal-red: #f44747;          /* Rojo de error */
    --terminal-border: #3e3e3e;      /* Bordes */
}
```

### Layout Responsive
```
┌─────────────────────────────────────────────────────────────┐
│                    TerminalHeader                           │
├───────────┬─────────────────────────────────┬───────────────┤
│           │                                 │               │
│  LeftBar  │           MainContent           │   RightBar    │
│           │                                 │               │
│  Config   │         ChatWindow              │   System      │
│  Panel    │                                 │   Monitor     │
│           │                                 │               │
├───────────┴─────────────────────────────────┴───────────────┤
│                     BottomBar                               │
│                  Console/Logs                              │
└─────────────────────────────────────────────────────────────┘
```

## 📁 Estructura de Componentes

### 🎯 Componente Principal

#### 📄 index.html
- **Ubicación**: `mcp_open_client/ui/index.html`
- **Responsabilidad**: Aplicación principal y orquestación
- **Características**:
  - Carga de todos los componentes
  - Configuración del layout principal
  - Estilos CSS globales
  - Inicialización de React

```html
<!-- Layout principal -->
<div id="app">
    <div class="app-layout">
        <header id="terminal-header"></header>
        <main class="main-layout">
            <aside id="left-bar"></aside>
            <section id="main-content"></section>
            <aside id="right-bar"></aside>
        </main>
        <footer id="bottom-bar"></footer>
    </div>
</div>
```

## 🧩 Componentes por Área

### 📋 TerminalHeader - Barra Superior

#### 📄 Ubicación
`mcp_open_client/ui/components/TerminalHeader.js`

#### 🎯 Funcionalidad
- Título de la aplicación
- Indicadores de estado
- Controles de ventana (estilo terminal)

#### 🏗️ Estructura
```javascript
class TerminalHeader extends React.Component {
    render() {
        // Header con estilo terminal
        // Botones de control de ventana
        // Título y subtítulo
    }
}
```

### ⚙️ LeftBar - Panel de Configuración

#### 📄 Ubicación
`mcp_open_client/ui/components/LeftBar.js`

#### 🎯 Funcionalidad Principal
- **Gestión de Providers LLM**
- **Configuración de API Keys**
- **Selección de Modelos**
- **Estado de Conexión**

#### 🔧 Características Avanzadas

##### Provider Management
```javascript
// Carga dinámica de providers
async loadProviders() {
    const response = await fetch('/api/config/providers');
    // Actualiza lista de providers disponibles
}

// Configuración de API Key
async handleAPIKeySubmit(providerId, apiKey) {
    const response = await fetch(`/api/config/providers/${providerId}/api-key`, {
        method: 'POST',
        body: JSON.stringify({ api_key: apiKey })
    });
}
```

##### Model Selection
```javascript
// Carga modelos por provider
async loadModels(providerId) {
    const response = await fetch(`/api/config/providers/${providerId}/models`);
    // Actualiza dropdown de modelos
}

// Actualiza configuración seleccionada
async updateSelectedConfig(config) {
    const response = await fetch('/api/config/selected', {
        method: 'PUT',
        body: JSON.stringify(config)
    });
}
```

#### 📊 Estado del Componente
```javascript
state = {
    providers: [],              // Lista de providers disponibles
    selectedProvider: null,     // Provider actualmente seleccionado
    models: [],                // Modelos disponibles
    selectedConfig: {},        // Configuración actual
    apiKeyVisible: false,      // Visibilidad del input API key
    loading: false,            // Estado de carga
    connectionStatus: 'disconnected' // Estado de conexión
}
```

### 💬 MainContent - Área Central

#### 📄 Ubicación
`mcp_open_client/ui/components/MainContent.js`

#### 🎯 Responsabilidad
- Orquestación de vistas principales
- Routing entre welcome y chat
- Integración con ChatWindow

#### 🏗️ Vista Selector
```javascript
render() {
    const { currentView } = this.state;
    return currentView === 'welcome' ?
        this.renderWelcomeView() :
        this.renderAIChatView();
}

renderAIChatView() {
    return React.createElement(ChatWindow, {
        key: 'chat-window'
    });
}
```

### 🤖 ChatWindow - Interface de Chat

#### 📄 Ubicación
`mcp_open_client/ui/components/ChatWindow.js`

#### 🎯 Funcionalidad Core
- **Chat con streaming en tiempo real**
- **Separación de reasoning vs content**
- **Manejo de tool calls**
- **Historial de mensajes**

#### ⚡ Streaming Implementation
```javascript
// Configuración Server-Sent Events
startStreaming(messages) {
    const eventSource = new EventSource('/api/chat/completions/stream');

    eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data);
        this.handleStreamEvent(data);
    };
}

handleStreamEvent(data) {
    switch(data.type) {
        case 'reasoning_chunk':
            this.updateReasoning(data);
            break;
        case 'content_chunk':
            this.updateContent(data);
            break;
        case 'tool_call_start':
            this.startToolCall(data);
            break;
        case 'tool_execution_complete':
            this.completeToolCall(data);
            break;
        case 'complete':
            this.finalizeMessage(data);
            break;
    }
}
```

#### 🧠 Message Structure
```javascript
const message = {
    id: uniqueId,
    role: 'user|assistant|system|tool',
    content: 'Main message content',
    reasoning: 'Model reasoning process',
    tool_calls: [...],
    tool_results: [...],
    timestamp: new Date(),
    isStreaming: false
};
```

#### 🛠️ Tool Call Display
```javascript
renderToolCalls(toolCalls) {
    return toolCalls.map(toolCall =>
        React.createElement('div', {
            className: 'tool-call-section'
        }, [
            // Tool call header
            React.createElement('div', {
                className: 'tool-call-header'
            }, `🔧 ${toolCall.function.name}`),

            // Tool arguments (expandable)
            React.createElement('details', {
                className: 'tool-arguments'
            }, [
                React.createElement('summary', {}, 'Arguments'),
                React.createElement('pre', {}, toolCall.function.arguments)
            ]),

            // Tool result
            toolCall.result && React.createElement('div', {
                className: 'tool-result'
            }, toolCall.result.content)
        ])
    );
}
```

### 📝 ChatInput - Input de Mensajes

#### 📄 Ubicación
`mcp_open_client/ui/components/ChatInput.js`

#### 🎯 Funcionalidad
- Input de texto con soporte multiline
- Envío de mensajes al chat
- Historial de comandos
- Estados de envío

#### ⌨️ Input Handling
```javascript
handleSend = () => {
    const { message } = this.state;
    if (!message.trim()) return;

    // Enviar mensaje al padre (ChatWindow)
    this.props.onSendMessage(message.trim());

    // Limpiar input
    this.setState({ message: '' });
}

handleKeyDown = (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        this.handleSend();
    }
}
```

### 📊 RightBar - Monitor del Sistema

#### 📄 Ubicación
`mcp_open_client/ui/components/RightBar.js`

#### 🎯 Funcionalidad
- Monitor de sistema (CPU, memoria)
- Estadísticas de la aplicación
- Estado de conexiones
- Información de debugging

#### 📈 System Monitoring
```javascript
// Actualización cada 2 segundos
componentDidMount() {
    this.interval = setInterval(this.updateStats, 2000);
}

updateStats = () => {
    // Simulación de datos del sistema
    this.setState({
        cpu: Math.floor(Math.random() * 100),
        memory: Math.floor(Math.random() * 100),
        connections: Math.floor(Math.random() * 10),
        uptime: this.calculateUptime()
    });
}
```

### 📺 BottomBar - Panel de Console

#### 📄 Ubicación
`mcp_open_client/ui/components/BottomBar.js`

#### 🎯 Funcionalidad
- Console de logs del sistema
- Historial de comandos
- Debug y diagnostics
- Mensajes de estado

#### 📝 Log Management
```javascript
state = {
    logs: [],
    showLogs: true,
    commandHistory: [],
    currentCommand: ''
}

addLog = (type, message) => {
    const logEntry = {
        id: Date.now(),
        type,    // 'info', 'warning', 'error'
        message,
        timestamp: new Date().toLocaleTimeString()
    };

    this.setState(prevState => ({
        logs: [...prevState.logs, logEntry].slice(-100) // Max 100 logs
    }));
}
```

## 🔄 Comunicación Entre Componentes

### 📡 Data Flow

#### Configuration Flow
```
LeftBar → API → ConfigManager → Backend State
  ↓
API Response → LeftBar State Update
  ↓
Props → ChatWindow (for provider/model info)
```

#### Chat Flow
```
ChatInput → onSendMessage() → ChatWindow
  ↓
ChatWindow → API → Chat Routes → LLM Provider
  ↓
SSE Stream → ChatWindow → UI Updates
```

#### System Monitoring Flow
```
RightBar → setInterval → updateStats()
  ↓
System Metrics → Display Components
```

### 🔗 Parent-Child Communication

#### Props Passing
- **MainContent** → **ChatWindow**: Global state
- **ChatWindow** → **ChatInput**: Message handlers
- **LeftBar** → Self: Configuration state

#### Event Bubbling
- **ChatInput** envía mensajes hacia arriba
- **API responses** fluyen hacia componentes específicos
- **Error states** se propagan al UI

## 🎛️ Estado y Gestión de Datos

### 🏪 State Management Pattern

#### Local Component State
Cada componente maneja su propio estado:

```javascript
// LeftBar - Estado de configuración
state = {
    providers: [],
    selectedProvider: null,
    models: [],
    selectedConfig: {},
    apiKeyVisible: false
}

// ChatWindow - Estado de chat
state = {
    messages: [],
    currentMessage: null,
    isStreaming: false,
    reasoningCollapsed: true
}

// RightBar - Estado del sistema
state = {
    cpu: 0,
    memory: 0,
    connections: 0,
    uptime: '00:00:00'
}
```

#### No Global State Management
- **Sin Redux/Context**: Cada componente es autónomo
- **API como fuente de verdad**: El backend mantiene el estado
- **Comunicación directa**: Props y callbacks

### 🔄 Lifecycle Management

#### Component Lifecycle
```javascript
// Patrón típico en todos los componentes
componentDidMount() {
    this.loadInitialData();
    this.setupEventListeners();
}

componentWillUnmount() {
    this.cleanupResources();
    this.removeEventListeners();
}
```

#### Resource Cleanup
```javascript
// ChatWindow - Cleanup de streaming
componentWillUnmount() {
    if (this.eventSource) {
        this.eventSource.close();
    }
}

// RightBar - Cleanup de intervals
componentWillUnmount() {
    if (this.interval) {
        clearInterval(this.interval);
    }
}
```

## 🚀 Performance Considerations

### ⚡ Optimizaciones

#### Event Source Management
- **Cleanup automático**: Close de SSE connections
- **Error handling**: Reconexión automática
- **Memory management**: Liberación de recursos

#### Update Batching
- **State updates**: Batch de actualizaciones React
- **DOM manipulation**: Minimal direct DOM access
- **Re-render optimization**: Key props para listas

#### Data Loading
- **Lazy loading**: Modelos se cargan por provider
- **Caching**: Providers se cachean en estado local
- **Error boundaries**: Prevención de crashes

## 🎭 Patrones de Diseño

### 🔧 Component Patterns

#### Composition over Inheritance
```javascript
// MainContent compone diferentes vistas
renderAIChatView() {
    return React.createElement(ChatWindow, {
        key: 'chat-window'
    });
}
```

#### Event Handler Pattern
```javascript
// ChatInput → ChatWindow communication
onSendMessage = (message) => {
    this.addUserMessage(message);
    this.startStreaming([...this.state.messages, userMessage]);
}
```

#### Conditional Rendering
```javascript
// Rendering condicional basado en estado
{this.state.reasoning && (
    React.createElement('details', {
        className: 'reasoning-section'
    }, reasoningContent)
)}
```

### 📱 Responsive Design

#### CSS Grid Layout
```css
.main-layout {
    display: grid;
    grid-template-columns: 320px 1fr 300px;
    grid-template-rows: 1fr;
    height: calc(100vh - 60px);
}
```

#### Collapsible Panels
- **LeftBar**: Configurable collapse
- **RightBar**: Hideable system monitor
- **BottomBar**: Expandible console
- **Reasoning**: Collapsible por defecto

## 🔐 Security Considerations

### 🛡️ Frontend Security

#### API Key Handling
- **No storage**: API keys no se almacenan en frontend
- **Masked input**: Inputs de API key ofuscados
- **Memory cleanup**: Keys no persisten en memory

#### Input Sanitization
- **Message content**: Sanitización básica
- **API requests**: Validación de datos
- **Error messages**: No exposición de detalles sensibles