/**
 * BottomBar Component
 * Collapsible console panel at the bottom
 */

class BottomBar extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            logs: [
                {
                    id: 1,
                    level: 'info',
                    message: 'MCP Open Client initialized',
                    timestamp: new Date().toISOString(),
                    source: 'system'
                },
                {
                    id: 2,
                    level: 'success',
                    message: 'FastAPI server started on port 8080',
                    timestamp: new Date().toISOString(),
                    source: 'server'
                },
                {
                    id: 3,
                    level: 'info',
                    message: 'WebSocket connection ready',
                    timestamp: new Date().toISOString(),
                    source: 'websocket'
                }
            ],
            commandHistory: [],
            currentCommand: '',
            historyIndex: -1
        };
        this.commandInputRef = React.createRef();
    }


    addLog = (level, message, source = 'user') => {
        const newLog = {
            id: Date.now(),
            level,
            message,
            timestamp: new Date().toISOString(),
            source
        };

        this.setState(prevState => ({
            logs: [...prevState.logs, newLog].slice(-100) // Keep only last 100 logs
        }));
    }

    handleCommandSubmit = (e) => {
        e.preventDefault();
        const { currentCommand, commandHistory } = this.state;

        if (currentCommand.trim()) {
            // Add to history
            this.setState(prevState => ({
                commandHistory: [...prevState.commandHistory, currentCommand],
                currentCommand: '',
                historyIndex: -1
            }));

            // Add command to logs
            this.addLog('command', `$ ${currentCommand}`, 'user');

            // Simulate command execution
            setTimeout(() => {
                this.addLog('info', `Executed: ${currentCommand}`, 'system');
            }, 100);
        }
    }

    handleKeyDown = (e) => {
        const { commandHistory, historyIndex } = this.state;

        if (e.key === 'ArrowUp') {
            e.preventDefault();
            if (commandHistory.length > 0 && historyIndex < commandHistory.length - 1) {
                const newIndex = historyIndex + 1;
                this.setState({
                    historyIndex: newIndex,
                    currentCommand: commandHistory[commandHistory.length - 1 - newIndex]
                });
            }
        } else if (e.key === 'ArrowDown') {
            e.preventDefault();
            if (historyIndex > 0) {
                const newIndex = historyIndex - 1;
                this.setState({
                    historyIndex: newIndex,
                    currentCommand: commandHistory[commandHistory.length - 1 - newIndex]
                });
            } else if (historyIndex === 0) {
                this.setState({
                    historyIndex: -1,
                    currentCommand: ''
                });
            }
        }
    }

    formatTimestamp = (timestamp) => {
        return new Date(timestamp).toLocaleTimeString();
    }

    getLevelColor = (level) => {
        switch (level) {
            case 'error': return 'var(--terminal-red)';
            case 'warning': return 'var(--terminal-yellow)';
            case 'success': return 'var(--terminal-green)';
            case 'command': return 'var(--terminal-purple)';
            default: return 'var(--terminal-cyan)';
        }
    }

    getLevelIcon = (level) => {
        switch (level) {
            case 'error': return '❌';
            case 'warning': return '⚠️';
            case 'success': return '✅';
            case 'command': return '>';
            default: return 'ℹ️';
        }
    }

    clearLogs = () => {
        this.setState({
            logs: []
        });
    }

    render() {
        const { collapsed = false, onToggle } = this.props;
        const { logs, currentCommand } = this.state;

        return React.createElement('div', {
            className: 'bottombar-content',
            style: {
                height: '100%',
                background: 'var(--terminal-bg-light)',
                display: 'flex',
                flexDirection: 'column',
                position: 'relative'
            }
        }, [
            // Header with title and controls
            React.createElement('div', {
                key: 'header',
                className: 'bottombar-header',
                style: {
                    padding: '12px 16px',
                    borderBottom: collapsed ? 'none' : '1px solid var(--terminal-border)',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    minHeight: '48px'
                }
            }, [
                React.createElement('div', {
                    key: 'title-area',
                    style: {
                        display: 'flex',
                        alignItems: 'center',
                        gap: '12px'
                    }
                }, [
                    React.createElement('span', {
                        key: 'title',
                        style: {
                            color: 'var(--terminal-yellow)',
                            fontSize: '14px',
                            fontWeight: '600',
                            fontFamily: 'inherit'
                        }
                    }, 'Console'),

                    !collapsed && React.createElement('div', {
                        key: 'status',
                        style: {
                            display: 'flex',
                            alignItems: 'center',
                            gap: '8px',
                            fontSize: '11px',
                            color: 'var(--terminal-text-dim)'
                        }
                    }, [
                        React.createElement('span', { key: 'logs-count' }, `${logs.length} logs`),
                        React.createElement('span', { key: 'separator' }, '•'),
                        React.createElement('span', { key: 'status' }, 'Active')
                    ])
                ]),

                React.createElement('div', {
                    key: 'controls',
                    style: {
                        display: 'flex',
                        alignItems: 'center',
                        gap: '8px'
                    }
                }, [
                    !collapsed && React.createElement('button', {
                        key: 'clear-btn',
                        onClick: this.clearLogs,
                        style: {
                            background: 'transparent',
                            border: '1px solid var(--terminal-border)',
                            color: 'var(--terminal-text-dim)',
                            padding: '4px 8px',
                            borderRadius: '3px',
                            cursor: 'pointer',
                            fontSize: '10px',
                            fontFamily: 'inherit',
                            transition: 'all 0.2s ease'
                        },
                        onMouseEnter: (e) => {
                            e.target.style.color = 'var(--terminal-red)';
                            e.target.style.borderColor = 'var(--terminal-red)';
                        },
                        onMouseLeave: (e) => {
                            e.target.style.color = 'var(--terminal-text-dim)';
                            e.target.style.borderColor = 'var(--terminal-border)';
                        }
                    }, 'Clear'),

                    React.createElement('button', {
                        key: 'toggle-btn',
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
                            e.target.style.borderColor = 'var(--terminal-yellow)';
                            e.target.style.color = 'var(--terminal-yellow)';
                        },
                        onMouseLeave: (e) => {
                            e.target.style.borderColor = 'var(--terminal-border)';
                            e.target.style.color = 'var(--terminal-text)';
                        }
                    }, collapsed ? '↑' : '↓')
                ])
            ]),

            // Console content (hidden when collapsed)
            !collapsed && React.createElement('div', {
                key: 'content',
                style: {
                    flex: 1,
                    display: 'flex',
                    flexDirection: 'column',
                    overflow: 'hidden'
                }
            }, [
                // Logs area
                React.createElement('div', {
                    key: 'logs',
                    className: 'console-logs scrollbar',
                    style: {
                        flex: 1,
                        padding: '8px 16px',
                        overflowY: 'auto',
                        fontSize: '12px',
                        fontFamily: 'inherit'
                    }
                }, logs.map(log =>
                    React.createElement('div', {
                        key: log.id,
                        className: 'log-entry',
                        style: {
                            display: 'flex',
                            alignItems: 'flex-start',
                            gap: '8px',
                            marginBottom: '4px',
                            padding: '2px 0'
                        }
                    }, [
                        React.createElement('span', {
                            key: 'time',
                            style: {
                                color: 'var(--terminal-text-dim)',
                                fontSize: '10px',
                                minWidth: '65px',
                                fontFamily: 'inherit'
                            }
                        }, this.formatTimestamp(log.timestamp)),

                        React.createElement('span', {
                            key: 'level',
                            style: {
                                color: this.getLevelColor(log.level),
                                minWidth: '15px',
                                fontSize: '10px'
                            }
                        }, this.getLevelIcon(log.level)),

                        React.createElement('span', {
                            key: 'source',
                            style: {
                                color: 'var(--terminal-purple)',
                                fontSize: '10px',
                                minWidth: '60px',
                                textTransform: 'uppercase'
                            }
                        }, `[${log.source}]`),

                        React.createElement('span', {
                            key: 'message',
                            style: {
                                color: 'var(--terminal-text)',
                                flex: 1,
                                wordBreak: 'break-word'
                            }
                        }, log.message)
                    ])
                )),

                // Command input
                React.createElement('div', {
                    key: 'command-input',
                    style: {
                        padding: '8px 16px',
                        borderTop: '1px solid var(--terminal-border)',
                        background: 'var(--terminal-bg)'
                    }
                }, [
                    React.createElement('form', {
                        key: 'form',
                        onSubmit: this.handleCommandSubmit,
                        style: {
                            display: 'flex',
                            alignItems: 'center',
                            gap: '8px'
                        }
                    }, [
                        React.createElement('span', {
                            key: 'prompt',
                            style: {
                                color: 'var(--terminal-green)',
                                fontSize: '13px',
                                fontWeight: '600'
                            }
                        }, '❯'),

                        React.createElement('input', {
                            key: 'input',
                            ref: this.commandInputRef,
                            type: 'text',
                            value: currentCommand,
                            onChange: (e) => this.setState({ currentCommand: e.target.value }),
                            onKeyDown: this.handleKeyDown,
                            placeholder: 'Enter command...',
                            style: {
                                flex: 1,
                                background: 'transparent',
                                border: 'none',
                                outline: 'none',
                                color: 'var(--terminal-text)',
                                fontSize: '13px',
                                fontFamily: 'inherit',
                                padding: '4px 0'
                            }
                        })
                    ])
                ])
            ])
        ]);
    }
}

// Export for use in other files
window.BottomBar = BottomBar;