/**
 * ChatWindow Component
 * Main chat interface with message history and input
 */

class ChatWindow extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            messages: [], // Array of {role: 'user'|'assistant', content: string}
            isLoading: false,
            error: null
        };
        this.messagesEndRef = React.createRef();
    }

    componentDidUpdate(prevProps, prevState) {
        // Auto-scroll to bottom when new messages are added
        if (prevState.messages.length !== this.state.messages.length) {
            this.scrollToBottom();
        }
    }

    scrollToBottom = () => {
        if (this.messagesEndRef.current) {
            this.messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
        }
    }

    handleSendMessage = async (messageText) => {
        if (!messageText.trim() || this.state.isLoading) return;

        const userMessage = { role: 'user', content: messageText.trim() };

        // Add user message to chat
        this.setState(prevState => ({
            messages: [...prevState.messages, userMessage],
            isLoading: true,
            error: null
        }));

        // Create a placeholder assistant message that will be updated with streaming content
        const assistantMessageId = Date.now();
        const assistantMessage = {
            role: 'assistant',
            content: '',
            reasoning: '',
            id: assistantMessageId,
            isStreaming: true,
            showReasoning: false  // Initially collapsed
        };

        this.setState(prevState => ({
            messages: [...prevState.messages, assistantMessage]
        }));

        try {
            console.log('🚀 Starting streaming chat request');

            // Use streaming endpoint with POST request
            const response = await fetch('/api/chat/completions/stream', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'text/event-stream',
                },
                body: JSON.stringify({
                    messages: [...this.state.messages, userMessage].filter(msg => !msg.isStreaming),
                    max_tokens: 1000,
                    temperature: 0.7
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: Error in streaming chat request`);
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder();

            let buffer = '';
            let accumulatedContent = '';

            while (true) {
                const { done, value } = await reader.read();

                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');

                // Keep the last potentially incomplete line in the buffer
                buffer = lines.pop() || '';

                for (const line of lines) {
                    if (line.trim() === '') continue;

                    if (line.startsWith('data: ')) {
                        const data = line.slice(6);

                        if (data === '[DONE]') {
                            console.log('✅ Streaming completed');
                            break;
                        }

                        try {
                            const parsed = JSON.parse(data);
                            console.log('📡 Streaming data:', parsed);

                            if (parsed.type === 'reasoning_chunk' && parsed.content) {
                                // Update reasoning section
                                this.setState(prevState => ({
                                    messages: prevState.messages.map(msg =>
                                        msg.id === assistantMessageId
                                            ? { ...msg, reasoning: parsed.accumulated_reasoning || (msg.reasoning + parsed.content) }
                                            : msg
                                    )
                                }));

                                // Auto-scroll as content updates
                                setTimeout(() => this.scrollToBottom(), 50);
                            } else if (parsed.type === 'content_chunk' && parsed.content) {
                                // Update content section
                                this.setState(prevState => ({
                                    messages: prevState.messages.map(msg =>
                                        msg.id === assistantMessageId
                                            ? { ...msg, content: parsed.accumulated_content || (msg.content + parsed.content) }
                                            : msg
                                    )
                                }));

                                // Auto-scroll as content updates
                                setTimeout(() => this.scrollToBottom(), 50);
                            } else if (parsed.type === 'complete') {
                                console.log('✅ Final response:', parsed.final_content, 'Reasoning:', parsed.final_reasoning);

                                // Mark message as complete
                                this.setState(prevState => ({
                                    messages: prevState.messages.map(msg =>
                                        msg.id === assistantMessageId
                                            ? {
                                                ...msg,
                                                content: parsed.final_content || msg.content,
                                                reasoning: parsed.final_reasoning || msg.reasoning,
                                                isStreaming: false
                                            }
                                            : msg
                                    ),
                                    isLoading: false
                                }));
                            } else if (parsed.type === 'error') {
                                throw new Error(parsed.error);
                            }
                        } catch (parseError) {
                            console.warn('Failed to parse streaming data:', parseError, data);
                        }
                    }
                }
            }

            // Ensure loading state is cleared
            this.setState({ isLoading: false });

        } catch (error) {
            console.error('❌ Streaming chat error:', error);

            // Remove the incomplete assistant message and show error
            this.setState(prevState => ({
                messages: prevState.messages.filter(msg => msg.id !== assistantMessageId),
                isLoading: false,
                error: error.message || 'Failed to send message'
            }));
        }
    }

    clearChat = () => {
        this.setState({
            messages: [],
            error: null
        });
    }

    toggleReasoning = (messageId) => {
        this.setState(prevState => ({
            messages: prevState.messages.map(msg =>
                msg.id === messageId
                    ? { ...msg, showReasoning: !msg.showReasoning }
                    : msg
            )
        }));
    }

    render() {
        return React.createElement('div', {
            className: 'chat-window',
            style: {
                display: 'flex',
                flexDirection: 'column',
                height: '100%',
                background: 'var(--terminal-background)',
                border: '1px solid var(--terminal-border)',
                borderRadius: '8px',
                fontFamily: 'inherit'
            }
        }, [
            // Header
            React.createElement('div', {
                key: 'header',
                style: {
                    padding: '12px 16px',
                    borderBottom: '1px solid var(--terminal-border)',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    background: 'var(--terminal-surface)'
                }
            }, [
                React.createElement('div', {
                    key: 'title',
                    style: {
                        color: 'var(--terminal-cyan)',
                        fontSize: '14px',
                        fontWeight: '600'
                    }
                }, '💬 Chat Assistant'),

                React.createElement('button', {
                    key: 'clear-btn',
                    onClick: this.clearChat,
                    style: {
                        background: 'transparent',
                        border: '1px solid var(--terminal-border)',
                        color: 'var(--terminal-text)',
                        padding: '4px 8px',
                        borderRadius: '4px',
                        cursor: 'pointer',
                        fontSize: '11px',
                        fontFamily: 'inherit'
                    },
                    onMouseEnter: (e) => {
                        e.target.style.borderColor = 'var(--terminal-cyan)';
                        e.target.style.color = 'var(--terminal-cyan)';
                    },
                    onMouseLeave: (e) => {
                        e.target.style.borderColor = 'var(--terminal-border)';
                        e.target.style.color = 'var(--terminal-text)';
                    }
                }, '🗑️ Clear')
            ]),

            // Messages Area
            React.createElement('div', {
                key: 'messages',
                className: 'messages-area scrollbar',
                style: {
                    flex: '1',
                    padding: '16px',
                    overflowY: 'auto',
                    overflowX: 'hidden'
                }
            }, [
                // Welcome message when no messages
                this.state.messages.length === 0 && React.createElement('div', {
                    key: 'welcome',
                    style: {
                        textAlign: 'center',
                        color: 'var(--terminal-gray)',
                        fontSize: '14px',
                        marginTop: '40px'
                    }
                }, [
                    React.createElement('div', { key: 'icon', style: { fontSize: '32px', marginBottom: '12px' } }, '🤖'),
                    React.createElement('div', { key: 'text' }, 'Start a conversation with the AI assistant')
                ]),

                // Chat Messages
                ...this.state.messages.map((message, index) =>
                    React.createElement('div', {
                        key: `message-${index}`,
                        className: `message ${message.role}`,
                        style: {
                            marginBottom: '16px',
                            display: 'flex',
                            flexDirection: message.role === 'user' ? 'row-reverse' : 'row',
                            alignItems: 'flex-start'
                        }
                    }, [
                        // Message Avatar
                        React.createElement('div', {
                            key: 'avatar',
                            style: {
                                width: '32px',
                                height: '32px',
                                borderRadius: '50%',
                                background: message.role === 'user' ? 'var(--terminal-blue)' : 'var(--terminal-green)',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                fontSize: '14px',
                                margin: message.role === 'user' ? '0 0 0 12px' : '0 12px 0 0',
                                flexShrink: 0
                            }
                        }, message.role === 'user' ? '👤' : '🤖'),

                        // Message Content
                        React.createElement('div', {
                            key: 'content',
                            style: {
                                maxWidth: '70%',
                                padding: '12px 16px',
                                borderRadius: '12px',
                                background: message.role === 'user'
                                    ? 'var(--terminal-blue)'
                                    : 'var(--terminal-surface)',
                                color: message.role === 'user'
                                    ? 'white'
                                    : 'var(--terminal-text)',
                                fontSize: '14px',
                                lineHeight: '1.5',
                                wordWrap: 'break-word',
                                border: message.role === 'assistant' ? '1px solid var(--terminal-border)' : 'none',
                                position: 'relative'
                            }
                        }, [
                            // Reasoning section for assistant messages
                            message.role === 'assistant' && message.reasoning && React.createElement('div', {
                                key: 'reasoning-section',
                                style: {
                                    marginBottom: '12px',
                                    border: '1px solid var(--terminal-border)',
                                    borderRadius: '6px',
                                    overflow: 'hidden'
                                }
                            }, [
                                // Reasoning toggle header
                                React.createElement('div', {
                                    key: 'reasoning-header',
                                    onClick: () => this.toggleReasoning(message.id),
                                    style: {
                                        background: 'var(--terminal-bg)',
                                        padding: '8px 12px',
                                        cursor: 'pointer',
                                        display: 'flex',
                                        alignItems: 'center',
                                        justifyContent: 'space-between',
                                        fontSize: '12px',
                                        fontWeight: '600',
                                        color: 'var(--terminal-purple)',
                                        borderBottom: message.showReasoning ? '1px solid var(--terminal-border)' : 'none'
                                    }
                                }, [
                                    React.createElement('span', {
                                        key: 'reasoning-label',
                                        style: {
                                            display: 'flex',
                                            alignItems: 'center',
                                            gap: '6px'
                                        }
                                    }, [
                                        React.createElement('span', { key: 'icon' }, '🧠'),
                                        React.createElement('span', { key: 'text' }, 'Pensamiento del modelo')
                                    ]),
                                    React.createElement('span', {
                                        key: 'toggle-icon',
                                        style: {
                                            transform: message.showReasoning ? 'rotate(180deg)' : 'rotate(0deg)',
                                            transition: 'transform 0.2s ease'
                                        }
                                    }, '▼')
                                ]),

                                // Reasoning content (collapsible)
                                message.showReasoning && React.createElement('div', {
                                    key: 'reasoning-content',
                                    style: {
                                        padding: '12px',
                                        background: 'rgba(124, 58, 237, 0.05)',
                                        fontSize: '13px',
                                        lineHeight: '1.4',
                                        color: 'var(--terminal-text-dim)',
                                        fontStyle: 'italic',
                                        whiteSpace: 'pre-wrap'
                                    }
                                }, message.reasoning)
                            ]),

                            // Main message content
                            React.createElement('div', {
                                key: 'main-content'
                            }, [
                                React.createElement('span', {
                                    key: 'text'
                                }, message.content || (message.isStreaming ? '' : 'No content')),

                                // Streaming indicator for assistant messages
                                message.role === 'assistant' && message.isStreaming && React.createElement('span', {
                                    key: 'typing-indicator',
                                    style: {
                                        color: 'var(--terminal-green)',
                                        fontSize: '12px',
                                        marginLeft: '4px',
                                        animation: 'blink 1s infinite'
                                    }
                                }, '●')
                            ])
                        ])
                    ])
                ),

                // Loading indicator
                this.state.isLoading && React.createElement('div', {
                    key: 'loading',
                    style: {
                        display: 'flex',
                        alignItems: 'center',
                        marginBottom: '16px'
                    }
                }, [
                    React.createElement('div', {
                        key: 'avatar',
                        style: {
                            width: '32px',
                            height: '32px',
                            borderRadius: '50%',
                            background: 'var(--terminal-green)',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            fontSize: '14px',
                            marginRight: '12px'
                        }
                    }, '🤖'),
                    React.createElement('div', {
                        key: 'dots',
                        style: {
                            padding: '12px 16px',
                            borderRadius: '12px',
                            background: 'var(--terminal-surface)',
                            border: '1px solid var(--terminal-border)',
                            color: 'var(--terminal-gray)',
                            fontSize: '14px'
                        }
                    }, 'Thinking...')
                ]),

                // Error message
                this.state.error && React.createElement('div', {
                    key: 'error',
                    style: {
                        padding: '12px 16px',
                        borderRadius: '8px',
                        background: 'rgba(255, 0, 0, 0.1)',
                        border: '1px solid var(--terminal-red)',
                        color: 'var(--terminal-red)',
                        fontSize: '14px',
                        marginBottom: '16px'
                    }
                }, [
                    React.createElement('strong', { key: 'title' }, 'Error: '),
                    this.state.error
                ]),

                // Scroll anchor
                React.createElement('div', {
                    key: 'scroll-anchor',
                    ref: this.messagesEndRef
                })
            ]),

            // Chat Input
            React.createElement(ChatInput, {
                key: 'input',
                onSendMessage: this.handleSendMessage,
                disabled: this.state.isLoading
            })
        ]);
    }
}

// Export for use in other files
window.ChatWindow = ChatWindow;