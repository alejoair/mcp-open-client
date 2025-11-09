# Componentes del Frontend

## Referencia Completa de Componentes

Este documento proporciona una referencia detallada de todos los componentes del frontend, sus props, métodos y patrones de uso.

---

## 🎯 TerminalHeader

### 📄 Ubicación
`mcp_open_client/ui/components/TerminalHeader.js`

### 🏗️ Clase
```javascript
class TerminalHeader extends React.Component
```

### 🎯 Propósito
Header principal que simula una ventana de terminal con controles de ventana estilo macOS.

### 📊 Props
- **Ninguna**: Componente autónomo sin props

### 🔧 Estado
```javascript
// Sin estado propio - componente puramente visual
```

### 🎨 Rendering
```javascript
render() {
    return React.createElement('div', {
        className: 'terminal-header'
    }, [
        // Traffic lights (botones de ventana)
        React.createElement('div', {
            className: 'traffic-lights'
        }),

        // Título
        React.createElement('div', {
            className: 'window-title'
        }, 'MCP Open Client'),

        // Spacer para centrar el título
        React.createElement('div', {
            className: 'spacer'
        })
    ]);
}
```

### 🎛️ Estilos Aplicados
- **Traffic lights**: Círculos rojo, amarillo, verde
- **Window title**: Texto centrado
- **Background**: Terminal dark theme
- **Height**: 40px fijo

---

## ⚙️ LeftBar - Panel de Configuración

### 📄 Ubicación
`mcp_open_client/ui/components/LeftBar.js`

### 🏗️ Clase
```javascript
class LeftBar extends React.Component
```

### 🎯 Propósito
Panel de configuración principal para gestión de providers LLM, API keys y selección de modelos.

### 📊 Props
- **Ninguna**: Componente autónomo que se conecta directamente a la API

### 🔧 Estado Detallado
```javascript
state = {
    providers: [],              // Array de providers disponibles
    selectedProvider: null,     // Provider actualmente seleccionado
    models: [],                // Array de modelos del provider seleccionado
    selectedConfig: {          // Configuración actual
        provider_id: '',
        main_model: '',
        small_model: ''
    },
    apiKeyVisible: false,      // Visibilidad del modal de API key
    currentApiKey: '',         // Valor temporal del API key
    loading: false,            // Estado de carga general
    modelLoading: false,       // Estado de carga específico para modelos
    connectionStatus: 'disconnected', // Estado de conexión
    lastError: null            // Último error ocurrido
}
```

### 🔄 Métodos del Ciclo de Vida

#### componentDidMount()
```javascript
async componentDidMount() {
    await this.loadProviders();
    await this.loadCurrentConfig();
    this.setState({ loading: false });
}
```

#### componentWillUnmount()
```javascript
componentWillUnmount() {
    // Cleanup de timers o event listeners si los hubiera
}
```

### 🌐 Métodos de API

#### loadProviders()
```javascript
async loadProviders() {
    try {
        const response = await fetch('/api/config/providers');
        const data = await response.json();

        this.setState({
            providers: data.providers || [],
            connectionStatus: 'connected'
        });
    } catch (error) {
        this.setState({
            lastError: 'Failed to load providers',
            connectionStatus: 'error'
        });
    }
}
```

#### loadModels(providerId)
```javascript
async loadModels(providerId) {
    this.setState({ modelLoading: true });

    try {
        const response = await fetch(`/api/config/providers/${providerId}/models`);
        const data = await response.json();

        this.setState({
            models: data.models || [],
            modelLoading: false
        });
    } catch (error) {
        this.setState({
            models: [],
            modelLoading: false,
            lastError: 'Failed to load models'
        });
    }
}
```

#### saveApiKey(providerId, apiKey)
```javascript
async saveApiKey(providerId, apiKey) {
    try {
        const response = await fetch(`/api/config/providers/${providerId}/api-key`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ api_key: apiKey })
        });

        if (response.ok) {
            await this.loadProviders(); // Reload para actualizar estado
            this.setState({ apiKeyVisible: false, currentApiKey: '' });
        }
    } catch (error) {
        this.setState({ lastError: 'Failed to save API key' });
    }
}
```

#### updateSelectedConfig(config)
```javascript
async updateSelectedConfig(config) {
    try {
        const response = await fetch('/api/config/selected', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(config)
        });

        if (response.ok) {
            this.setState({ selectedConfig: config });
        }
    } catch (error) {
        this.setState({ lastError: 'Failed to update configuration' });
    }
}
```

### 🎨 Métodos de Renderizado

#### renderProviderSelection()
```javascript
renderProviderSelection() {
    const { providers, selectedProvider } = this.state;

    return React.createElement(antd.Select, {
        value: selectedProvider?.id,
        placeholder: 'Select LLM Provider',
        onChange: this.handleProviderChange,
        style: { width: '100%' }
    }, providers.map(provider =>
        React.createElement(antd.Select.Option, {
            key: provider.id,
            value: provider.id
        }, `${provider.name} ${provider.has_api_key ? '✓' : '⚠️'}`)
    ));
}
```

#### renderModelSelection()
```javascript
renderModelSelection() {
    const { models, selectedConfig, modelLoading } = this.state;

    if (!models.length) return null;

    return React.createElement('div', {
        className: 'model-selection'
    }, [
        React.createElement('label', { key: 'label' }, 'Main Model:'),
        React.createElement(antd.Select, {
            key: 'select',
            value: selectedConfig.main_model,
            loading: modelLoading,
            onChange: this.handleMainModelChange,
            style: { width: '100%' }
        }, models.map(model =>
            React.createElement(antd.Select.Option, {
                key: model.id,
                value: model.id
            }, model.name)
        ))
    ]);
}
```

#### renderApiKeyModal()
```javascript
renderApiKeyModal() {
    const { apiKeyVisible, currentApiKey, selectedProvider } = this.state;

    return React.createElement(antd.Modal, {
        title: `Configure API Key - ${selectedProvider?.name}`,
        visible: apiKeyVisible,
        onOk: this.handleApiKeySubmit,
        onCancel: this.handleApiKeyCancel
    }, [
        React.createElement(antd.Input.Password, {
            key: 'input',
            value: currentApiKey,
            onChange: this.handleApiKeyChange,
            placeholder: 'Enter your API key...'
        })
    ]);
}
```

### 🎛️ Event Handlers
```javascript
handleProviderChange = async (providerId) => {
    const provider = this.state.providers.find(p => p.id === providerId);
    this.setState({ selectedProvider: provider });

    if (provider?.has_api_key) {
        await this.loadModels(providerId);
    }
}

handleMainModelChange = (modelId) => {
    const updatedConfig = {
        ...this.state.selectedConfig,
        provider_id: this.state.selectedProvider.id,
        main_model: modelId
    };

    this.updateSelectedConfig(updatedConfig);
}

handleApiKeySubmit = () => {
    const { selectedProvider, currentApiKey } = this.state;
    if (selectedProvider && currentApiKey.trim()) {
        this.saveApiKey(selectedProvider.id, currentApiKey.trim());
    }
}
```

---

## 💬 MainContent - Orquestador Central

### 📄 Ubicación
`mcp_open_client/ui/components/MainContent.js`

### 🏗️ Clase
```javascript
class MainContent extends React.Component
```

### 🎯 Propósito
Orquesta las vistas principales de la aplicación y actúa como contenedor para ChatWindow.

### 📊 Props
- **Ninguna**: Componente autónomo

### 🔧 Estado
```javascript
state = {
    currentView: 'chat' // 'welcome' | 'chat'
}
```

### 🎨 Métodos de Renderizado

#### renderWelcomeView()
```javascript
renderWelcomeView() {
    return React.createElement('div', {
        className: 'welcome-view'
    }, [
        React.createElement('h1', { key: 'title' }, 'Welcome to MCP Open Client'),
        React.createElement('p', { key: 'subtitle' }, 'Universal client for LLM providers'),

        // Feature cards
        React.createElement('div', {
            key: 'features',
            className: 'feature-grid'
        }, this.renderFeatureCards())
    ]);
}
```

#### renderAIChatView()
```javascript
renderAIChatView() {
    return React.createElement('div', {
        className: 'ai-chat-view',
        style: {
            height: '100%',
            padding: '16px'
        }
    }, [
        React.createElement(ChatWindow, {
            key: 'chat-window'
        })
    ]);
}
```

#### renderFeatureCards()
```javascript
renderFeatureCards() {
    const features = [
        {
            title: 'Multi-Provider Support',
            description: 'Connect to OpenAI, Anthropic, Cerebras and more',
            icon: '🔗'
        },
        // ... more features
    ];

    return features.map(feature =>
        this.renderFeatureCard(feature)
    );
}
```

### 🎛️ Navigation
```javascript
// Vista principal que determina qué mostrar
render() {
    const { currentView } = this.state;

    return React.createElement('div', {
        className: 'main-content'
    }, [
        React.createElement('div', {
            key: 'content-area'
        },
            currentView === 'welcome' ?
                this.renderWelcomeView() :
                this.renderAIChatView()
        )
    ]);
}
```

---

## 🤖 ChatWindow - Interface Principal de Chat

### 📄 Ubicación
`mcp_open_client/ui/components/ChatWindow.js`

### 🏗️ Clase
```javascript
class ChatWindow extends React.Component
```

### 🎯 Propósito
Interface principal de chat con soporte completo para streaming, tool calls y separación de reasoning/content.

### 📊 Props
- **Ninguna**: Componente autónomo que gestiona todo el chat

### 🔧 Estado Completo
```javascript
state = {
    messages: [],              // Array de mensajes del chat
    isStreaming: false,        // Estado de streaming activo
    currentMessage: null,      // Mensaje siendo construido en streaming
    reasoningCollapsed: true,  // Estado del panel de reasoning
    error: null,              // Último error ocurrido
    eventSource: null,        // Conexión SSE actual
    connectionStatus: 'ready', // 'ready' | 'connecting' | 'streaming' | 'error'
    streamingStats: {         // Estadísticas del streaming actual
        startTime: null,
        chunks: 0,
        totalChars: 0
    }
}
```

### 🌊 Streaming Management

#### startStreaming(messages)
```javascript
startStreaming = async (messages) => {
    this.setState({
        isStreaming: true,
        connectionStatus: 'connecting',
        streamingStats: {
            startTime: Date.now(),
            chunks: 0,
            totalChars: 0
        }
    });

    try {
        const response = await fetch('/api/chat/completions/stream', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                messages: messages,
                max_tokens: 1000,
                temperature: 0.7
            })
        });

        this.handleStreamingResponse(response);
    } catch (error) {
        this.handleStreamingError(error);
    }
}
```

#### handleStreamingResponse(response)
```javascript
handleStreamingResponse = (response) => {
    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    this.setState({ connectionStatus: 'streaming' });

    const processStream = async () => {
        try {
            while (true) {
                const { value, done } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value);
                const lines = chunk.split('\n');

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const data = line.slice(6);
                        if (data === '[DONE]') {
                            this.completeStreaming();
                            return;
                        }

                        try {
                            const parsedData = JSON.parse(data);
                            this.handleStreamEvent(parsedData);
                        } catch (e) {
                            // Skip invalid JSON
                        }
                    }
                }
            }
        } catch (error) {
            this.handleStreamingError(error);
        }
    };

    processStream();
}
```

#### handleStreamEvent(data)
```javascript
handleStreamEvent = (data) => {
    const { streamingStats } = this.state;

    // Update stats
    this.setState({
        streamingStats: {
            ...streamingStats,
            chunks: streamingStats.chunks + 1,
            totalChars: streamingStats.totalChars + (data.content?.length || 0)
        }
    });

    switch (data.type) {
        case 'start':
            this.handleStreamStart(data);
            break;
        case 'reasoning_chunk':
            this.updateReasoning(data);
            break;
        case 'content_chunk':
            this.updateContent(data);
            break;
        case 'tool_call_start':
            this.startToolCall(data);
            break;
        case 'tool_call_arguments':
            this.updateToolCallArguments(data);
            break;
        case 'tool_execution_start':
            this.startToolExecution(data);
            break;
        case 'tool_execution_complete':
            this.completeToolExecution(data);
            break;
        case 'tool_execution_error':
            this.handleToolExecutionError(data);
            break;
        case 'complete':
            this.handleStreamComplete(data);
            break;
        case 'error':
            this.handleStreamingError(new Error(data.error));
            break;
    }
}
```

### 🛠️ Tool Call Management

#### startToolCall(data)
```javascript
startToolCall = (data) => {
    const { currentMessage } = this.state;
    const { tool_call_id, function_name } = data;

    if (!currentMessage) return;

    const newToolCall = {
        id: tool_call_id,
        function: {
            name: function_name,
            arguments: ''
        },
        status: 'building', // 'building' | 'executing' | 'completed' | 'error'
        result: null
    };

    const updatedMessage = {
        ...currentMessage,
        tool_calls: [...(currentMessage.tool_calls || []), newToolCall]
    };

    this.setState({ currentMessage: updatedMessage });
    this.updateMessagesArray(updatedMessage);
}
```

#### updateToolCallArguments(data)
```javascript
updateToolCallArguments = (data) => {
    const { currentMessage } = this.state;
    const { tool_call_id, arguments: newArgs, full_arguments } = data;

    if (!currentMessage?.tool_calls) return;

    const updatedToolCalls = currentMessage.tool_calls.map(toolCall =>
        toolCall.id === tool_call_id
            ? { ...toolCall, function: { ...toolCall.function, arguments: full_arguments } }
            : toolCall
    );

    const updatedMessage = {
        ...currentMessage,
        tool_calls: updatedToolCalls
    };

    this.setState({ currentMessage: updatedMessage });
    this.updateMessagesArray(updatedMessage);
}
```

#### completeToolExecution(data)
```javascript
completeToolExecution = (data) => {
    const { currentMessage } = this.state;
    const { tool_result } = data;

    if (!currentMessage?.tool_calls) return;

    const updatedToolCalls = currentMessage.tool_calls.map(toolCall =>
        toolCall.id === tool_result.tool_call_id
            ? {
                ...toolCall,
                status: tool_result.status,
                result: tool_result
              }
            : toolCall
    );

    const updatedMessage = {
        ...currentMessage,
        tool_calls: updatedToolCalls
    };

    this.setState({ currentMessage: updatedMessage });
    this.updateMessagesArray(updatedMessage);
}
```

### 🎨 Rendering Methods

#### renderMessage(message)
```javascript
renderMessage = (message) => {
    return React.createElement('div', {
        key: message.id,
        className: `chat-message ${message.role}`
    }, [
        this.renderMessageHeader(message),
        this.renderMessageContent(message),
        message.reasoning && this.renderReasoning(message),
        message.tool_calls && this.renderToolCalls(message.tool_calls)
    ]);
}
```

#### renderReasoning(message)
```javascript
renderReasoning = (message) => {
    const { reasoningCollapsed } = this.state;

    return React.createElement('details', {
        className: 'reasoning-section',
        open: !reasoningCollapsed
    }, [
        React.createElement('summary', {
            key: 'summary',
            onClick: this.toggleReasoning
        }, '🧠 Model Reasoning'),

        React.createElement('div', {
            key: 'content',
            className: 'reasoning-content'
        }, message.reasoning)
    ]);
}
```

#### renderToolCalls(toolCalls)
```javascript
renderToolCalls = (toolCalls) => {
    return React.createElement('div', {
        className: 'tool-calls-section'
    }, toolCalls.map(toolCall =>
        React.createElement('div', {
            key: toolCall.id,
            className: `tool-call ${toolCall.status}`
        }, [
            this.renderToolCallHeader(toolCall),
            this.renderToolCallArguments(toolCall),
            toolCall.result && this.renderToolCallResult(toolCall.result)
        ])
    ));
}
```

### 🎛️ User Interaction

#### onSendMessage(message)
```javascript
onSendMessage = (message) => {
    const userMessage = {
        id: `user-${Date.now()}`,
        role: 'user',
        content: message,
        timestamp: new Date()
    };

    const updatedMessages = [...this.state.messages, userMessage];

    this.setState({
        messages: updatedMessages,
        error: null
    });

    this.startStreaming(updatedMessages);
}
```

#### toggleReasoning()
```javascript
toggleReasoning = () => {
    this.setState(prevState => ({
        reasoningCollapsed: !prevState.reasoningCollapsed
    }));
}
```

---

## 📝 ChatInput - Input de Mensajes

### 📄 Ubicación
`mcp_open_client/ui/components/ChatInput.js`

### 🏗️ Clase
```javascript
class ChatInput extends React.Component
```

### 🎯 Propósito
Input especializado para mensajes de chat con soporte para multiline y historial de comandos.

### 📊 Props
```javascript
propTypes = {
    onSendMessage: PropTypes.func.isRequired, // Callback para enviar mensaje
    disabled: PropTypes.bool,                 // Estado deshabilitado
    placeholder: PropTypes.string             // Placeholder text
}
```

### 🔧 Estado
```javascript
state = {
    message: '',              // Contenido actual del mensaje
    commandHistory: [],       // Historial de mensajes enviados
    historyIndex: -1,         // Índice actual en el historial
    isComposing: false        // Estado de composición (IME)
}
```

### ⌨️ Input Handling

#### handleKeyDown(event)
```javascript
handleKeyDown = (event) => {
    if (event.key === 'Enter' && !event.shiftKey && !this.state.isComposing) {
        event.preventDefault();
        this.handleSend();
    } else if (event.key === 'ArrowUp' && event.ctrlKey) {
        event.preventDefault();
        this.navigateHistory('up');
    } else if (event.key === 'ArrowDown' && event.ctrlKey) {
        event.preventDefault();
        this.navigateHistory('down');
    }
}

handleSend = () => {
    const { message } = this.state;
    const trimmedMessage = message.trim();

    if (!trimmedMessage) return;

    // Agregar al historial
    this.addToHistory(trimmedMessage);

    // Enviar mensaje
    this.props.onSendMessage(trimmedMessage);

    // Limpiar input
    this.setState({
        message: '',
        historyIndex: -1
    });
}
```

#### Command History Management
```javascript
addToHistory = (message) => {
    this.setState(prevState => ({
        commandHistory: [message, ...prevState.commandHistory.slice(0, 19)] // Max 20 items
    }));
}

navigateHistory = (direction) => {
    const { commandHistory, historyIndex } = this.state;
    let newIndex = historyIndex;

    if (direction === 'up' && newIndex < commandHistory.length - 1) {
        newIndex++;
    } else if (direction === 'down' && newIndex > -1) {
        newIndex--;
    }

    const message = newIndex === -1 ? '' : commandHistory[newIndex];

    this.setState({
        historyIndex: newIndex,
        message: message
    });
}
```

### 🎨 Rendering
```javascript
render() {
    const { message } = this.state;
    const { disabled, placeholder } = this.props;

    return React.createElement('div', {
        className: 'chat-input-container'
    }, [
        React.createElement('textarea', {
            key: 'input',
            value: message,
            onChange: this.handleChange,
            onKeyDown: this.handleKeyDown,
            onCompositionStart: () => this.setState({ isComposing: true }),
            onCompositionEnd: () => this.setState({ isComposing: false }),
            placeholder: placeholder || 'Type a message...',
            disabled: disabled,
            className: 'chat-input',
            rows: 1
        }),

        React.createElement('button', {
            key: 'send',
            onClick: this.handleSend,
            disabled: disabled || !message.trim(),
            className: 'send-button'
        }, '➤')
    ]);
}
```

---

## 📊 RightBar - Sistema Monitor

### 📄 Ubicación
`mcp_open_client/ui/components/RightBar.js`

### 🏗️ Clase
```javascript
class RightBar extends React.Component
```

### 🎯 Propósito
Monitor del sistema que muestra estadísticas simuladas de rendimiento y estado de la aplicación.

### 📊 Props
- **Ninguna**: Componente autónomo con datos simulados

### 🔧 Estado
```javascript
state = {
    cpu: 0,                   // Porcentaje de CPU (simulado)
    memory: 0,                // Porcentaje de memoria (simulado)
    connections: 0,           // Número de conexiones activas
    uptime: '00:00:00',      // Tiempo de funcionamiento
    networkActivity: {        // Actividad de red simulada
        incoming: 0,
        outgoing: 0
    },
    processes: [],           // Lista de procesos simulados
    collapsed: false         // Estado del panel
}
```

### ⏰ Data Simulation

#### componentDidMount()
```javascript
componentDidMount() {
    this.startTime = Date.now();
    this.interval = setInterval(this.updateStats, 2000);
    this.updateStats(); // Initial update
}

componentWillUnmount() {
    if (this.interval) {
        clearInterval(this.interval);
    }
}
```

#### updateStats()
```javascript
updateStats = () => {
    const uptime = this.calculateUptime();

    this.setState({
        cpu: this.generateCPUUsage(),
        memory: this.generateMemoryUsage(),
        connections: Math.floor(Math.random() * 10) + 1,
        uptime: uptime,
        networkActivity: {
            incoming: Math.floor(Math.random() * 1000),
            outgoing: Math.floor(Math.random() * 500)
        },
        processes: this.generateProcessList()
    });
}

generateCPUUsage = () => {
    // Simulación más realista de uso de CPU
    const base = Math.random() * 30; // Base load
    const spike = Math.random() > 0.8 ? Math.random() * 40 : 0; // Occasional spike
    return Math.min(Math.floor(base + spike), 100);
}

calculateUptime = () => {
    const elapsed = Date.now() - this.startTime;
    const hours = Math.floor(elapsed / (1000 * 60 * 60));
    const minutes = Math.floor((elapsed % (1000 * 60 * 60)) / (1000 * 60));
    const seconds = Math.floor((elapsed % (1000 * 60)) / 1000);

    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
}
```

### 🎨 Rendering Components

#### renderSystemStats()
```javascript
renderSystemStats = () => {
    const { cpu, memory, connections, uptime } = this.state;

    return React.createElement('div', {
        className: 'system-stats'
    }, [
        React.createElement('div', {
            key: 'cpu',
            className: 'stat-item'
        }, [
            React.createElement('label', { key: 'label' }, 'CPU:'),
            React.createElement('div', {
                key: 'value',
                className: 'stat-value'
            }, `${cpu}%`),
            React.createElement('div', {
                key: 'bar',
                className: 'stat-bar'
            }, React.createElement('div', {
                className: 'stat-fill',
                style: { width: `${cpu}%` }
            }))
        ]),
        // Similar structure for memory, connections, uptime
    ]);
}
```

#### renderNetworkActivity()
```javascript
renderNetworkActivity = () => {
    const { networkActivity } = this.state;

    return React.createElement('div', {
        className: 'network-section'
    }, [
        React.createElement('h4', { key: 'title' }, '🌐 Network'),
        React.createElement('div', {
            key: 'stats',
            className: 'network-stats'
        }, [
            React.createElement('div', {
                key: 'in'
            }, `↓ ${networkActivity.incoming} KB/s`),
            React.createElement('div', {
                key: 'out'
            }, `↑ ${networkActivity.outgoing} KB/s`)
        ])
    ]);
}
```

---

## 📺 BottomBar - Console Panel

### 📄 Ubicación
`mcp_open_client/ui/components/BottomBar.js`

### 🏗️ Clase
```javascript
class BottomBar extends React.Component
```

### 🎯 Propósito
Panel de console que muestra logs del sistema, historial de comandos y debugging information.

### 📊 Props
- **Ninguna**: Componente autónomo

### 🔧 Estado
```javascript
state = {
    logs: [],                 // Array de logs
    showLogs: true,          // Visibilidad del panel
    commandHistory: [],      // Historial de comandos
    currentCommand: '',      // Comando actual en input
    logLevel: 'all',         // Filtro de nivel de logs
    collapsed: false         // Estado colapsado
}
```

### 📝 Log Management

#### addLog(type, message)
```javascript
addLog = (type, message) => {
    const logEntry = {
        id: Date.now(),
        type: type,              // 'info', 'warning', 'error', 'success'
        message: message,
        timestamp: new Date().toISOString(),
        source: 'system'
    };

    this.setState(prevState => ({
        logs: [...prevState.logs, logEntry].slice(-100) // Keep last 100 logs
    }));

    // Auto-scroll to bottom
    setTimeout(() => {
        const logsContainer = document.querySelector('.logs-container');
        if (logsContainer) {
            logsContainer.scrollTop = logsContainer.scrollHeight;
        }
    }, 0);
}

clearLogs = () => {
    this.setState({ logs: [] });
}

filterLogsByLevel = (logs, level) => {
    if (level === 'all') return logs;
    return logs.filter(log => log.type === level);
}
```

### 🎨 Rendering

#### renderLogEntry(log)
```javascript
renderLogEntry = (log) => {
    const iconMap = {
        info: 'ℹ️',
        warning: '⚠️',
        error: '❌',
        success: '✅'
    };

    return React.createElement('div', {
        key: log.id,
        className: `log-entry log-${log.type}`
    }, [
        React.createElement('span', {
            key: 'icon',
            className: 'log-icon'
        }, iconMap[log.type]),

        React.createElement('span', {
            key: 'timestamp',
            className: 'log-timestamp'
        }, new Date(log.timestamp).toLocaleTimeString()),

        React.createElement('span', {
            key: 'message',
            className: 'log-message'
        }, log.message)
    ]);
}
```

#### renderCommandInput()
```javascript
renderCommandInput = () => {
    const { currentCommand } = this.state;

    return React.createElement('div', {
        className: 'command-input-section'
    }, [
        React.createElement('span', {
            key: 'prompt',
            className: 'command-prompt'
        }, '$ '),

        React.createElement('input', {
            key: 'input',
            type: 'text',
            value: currentCommand,
            onChange: this.handleCommandChange,
            onKeyDown: this.handleCommandKeyDown,
            className: 'command-input',
            placeholder: 'Enter command...'
        })
    ]);
}
```

### 🎛️ Component Integration

#### Window-scoped Export Pattern
Todos los componentes siguen este patrón:

```javascript
// Al final de cada archivo
window.ComponentName = ComponentName;
```

#### Usage in index.html
```javascript
// Instanciación de componentes
const terminalHeaderElement = React.createElement(TerminalHeader);
const leftBarElement = React.createElement(LeftBar);
const mainContentElement = React.createElement(MainContent);
const rightBarElement = React.createElement(RightBar);
const bottomBarElement = React.createElement(BottomBar);

// Renderizado
ReactDOM.render(terminalHeaderElement, document.getElementById('terminal-header'));
ReactDOM.render(leftBarElement, document.getElementById('left-bar'));
ReactDOM.render(mainContentElement, document.getElementById('main-content'));
ReactDOM.render(rightBarElement, document.getElementById('right-bar'));
ReactDOM.render(bottomBarElement, document.getElementById('bottom-bar'));
```