/**
 * Terminal Header Component
 * Provides the terminal-style header with title and help button
 */

class TerminalHeader extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            isHelpVisible: false
        };
    }

    showHelp = () => {
        const helpContent = `
═══════════════════════════════════════════════════════════
                        GUÍA DE USO - MCP OPEN CLIENT
═══════════════════════════════════════════════════════════

DESCRIPCIÓN:
  MCP Open Client es un cliente web moderno para el protocolo
  Model Context Protocol (MCP), diseñado con estética de
  terminal para una experiencia familiar de línea de comandos.

CARACTERÍSTICAS:
  • Interfaz de terminal con tema oscuro
  • Conexión a servidores MCP
  • Comunicación WebSocket en tiempo real
  • Backend FastAPI de alto rendimiento
  • Frontend React con componentes Ant Design

COMANDOS BÁSICOS:
  connect <url>     - Conectar a servidor MCP
  disconnect        - Desconectar servidor actual
  list              - Listar servidores disponibles
  status            - Mostrar estado del sistema
  tools             - Listar herramientas disponibles
  clear             - Limpiar pantalla
  help              - Mostrar esta ayuda

SHORTCUTS:
  Ctrl+C           - Cancelar operación actual
  Ctrl+L           - Limpiar terminal
  ↑/↓              - Historial de comandos
  Tab              - Autocompletar comando

CONFIGURACIÓN:
  La configuración se puede realizar desde la interfaz web
  o editando el archivo de configuración JSON.

Para más información, visita: /docs
═══════════════════════════════════════════════════════════`;

        // Create modal-like help display
        const helpModal = document.createElement('div');
        helpModal.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.9);
            z-index: 9999;
            display: flex;
            align-items: center;
            justify-content: center;
            font-family: inherit;
        `;

        const helpBox = document.createElement('div');
        helpBox.style.cssText = `
            background: var(--terminal-bg-light);
            border: 1px solid var(--terminal-green);
            border-radius: 4px;
            padding: 24px;
            max-width: 800px;
            max-height: 80vh;
            overflow-y: auto;
            color: var(--terminal-text);
            font-family: inherit;
            font-size: 12px;
            line-height: 1.4;
            white-space: pre-wrap;
            box-shadow: 0 0 20px rgba(124, 58, 237, 0.5);
        `;

        helpBox.textContent = helpContent;

        const closeButton = document.createElement('button');
        closeButton.textContent = 'Presiona ESC o Click para cerrar';
        closeButton.style.cssText = `
            display: block;
            margin: 16px auto 0;
            padding: 8px 16px;
            background: transparent;
            border: 1px solid var(--terminal-green);
            color: var(--terminal-green);
            font-family: inherit;
            border-radius: 4px;
            cursor: pointer;
        `;

        helpBox.appendChild(closeButton);
        helpModal.appendChild(helpBox);
        document.body.appendChild(helpModal);

        // Close handlers
        const closeHelp = () => document.body.removeChild(helpModal);
        helpModal.addEventListener('click', closeHelp);
        closeButton.addEventListener('click', closeHelp);
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') closeHelp();
        }, { once: true });
    }

    render() {
        return React.createElement('div', {
            className: 'terminal-header'
        }, [
            // Terminal title section
            React.createElement('div', {
                key: 'title',
                className: 'terminal-title'
            }, [
                React.createElement('span', {
                    key: 'prompt',
                    className: 'terminal-prompt'
                }, 'mcp@client:'),
                React.createElement('span', {
                    key: 'path',
                    className: 'terminal-path'
                }, '~/open-client$'),
                React.createElement('span', {
                    key: 'title-text',
                    className: 'terminal-title-text'
                }, 'MCP Open Client')
            ]),

            // Help button
            React.createElement('button', {
                key: 'help-btn',
                className: 'help-button',
                onClick: this.showHelp
            }, [
                React.createElement('span', {
                    key: 'icon',
                    className: 'help-icon'
                }, '?'),
                React.createElement('span', {
                    key: 'text'
                }, 'Guía de uso')
            ])
        ]);
    }
}

// Export for use in other files
window.TerminalHeader = TerminalHeader;