/**
 * ChatInput Component
 * Text input area for sending messages to chat
 */

class ChatInput extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            message: '',
            isFocused: false
        };
        this.textareaRef = React.createRef();
    }

    handleInputChange = (e) => {
        this.setState({ message: e.target.value });
        this.adjustTextareaHeight();
    }

    handleKeyDown = (e) => {
        if (e.key === 'Enter') {
            if (e.shiftKey) {
                // Shift+Enter: new line (default behavior)
                return;
            } else {
                // Enter: send message
                e.preventDefault();
                this.handleSubmit();
            }
        }
    }

    handleSubmit = () => {
        const { message } = this.state;
        const { onSendMessage, disabled } = this.props;

        if (!message.trim() || disabled) return;

        // Send message via prop callback
        onSendMessage(message);

        // Clear input
        this.setState({ message: '' });
        this.resetTextareaHeight();
    }

    adjustTextareaHeight = () => {
        const textarea = this.textareaRef.current;
        if (textarea) {
            textarea.style.height = 'auto';
            textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
        }
    }

    resetTextareaHeight = () => {
        const textarea = this.textareaRef.current;
        if (textarea) {
            textarea.style.height = '40px';
        }
    }

    handleFocus = () => {
        this.setState({ isFocused: true });
    }

    handleBlur = () => {
        this.setState({ isFocused: false });
    }

    render() {
        const { disabled } = this.props;
        const { message, isFocused } = this.state;

        return React.createElement('div', {
            className: 'chat-input',
            style: {
                padding: '16px',
                borderTop: '1px solid var(--terminal-border)',
                background: 'var(--terminal-surface)'
            }
        }, [
            React.createElement('div', {
                key: 'input-wrapper',
                style: {
                    display: 'flex',
                    alignItems: 'flex-end',
                    gap: '8px'
                }
            }, [
                // Message textarea
                React.createElement('div', {
                    key: 'textarea-container',
                    style: {
                        flex: '1',
                        position: 'relative'
                    }
                }, [
                    React.createElement('textarea', {
                        key: 'textarea',
                        ref: this.textareaRef,
                        value: message,
                        onChange: this.handleInputChange,
                        onKeyDown: this.handleKeyDown,
                        onFocus: this.handleFocus,
                        onBlur: this.handleBlur,
                        disabled: disabled,
                        placeholder: disabled ? 'Sending...' : 'Type your message... (Enter to send, Shift+Enter for new line)',
                        style: {
                            width: '100%',
                            minHeight: '40px',
                            maxHeight: '120px',
                            padding: '10px 12px',
                            border: `1px solid ${isFocused ? 'var(--terminal-cyan)' : 'var(--terminal-border)'}`,
                            borderRadius: '6px',
                            background: 'var(--terminal-background)',
                            color: 'var(--terminal-text)',
                            fontSize: '14px',
                            fontFamily: 'inherit',
                            resize: 'none',
                            outline: 'none',
                            lineHeight: '1.4',
                            transition: 'border-color 0.2s ease',
                            boxSizing: 'border-box'
                        }
                    }),

                    // Character counter (optional)
                    message.length > 500 && React.createElement('div', {
                        key: 'counter',
                        style: {
                            position: 'absolute',
                            bottom: '-20px',
                            right: '0',
                            fontSize: '11px',
                            color: message.length > 1000 ? 'var(--terminal-red)' : 'var(--terminal-gray)'
                        }
                    }, `${message.length}/2000`)
                ]),

                // Send button
                React.createElement('button', {
                    key: 'send-btn',
                    onClick: this.handleSubmit,
                    disabled: disabled || !message.trim(),
                    style: {
                        padding: '10px 16px',
                        background: (!disabled && message.trim()) ? 'var(--terminal-cyan)' : 'var(--terminal-gray)',
                        color: 'white',
                        border: 'none',
                        borderRadius: '6px',
                        cursor: (!disabled && message.trim()) ? 'pointer' : 'not-allowed',
                        fontSize: '14px',
                        fontWeight: '500',
                        fontFamily: 'inherit',
                        transition: 'background-color 0.2s ease',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '6px',
                        minWidth: '80px',
                        height: '40px',
                        justifyContent: 'center'
                    },
                    onMouseEnter: (e) => {
                        if (!disabled && message.trim()) {
                            e.target.style.background = 'var(--terminal-blue)';
                        }
                    },
                    onMouseLeave: (e) => {
                        if (!disabled && message.trim()) {
                            e.target.style.background = 'var(--terminal-cyan)';
                        }
                    }
                }, [
                    disabled
                        ? React.createElement('span', { key: 'loading' }, '⏳')
                        : React.createElement('span', { key: 'send' }, '🚀'),
                    disabled ? 'Sending' : 'Send'
                ])
            ]),

            // Helper text
            React.createElement('div', {
                key: 'helper',
                style: {
                    fontSize: '11px',
                    color: 'var(--terminal-gray)',
                    marginTop: '8px',
                    textAlign: 'center'
                }
            }, 'Tip: Use Shift+Enter for line breaks, Enter to send')
        ]);
    }
}

// Export for use in other files
window.ChatInput = ChatInput;