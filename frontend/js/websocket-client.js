/**
 * WebSocket Client - Real-time communication with server
 */

export class WSClient {
    constructor(sessionId, messageHandlers = {}) {
        this.sessionId = sessionId;
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnects = 5;
        this.reconnectDelay = 2000; // ms
        this.handlers = messageHandlers;
        this.connected = false;
    }

    connect() {
        const wsUrl = `ws://localhost:8000/ws/${this.sessionId}`;
        console.log(`[WS] Connecting to ${wsUrl}`);

        try {
            this.ws = new WebSocket(wsUrl);

            this.ws.onopen = () => {
                console.log('[WS] Connected');
                this.connected = true;
                this.reconnectAttempts = 0;

                if (this.handlers.onConnect) {
                    this.handlers.onConnect();
                }
            };

            this.ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.handleMessage(data);
                } catch (err) {
                    console.error('[WS] Failed to parse message:', err);
                }
            };

            this.ws.onerror = (error) => {
                console.error('[WS] Error:', error);
                if (this.handlers.onError) {
                    this.handlers.onError(error);
                }
            };

            this.ws.onclose = () => {
                console.log('[WS] Connection closed');
                this.connected = false;

                if (this.handlers.onDisconnect) {
                    this.handlers.onDisconnect();
                }

                this.attemptReconnect();
            };

        } catch (err) {
            console.error('[WS] Connection failed:', err);
        }
    }

    handleMessage(data) {
        console.log('[WS] Received:', data.type);

        switch (data.type) {
            case 'initial_state':
                if (this.handlers.onInitialState) {
                    this.handlers.onInitialState(data.data);
                }
                break;

            case 'body_update':
                if (this.handlers.onBodyUpdate) {
                    this.handlers.onBodyUpdate(data.data);
                }
                break;

            case 'action_result':
                if (this.handlers.onActionResult) {
                    this.handlers.onActionResult(data.data);
                }
                break;

            case 'narrative':
                if (this.handlers.onNarrative) {
                    this.handlers.onNarrative(data.text);
                }
                break;

            case 'combat_event':
                if (this.handlers.onCombatEvent) {
                    this.handlers.onCombatEvent(data.data);
                }
                break;

            case 'pong':
                // Keepalive response
                break;

            default:
                console.warn('[WS] Unknown message type:', data.type);
        }
    }

    send(message) {
        if (!this.connected || !this.ws) {
            console.warn('[WS] Not connected, cannot send message');
            return false;
        }

        if (this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(message));
            return true;
        }

        return false;
    }

    sendCommand(command) {
        return this.send({
            type: 'command',
            command: command
        });
    }

    ping() {
        return this.send({ type: 'ping' });
    }

    attemptReconnect() {
        if (this.reconnectAttempts >= this.maxReconnects) {
            console.error('[WS] Max reconnection attempts reached');
            return;
        }

        this.reconnectAttempts++;
        console.log(`[WS] Reconnecting in ${this.reconnectDelay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnects})`);

        setTimeout(() => {
            this.connect();
        }, this.reconnectDelay);
    }

    disconnect() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
            this.connected = false;
        }
    }
}
