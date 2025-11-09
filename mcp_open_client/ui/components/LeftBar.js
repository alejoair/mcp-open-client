/**
 * LeftBar Component
 * Collapsible sidebar with accordion navigation
 */

class LeftBar extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            activeKeys: ['1'], // Default open panel
            // Configuration state
            providers: [],
            selectedProvider: '',
            providersLoading: false,
            apiKeyInput: '',
            apiKeyVisible: false,
            mainModel: '',
            smallModel: '',
            maxTokens: 1000,
            availableModels: [],
            modelsLoading: false,
            configLoading: false,
            // UI feedback state
            apiKeySubmitting: false,
            configSaving: false,
            lastOperationStatus: null, // 'success', 'error', null
            operationMessage: ''
        };
    }

    componentDidMount() {
        this.loadConfiguration();
    }

    onAccordionChange = (key) => {
        this.setState({
            activeKeys: key
        });
    }

    // Configuration API methods
    loadConfiguration = async () => {
        this.setState({ configLoading: true });
        try {
            // Load current configuration
            const configResponse = await fetch('/api/config/');
            if (configResponse.ok) {
                const config = await configResponse.json();
                console.log('Current config loaded:', config);
                const selectedConfig = config.selected_configuration || {};
                this.setState({
                    selectedProvider: selectedConfig.provider_id || '',
                    mainModel: selectedConfig.main_model || '',
                    smallModel: selectedConfig.small_model || '',
                    maxTokens: selectedConfig.max_tokens || 1000
                });
            }

            // Load providers
            const providersResponse = await fetch('/api/config/providers');
            if (providersResponse.ok) {
                const providersData = await providersResponse.json();
                console.log('Providers loaded:', providersData.providers?.length || 0);
                this.setState({ providers: providersData.providers || [] });
            }

            // Load models for selected provider after state has been updated
            if (this.state.selectedProvider) {
                console.log('Loading models for provider:', this.state.selectedProvider);
                await this.loadModelsForProvider(this.state.selectedProvider);

                // Validate that selected models exist in available models
                await this.validateSelectedModels();
            }
        } catch (error) {
            console.error('Failed to load configuration:', error);
        } finally {
            this.setState({ configLoading: false });
        }
    }

    loadModelsForProvider = async (providerId) => {
        this.setState({ modelsLoading: true });
        try {
            console.log('Loading models for provider:', providerId);
            const response = await fetch(`/api/config/providers/${providerId}/models`);
            if (response.ok) {
                const data = await response.json();
                console.log('Models loaded:', data.models?.length || 0, 'for provider:', providerId);
                console.log('Models data received:', data.models);
                this.setState({ availableModels: data.models || [] });

                // Additional debugging to check state after update
                setTimeout(() => {
                    console.log('Available models in state:', this.state.availableModels);
                    console.log('Total models count:', this.state.availableModels.length);
                }, 100);
            } else {
                console.error('Failed to fetch models - response not ok:', response.status);
                this.setState({ availableModels: [] });
            }
        } catch (error) {
            console.error('Failed to load models:', error);
            this.setState({ availableModels: [] });
        } finally {
            this.setState({ modelsLoading: false });
        }
    }

    validateSelectedModels = async () => {
        const { availableModels, mainModel, smallModel } = this.state;

        // Check if selected models exist in available models
        const mainExists = availableModels.some(model => model.id === mainModel);
        const smallExists = availableModels.some(model => model.id === smallModel);

        let needsUpdate = false;
        let updates = {};

        // Clear invalid main model selection
        if (!mainExists && mainModel) {
            console.log('Clearing invalid main model:', mainModel);
            this.setState({ mainModel: '' });
            updates.main_model = '';
            needsUpdate = true;
        }

        // Clear invalid small model selection
        if (!smallExists && smallModel) {
            console.log('Clearing invalid small model:', smallModel);
            this.setState({ smallModel: '' });
            updates.small_model = '';
            needsUpdate = true;
        }

        // Update backend if needed
        if (needsUpdate) {
            try {
                await fetch('/api/config/selected', {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(updates)
                });
            } catch (error) {
                console.error('Failed to clear invalid models:', error);
            }
        }
    }

    onProviderChange = async (providerId) => {
        console.log('Provider changed to:', providerId);
        this.setState({
            selectedProvider: providerId,
            mainModel: '',
            smallModel: '',
            availableModels: []
        });

        // Load models for new provider
        console.log('About to load models for provider:', providerId);
        await this.loadModelsForProvider(providerId);

        // Update backend
        try {
            const response = await fetch('/api/config/selected', {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ provider_id: providerId })
            });

            if (response.ok) {
                console.log('Provider updated in backend:', providerId);
            } else {
                console.error('Failed to update provider in backend');
            }
        } catch (error) {
            console.error('Failed to update provider:', error);
        }
    }

    onModelChange = async (modelType, modelId) => {
        // Update local state
        if (modelType === 'main') {
            this.setState({ mainModel: modelId });
        } else if (modelType === 'small') {
            this.setState({ smallModel: modelId });
        }

        // Update backend
        try {
            const updateData = {};
            if (modelType === 'main') {
                updateData.main_model = modelId;
            } else if (modelType === 'small') {
                updateData.small_model = modelId;
            }

            await fetch('/api/config/selected', {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(updateData)
            });
            console.log(`Selected ${modelType} model updated to:`, modelId);
        } catch (error) {
            console.error(`Failed to update ${modelType} model:`, error);
        }
    }

    onMaxTokensChange = (value) => {
        // Validate max_tokens value
        const numValue = parseInt(value);
        if (!isNaN(numValue) && numValue > 0 && numValue <= 32000) {
            this.setState({ maxTokens: numValue });
        }
    }

    onApiKeySubmit = async () => {
        if (!this.state.apiKeyInput || !this.state.selectedProvider) return;

        this.setState({
            apiKeySubmitting: true,
            lastOperationStatus: null,
            operationMessage: 'Configurando API key...'
        });

        try {
            console.log('Submitting API key for provider:', this.state.selectedProvider);
            const response = await fetch(`/api/config/providers/${this.state.selectedProvider}/api-key`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    provider_id: this.state.selectedProvider,
                    api_key: this.state.apiKeyInput
                })
            });

            if (response.ok) {
                const result = await response.json();
                console.log('API key updated successfully:', result.message);

                // Clear input and hide password
                this.setState({
                    apiKeyInput: '',
                    apiKeyVisible: false,
                    lastOperationStatus: 'success',
                    operationMessage: 'API key configurada correctamente. Cargando modelos...'
                });

                // Reload entire configuration to get updated models and config
                setTimeout(async () => {
                    await this.loadConfiguration();
                    this.setState({
                        operationMessage: 'Configuración actualizada exitosamente',
                        lastOperationStatus: 'success'
                    });
                    console.log('Configuration reloaded after API key update');
                    // Clear success message after 3 seconds
                    setTimeout(() => {
                        this.setState({ lastOperationStatus: null, operationMessage: '' });
                    }, 3000);
                }, 500);
            } else {
                const error = await response.json();
                const errorMsg = error.detail || 'Error desconocido al configurar API key';
                console.error('Failed to update API key:', errorMsg);
                this.setState({
                    lastOperationStatus: 'error',
                    operationMessage: errorMsg
                });
                // Clear error message after 5 seconds
                setTimeout(() => {
                    this.setState({ lastOperationStatus: null, operationMessage: '' });
                }, 5000);
            }
        } catch (error) {
            console.error('Failed to update API key:', error);
            this.setState({
                lastOperationStatus: 'error',
                operationMessage: 'Error de conexión al configurar API key'
            });
            // Clear error message after 5 seconds
            setTimeout(() => {
                this.setState({ lastOperationStatus: null, operationMessage: '' });
            }, 5000);
        } finally {
            this.setState({ apiKeySubmitting: false });
        }
    }

    onSaveConfiguration = async () => {
        if (!this.state.selectedProvider) return;

        this.setState({
            configSaving: true,
            lastOperationStatus: null,
            operationMessage: 'Guardando configuración...'
        });

        try {
            const updateData = {
                provider_id: this.state.selectedProvider,
                main_model: this.state.mainModel || '',
                small_model: this.state.smallModel || '',
                max_tokens: this.state.maxTokens
            };

            console.log('Saving configuration:', updateData);
            const response = await fetch('/api/config/selected', {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(updateData)
            });

            if (response.ok) {
                const result = await response.json();
                console.log('Configuration saved successfully:', result.message);

                this.setState({
                    lastOperationStatus: 'success',
                    operationMessage: 'Configuración guardada exitosamente'
                });

                // Clear success message after 3 seconds
                setTimeout(() => {
                    this.setState({ lastOperationStatus: null, operationMessage: '' });
                }, 3000);
            } else {
                const error = await response.json();
                const errorMsg = error.detail || 'Error desconocido al guardar configuración';
                console.error('Failed to save configuration:', errorMsg);
                this.setState({
                    lastOperationStatus: 'error',
                    operationMessage: errorMsg
                });
                // Clear error message after 5 seconds
                setTimeout(() => {
                    this.setState({ lastOperationStatus: null, operationMessage: '' });
                }, 5000);
            }
        } catch (error) {
            console.error('Failed to save configuration:', error);
            this.setState({
                lastOperationStatus: 'error',
                operationMessage: 'Error de conexión al guardar configuración'
            });
            // Clear error message after 5 seconds
            setTimeout(() => {
                this.setState({ lastOperationStatus: null, operationMessage: '' });
            }, 5000);
        } finally {
            this.setState({ configSaving: false });
        }
    }

    render() {
        const { collapsed = false, onToggle } = this.props;
        const { activeKeys } = this.state;

        // Accordion items following Rayflow pattern
        const accordionItems = [
            {
                key: '1',
                label: 'Config',
                children: React.createElement('div', {
                    className: 'accordion-content',
                    style: { padding: '8px' }
                }, [
                    // Provider Selection
                    React.createElement('div', { key: 'provider-section', style: { marginBottom: '16px' } }, [
                        React.createElement('label', {
                            key: 'provider-label',
                            style: {
                                display: 'block',
                                color: 'var(--terminal-cyan)',
                                fontSize: '12px',
                                fontWeight: '600',
                                marginBottom: '6px'
                            }
                        }, 'Provider:'),
                        React.createElement(antd.Select, {
                            key: 'provider-select',
                            value: this.state.selectedProvider,
                            onChange: this.onProviderChange,
                            loading: this.state.providersLoading,
                            placeholder: 'Select Provider',
                            style: {
                                width: '100%',
                                fontFamily: 'inherit'
                            },
                            size: 'small',
                            options: this.state.providers.map(provider => ({
                                label: provider.name,
                                value: provider.id
                            }))
                        })
                    ]),

                    // API Key Section
                    this.state.selectedProvider && React.createElement('div', { key: 'apikey-section', style: { marginBottom: '16px' } }, [
                        React.createElement('label', {
                            key: 'apikey-label',
                            style: {
                                display: 'block',
                                color: 'var(--terminal-cyan)',
                                fontSize: '12px',
                                fontWeight: '600',
                                marginBottom: '6px'
                            }
                        }, 'API Key:'),
                        React.createElement('div', { key: 'apikey-group', style: { display: 'flex', gap: '4px' } }, [
                            React.createElement(antd.Input, {
                                key: 'apikey-input',
                                value: this.state.apiKeyInput,
                                onChange: (e) => this.setState({ apiKeyInput: e.target.value }),
                                type: this.state.apiKeyVisible ? 'text' : 'password',
                                placeholder: 'Enter API Key',
                                size: 'small',
                                style: {
                                    flex: 1,
                                    fontFamily: 'inherit'
                                }
                            }),
                            React.createElement(antd.Button, {
                                key: 'apikey-toggle',
                                size: 'small',
                                icon: this.state.apiKeyVisible ? '🙈' : '👁️',
                                onClick: () => this.setState({ apiKeyVisible: !this.state.apiKeyVisible }),
                                style: { fontFamily: 'inherit' }
                            }),
                            React.createElement(antd.Button, {
                                key: 'apikey-submit',
                                size: 'small',
                                type: 'primary',
                                onClick: this.onApiKeySubmit,
                                disabled: !this.state.apiKeyInput || this.state.apiKeySubmitting,
                                loading: this.state.apiKeySubmitting,
                                style: { fontFamily: 'inherit' },
                                children: this.state.apiKeySubmitting ? 'Configurando...' : '✓'
                            })
                        ]),

                        // Status message
                        this.state.operationMessage && React.createElement('div', {
                            key: 'status-message',
                            style: {
                                fontSize: '11px',
                                marginTop: '4px',
                                padding: '4px 6px',
                                borderRadius: '3px',
                                backgroundColor: this.state.lastOperationStatus === 'success' ? 'rgba(0, 255, 0, 0.1)' : 'rgba(255, 0, 0, 0.1)',
                                color: this.state.lastOperationStatus === 'success' ? 'var(--terminal-green)' : 'var(--terminal-red)',
                                border: `1px solid ${this.state.lastOperationStatus === 'success' ? 'var(--terminal-green)' : 'var(--terminal-red)'}`
                            }
                        }, this.state.operationMessage)
                    ]),

                    // Main Model Selection
                    this.state.selectedProvider && React.createElement('div', { key: 'mainmodel-section', style: { marginBottom: '16px' } }, [
                        React.createElement('label', {
                            key: 'mainmodel-label',
                            style: {
                                display: 'block',
                                color: 'var(--terminal-cyan)',
                                fontSize: '12px',
                                fontWeight: '600',
                                marginBottom: '6px'
                            }
                        }, 'Main Model:'),
                        React.createElement(antd.Select, {
                            key: 'mainmodel-select',
                            value: this.state.mainModel,
                            onChange: (value) => this.onModelChange('main', value),
                            loading: this.state.modelsLoading,
                            placeholder: this.state.availableModels.length === 0 ? 'No models available' : 'Select Main Model',
                            style: {
                                width: '100%',
                                fontFamily: 'inherit'
                            },
                            size: 'small',
                            disabled: this.state.availableModels.length === 0,
                            options: (() => {
                                const allModels = this.state.availableModels;
                                console.log('Rendering main model options:', allModels);
                                const options = allModels.map(model => ({
                                    label: model.id,
                                    value: model.id
                                }));
                                console.log('Main model options created:', options);
                                return options;
                            })()
                        })
                    ]),

                    // Small Model Selection
                    this.state.selectedProvider && React.createElement('div', { key: 'smallmodel-section', style: { marginBottom: '16px' } }, [
                        React.createElement('label', {
                            key: 'smallmodel-label',
                            style: {
                                display: 'block',
                                color: 'var(--terminal-cyan)',
                                fontSize: '12px',
                                fontWeight: '600',
                                marginBottom: '6px'
                            }
                        }, 'Small Model:'),
                        React.createElement(antd.Select, {
                            key: 'smallmodel-select',
                            value: this.state.smallModel,
                            onChange: (value) => this.onModelChange('small', value),
                            loading: this.state.modelsLoading,
                            placeholder: this.state.availableModels.length === 0 ? 'No models available' : 'Select Small Model',
                            style: {
                                width: '100%',
                                fontFamily: 'inherit'
                            },
                            size: 'small',
                            disabled: this.state.availableModels.length === 0,
                            options: (() => {
                                const allModels = this.state.availableModels;
                                console.log('Rendering small model options:', allModels);
                                const options = allModels.map(model => ({
                                    label: model.id,
                                    value: model.id
                                }));
                                console.log('Small model options created:', options);
                                return options;
                            })()
                        })
                    ]),

                    // Max Tokens Configuration
                    this.state.selectedProvider && React.createElement('div', { key: 'maxtokens-section', style: { marginBottom: '16px' } }, [
                        React.createElement('label', {
                            key: 'maxtokens-label',
                            style: {
                                display: 'block',
                                color: 'var(--terminal-cyan)',
                                fontSize: '12px',
                                fontWeight: '600',
                                marginBottom: '6px'
                            }
                        }, 'Max Tokens:'),
                        React.createElement(antd.InputNumber, {
                            key: 'maxtokens-input',
                            value: this.state.maxTokens,
                            onChange: this.onMaxTokensChange,
                            min: 1,
                            max: 32000,
                            step: 100,
                            placeholder: '1000',
                            style: {
                                width: '100%',
                                fontFamily: 'inherit'
                            },
                            size: 'small'
                        }),
                        React.createElement('div', {
                            key: 'maxtokens-hint',
                            style: {
                                fontSize: '10px',
                                color: 'var(--terminal-text-muted)',
                                marginTop: '2px'
                            }
                        }, 'Maximum tokens in response (1-32000)')
                    ]),

                    // Save Configuration Button
                    this.state.selectedProvider && (this.state.mainModel || this.state.smallModel) && React.createElement('div', { key: 'save-section', style: { marginBottom: '16px' } }, [
                        React.createElement(antd.Button, {
                            key: 'save-config-btn',
                            type: 'primary',
                            size: 'small',
                            onClick: this.onSaveConfiguration,
                            loading: this.state.configSaving,
                            disabled: this.state.configSaving,
                            style: {
                                width: '100%',
                                fontFamily: 'inherit',
                                background: 'var(--terminal-green)',
                                borderColor: 'var(--terminal-green)'
                            },
                            children: this.state.configSaving ? 'Guardando...' : '💾 Guardar Configuración'
                        })
                    ]),

                ])
            },
            {
                key: '2',
                label: 'MCP Servers',
                children: React.createElement('div', {
                    className: 'accordion-content'
                }, [
                    React.createElement('div', { key: 'server1', className: 'menu-item' }, '• Local Server'),
                    React.createElement('div', { key: 'server2', className: 'menu-item' }, '• Remote Server'),
                    React.createElement('div', { key: 'server3', className: 'menu-item' }, '• Test Server'),
                    React.createElement('div', { key: 'add-server', className: 'menu-item add-item' }, '+ Add Server')
                ])
            },
            {
                key: '3',
                label: 'Tools',
                children: React.createElement('div', {
                    className: 'accordion-content'
                }, [
                    React.createElement('div', { key: 'tool1', className: 'menu-item' }, '• File Manager'),
                    React.createElement('div', { key: 'tool2', className: 'menu-item' }, '• Code Editor'),
                    React.createElement('div', { key: 'tool3', className: 'menu-item' }, '• Terminal'),
                    React.createElement('div', { key: 'tool4', className: 'menu-item' }, '• Database'),
                ])
            },
            {
                key: '4',
                label: 'Resources',
                children: React.createElement('div', {
                    className: 'accordion-content'
                }, [
                    React.createElement('div', { key: 'res1', className: 'menu-item' }, '• Templates'),
                    React.createElement('div', { key: 'res2', className: 'menu-item' }, '• Snippets'),
                    React.createElement('div', { key: 'res3', className: 'menu-item' }, '• Documentation'),
                    React.createElement('div', { key: 'res4', className: 'menu-item' }, '• Examples'),
                ])
            },
            {
                key: '5',
                label: 'History',
                children: React.createElement('div', {
                    className: 'accordion-content'
                }, [
                    React.createElement('div', { key: 'hist1', className: 'menu-item' }, '• Recent Sessions'),
                    React.createElement('div', { key: 'hist2', className: 'menu-item' }, '• Saved Queries'),
                    React.createElement('div', { key: 'hist3', className: 'menu-item' }, '• Bookmarks'),
                ])
            }
        ];

        return React.createElement('div', {
            className: 'leftbar-content',
            style: {
                display: 'flex',
                flexDirection: 'column',
                height: '100%'
            }
        }, [
            // Header with title and collapse button
            React.createElement('div', {
                key: 'header',
                className: 'leftbar-header',
                style: {
                    padding: '12px',
                    borderBottom: '1px solid var(--terminal-border)',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    minHeight: '48px'
                }
            }, [
                !collapsed && React.createElement('span', {
                    key: 'title',
                    style: {
                        color: 'var(--terminal-cyan)',
                        fontSize: '14px',
                        fontWeight: '600',
                        fontFamily: 'inherit'
                    }
                }, 'Navigation'),

                React.createElement('button', {
                    key: 'collapse-btn',
                    onClick: onToggle,
                    style: {
                        background: 'transparent',
                        border: '1px solid var(--terminal-border)',
                        color: 'var(--terminal-text)',
                        padding: '6px 8px',
                        borderRadius: '4px',
                        cursor: 'pointer',
                        fontFamily: 'inherit',
                        fontSize: '12px',
                        transition: 'all 0.2s ease'
                    },
                    onMouseEnter: (e) => {
                        e.target.style.borderColor = 'var(--terminal-cyan)';
                        e.target.style.color = 'var(--terminal-cyan)';
                    },
                    onMouseLeave: (e) => {
                        e.target.style.borderColor = 'var(--terminal-border)';
                        e.target.style.color = 'var(--terminal-text)';
                    }
                }, collapsed ? '→' : '←')
            ]),

            // Scrollable content area
            !collapsed && React.createElement('div', {
                key: 'content',
                className: 'leftbar-content scrollbar',
                style: {
                    flex: '1',
                    padding: '16px 12px',
                    overflowY: 'auto',
                    overflowX: 'hidden'
                }
            }, [
                // Using antd.Collapse following Rayflow pattern
                React.createElement(antd.Collapse, {
                    key: 'accordion',
                    activeKey: activeKeys,
                    onChange: this.onAccordionChange,
                    ghost: true,
                    size: 'small',
                    items: accordionItems,
                    className: 'terminal-accordion',
                    style: {
                        background: 'transparent',
                        fontFamily: 'inherit'
                    }
                })
            ])
        ]);
    }
}

// Export for use in other files
window.LeftBar = LeftBar;