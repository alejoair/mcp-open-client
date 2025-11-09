/**
 * MainContent Component
 * Central content area between sidebars
 */

class MainContent extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            currentView: 'chat', // Default to chat view
            messages: [
                {
                    id: 1,
                    type: 'system',
                    content: 'MCP Open Client initialized successfully',
                    timestamp: new Date().toLocaleTimeString()
                },
                {
                    id: 2,
                    type: 'info',
                    content: 'Ready to connect to MCP servers',
                    timestamp: new Date().toLocaleTimeString()
                }
            ]
        };
    }

    addMessage = (type, content) => {
        const newMessage = {
            id: Date.now(),
            type,
            content,
            timestamp: new Date().toLocaleTimeString()
        };

        this.setState(prevState => ({
            messages: [...prevState.messages, newMessage]
        }));
    }

    renderWelcomeView = () => {
        return React.createElement('div', {
            className: 'welcome-view',
            style: {
                padding: '40px',
                textAlign: 'center',
                height: '100%',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'center',
                alignItems: 'center'
            }
        }, [
            React.createElement('div', {
                key: 'logo',
                style: {
                    fontSize: '64px',
                    marginBottom: '24px',
                    background: 'linear-gradient(45deg, var(--terminal-green), var(--terminal-cyan))',
                    backgroundClip: 'text',
                    WebkitBackgroundClip: 'text',
                    color: 'transparent'
                }
            }, '🚀'),

            React.createElement('h1', {
                key: 'title',
                style: {
                    color: 'var(--terminal-text-bright)',
                    fontSize: '28px',
                    fontWeight: '600',
                    marginBottom: '16px',
                    fontFamily: 'inherit'
                }
            }, 'MCP Open Client'),

            React.createElement('p', {
                key: 'subtitle',
                style: {
                    color: 'var(--terminal-text-dim)',
                    fontSize: '16px',
                    maxWidth: '600px',
                    lineHeight: '1.6',
                    marginBottom: '32px'
                }
            }, 'A modern, web-based Model Context Protocol client with terminal aesthetics. Connect to MCP servers, execute tools, and manage resources through a sleek interface.'),

            React.createElement('div', {
                key: 'features',
                className: 'feature-grid',
                style: {
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                    gap: '20px',
                    maxWidth: '800px',
                    width: '100%',
                    marginTop: '40px'
                }
            }, [
                this.renderFeatureCard('⚡', 'Fast Performance', 'Built with FastAPI and React for optimal speed'),
                this.renderFeatureCard('🔧', 'Tool Integration', 'Seamless MCP tool execution and management'),
                this.renderFeatureCard('🌐', 'Real-time Updates', 'WebSocket-powered live communication'),
                this.renderFeatureCard('🎨', 'Modern UI', 'Terminal-inspired dark theme with Ant Design')
            ])
        ]);
    }

    renderFeatureCard = (icon, title, description) => {
        return React.createElement('div', {
            key: title,
            className: 'feature-card',
            style: {
                background: 'var(--terminal-bg-light)',
                border: '1px solid var(--terminal-border)',
                borderRadius: '8px',
                padding: '24px',
                textAlign: 'center',
                transition: 'all 0.3s ease'
            },
            onMouseEnter: (e) => {
                e.target.style.borderColor = 'var(--terminal-cyan)';
                e.target.style.transform = 'translateY(-2px)';
                e.target.style.boxShadow = '0 8px 16px rgba(124, 58, 237, 0.2)';
            },
            onMouseLeave: (e) => {
                e.target.style.borderColor = 'var(--terminal-border)';
                e.target.style.transform = 'translateY(0)';
                e.target.style.boxShadow = 'none';
            }
        }, [
            React.createElement('div', {
                key: 'icon',
                style: {
                    fontSize: '32px',
                    marginBottom: '12px'
                }
            }, icon),

            React.createElement('h3', {
                key: 'title',
                style: {
                    color: 'var(--terminal-cyan)',
                    fontSize: '16px',
                    fontWeight: '600',
                    marginBottom: '8px',
                    fontFamily: 'inherit'
                }
            }, title),

            React.createElement('p', {
                key: 'description',
                style: {
                    color: 'var(--terminal-text-dim)',
                    fontSize: '12px',
                    lineHeight: '1.5',
                    margin: 0
                }
            }, description)
        ]);
    }

    renderAIChatView = () => {
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

    renderChatView = () => {
        const { messages } = this.state;

        return React.createElement('div', {
            className: 'chat-view',
            style: {
                height: '100%',
                display: 'flex',
                flexDirection: 'column'
            }
        }, [
            React.createElement('div', {
                key: 'chat-header',
                style: {
                    padding: '16px',
                    borderBottom: '1px solid var(--terminal-border)',
                    background: 'var(--terminal-bg-light)'
                }
            }, [
                React.createElement('h3', {
                    key: 'title',
                    style: {
                        color: 'var(--terminal-text-bright)',
                        fontSize: '16px',
                        fontWeight: '600',
                        margin: 0,
                        fontFamily: 'inherit'
                    }
                }, 'Active Session')
            ]),

            React.createElement('div', {
                key: 'messages-container',
                className: 'messages-container scrollbar',
                style: {
                    flex: 1,
                    padding: '16px',
                    overflowY: 'auto'
                }
            }, messages.map(message =>
                React.createElement('div', {
                    key: message.id,
                    className: `message message-${message.type}`,
                    style: {
                        marginBottom: '12px',
                        padding: '12px 16px',
                        borderLeft: '3px solid ' + (
                            message.type === 'system' ? 'var(--terminal-green)' :
                            message.type === 'error' ? 'var(--terminal-red)' :
                            'var(--terminal-cyan)'
                        ),
                        background: 'rgba(255,255,255,0.03)',
                        borderRadius: '0 4px 4px 0'
                    }
                }, [
                    React.createElement('div', {
                        key: 'header',
                        style: {
                            display: 'flex',
                            justifyContent: 'space-between',
                            alignItems: 'center',
                            marginBottom: '6px'
                        }
                    }, [
                        React.createElement('span', {
                            key: 'type',
                            style: {
                                color: message.type === 'system' ? 'var(--terminal-green)' :
                                       message.type === 'error' ? 'var(--terminal-red)' :
                                       'var(--terminal-cyan)',
                                fontSize: '11px',
                                fontWeight: '600',
                                textTransform: 'uppercase'
                            }
                        }, message.type),
                        React.createElement('span', {
                            key: 'time',
                            style: {
                                color: 'var(--terminal-text-dim)',
                                fontSize: '10px'
                            }
                        }, message.timestamp)
                    ]),
                    React.createElement('div', {
                        key: 'content',
                        style: {
                            color: 'var(--terminal-text)',
                            fontSize: '13px',
                            lineHeight: '1.4'
                        }
                    }, message.content)
                ])
            ))
        ]);
    }

    render() {
        const { currentView } = this.state;

        return React.createElement('div', {
            className: 'main-content',
            style: {
                flex: 1,
                background: 'var(--terminal-bg)',
                height: '100%',
                overflow: 'hidden'
            }
        }, [
            React.createElement('div', {
                key: 'content-area',
                style: {
                    height: '100%',
                    overflow: 'hidden'
                }
            },
                currentView === 'welcome' ? this.renderWelcomeView() :
                currentView === 'chat' ? this.renderAIChatView() :
                this.renderChatView()
            )
        ]);
    }
}

// Export for use in other files
window.MainContent = MainContent;