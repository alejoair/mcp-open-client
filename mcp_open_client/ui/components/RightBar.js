/**
 * RightBar Component
 * Inspector showing machine characteristics and system information
 */

class RightBar extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            systemInfo: {
                os: 'Windows 11',
                cpu: 'Intel Core i7-12700K',
                memory: '16 GB DDR4',
                disk: '512 GB NVMe SSD',
                gpu: 'NVIDIA RTX 3080',
                uptime: '2 days, 14 hours',
                load: '23%',
                temperature: '42°C'
            },
            networkInfo: {
                ip: '192.168.1.100',
                gateway: '192.168.1.1',
                dns: '1.1.1.1',
                status: 'Connected'
            },
            processInfo: {
                totalProcesses: 156,
                runningServices: 23,
                memoryUsage: '8.2 GB',
                cpuUsage: '12%'
            }
        };
        this.updateInterval = null;
    }

    componentDidMount() {
        this.updateInterval = setInterval(this.updateStats, 2000);
    }

    componentWillUnmount() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
        }
    }

    updateStats = () => {
        this.setState(prevState => ({
            systemInfo: {
                ...prevState.systemInfo,
                load: Math.floor(Math.random() * 40 + 10) + '%',
                temperature: Math.floor(Math.random() * 20 + 35) + '°C'
            },
            processInfo: {
                ...prevState.processInfo,
                totalProcesses: Math.floor(Math.random() * 20 + 150),
                cpuUsage: Math.floor(Math.random() * 30 + 5) + '%'
            }
        }));
    }


    renderInfoSection = (title, data, icon) => {
        return React.createElement('div', {
            key: title,
            className: 'inspector-section',
            style: {
                marginBottom: '20px',
                padding: '12px',
                border: '1px solid var(--terminal-border)',
                borderRadius: '4px',
                background: 'rgba(0,0,0,0.3)'
            }
        }, [
            React.createElement('div', {
                key: 'title',
                className: 'section-title',
                style: {
                    color: 'var(--terminal-purple)',
                    fontSize: '12px',
                    fontWeight: '600',
                    marginBottom: '8px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px'
                }
            }, [
                React.createElement('span', { key: 'icon' }, icon),
                React.createElement('span', { key: 'text' }, title)
            ]),

            React.createElement('div', {
                key: 'content',
                className: 'section-content'
            }, Object.entries(data).map(([key, value], index) =>
                React.createElement('div', {
                    key: index,
                    className: 'info-row',
                    style: {
                        display: 'flex',
                        justifyContent: 'space-between',
                        marginBottom: '4px',
                        fontSize: '11px'
                    }
                }, [
                    React.createElement('span', {
                        key: 'label',
                        style: { color: 'var(--terminal-text-dim)' }
                    }, key.replace(/([A-Z])/g, ' $1').toLowerCase().replace(/^\w/, c => c.toUpperCase()) + ':'),
                    React.createElement('span', {
                        key: 'value',
                        style: {
                            color: 'var(--terminal-cyan)',
                            fontWeight: '500'
                        }
                    }, value)
                ])
            ))
        ]);
    }

    render() {
        const { collapsed = false, onToggle } = this.props;
        const { systemInfo, networkInfo, processInfo } = this.state;

        return React.createElement('div', {
            className: 'rightbar-content',
            style: {
                display: 'flex',
                flexDirection: 'column',
                height: '100%'
            }
        }, [
            // Header with title and collapse button
            React.createElement('div', {
                key: 'header',
                className: 'rightbar-header',
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
                        color: 'var(--terminal-purple)',
                        fontSize: '14px',
                        fontWeight: '600',
                        fontFamily: 'inherit'
                    }
                }, 'System Inspector'),

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
                        e.target.style.borderColor = 'var(--terminal-purple)';
                        e.target.style.color = 'var(--terminal-purple)';
                    },
                    onMouseLeave: (e) => {
                        e.target.style.borderColor = 'var(--terminal-border)';
                        e.target.style.color = 'var(--terminal-text)';
                    }
                }, collapsed ? '←' : '→')
            ]),

            // Scrollable content area
            !collapsed && React.createElement('div', {
                key: 'content',
                className: 'rightbar-content scrollbar',
                style: {
                    flex: '1',
                    padding: '16px 12px',
                    overflowY: 'auto',
                    overflowX: 'hidden'
                }
            }, [
                this.renderInfoSection('System Info', systemInfo, '💻'),
                this.renderInfoSection('Network', networkInfo, '🌐'),
                this.renderInfoSection('Processes', processInfo, '⚡'),

                // Status indicator
                React.createElement('div', {
                    key: 'status',
                    className: 'status-indicator',
                    style: {
                        padding: '12px',
                        border: '1px solid var(--terminal-green)',
                        borderRadius: '4px',
                        background: 'rgba(124, 58, 237, 0.1)',
                        textAlign: 'center'
                    }
                }, [
                    React.createElement('div', {
                        key: 'status-title',
                        style: {
                            color: 'var(--terminal-green)',
                            fontSize: '12px',
                            fontWeight: '600',
                            marginBottom: '4px'
                        }
                    }, 'System Status'),
                    React.createElement('div', {
                        key: 'status-indicator',
                        style: {
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            gap: '6px',
                            fontSize: '11px',
                            color: 'var(--terminal-text)'
                        }
                    }, [
                        React.createElement('div', {
                            key: 'dot',
                            style: {
                                width: '8px',
                                height: '8px',
                                borderRadius: '50%',
                                background: 'var(--terminal-green)',
                                animation: 'pulse 2s infinite'
                            }
                        }),
                        React.createElement('span', { key: 'text' }, 'Online & Monitoring')
                    ])
                ])
            ])
        ]);
    }
}

// Export for use in other files
window.RightBar = RightBar;