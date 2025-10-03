// js/api-client.js
const API_BASE = 'http://localhost:8000';

export class APIClient {
    constructor() {
        this.sessionId = null;
    }
    
    async startGame(playerName) {
        const response = await fetch(`${API_BASE}/game/start`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ player_name: playerName })
        });
        
        const data = await response.json();
        this.sessionId = data.session_id;
        
        return data;
    }
    
    async getWorldGraph() {
        const response = await fetch(`${API_BASE}/game/world/${this.sessionId}`);
        return response.json();
    }
    
    async moveToLocation(targetLocationId) {
        const response = await fetch(`${API_BASE}/game/move/${this.sessionId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ target_location_id: targetLocationId })
        });
        
        return response.json();
    }
    
    async performAction(command) {
        const response = await fetch(`${API_BASE}/game/action/${this.sessionId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ command })
        });
        
        return response.json();
    }
    
    async exploreBoundaries() {
        const response = await fetch(`${API_BASE}/game/explore/${this.sessionId}`);
        return response.json();
    }
    
    connectWebSocket(onMessage) {
        this.ws = new WebSocket(`ws://localhost:8000/ws/${this.sessionId}`);
        
        this.ws.onopen = () => console.log('WebSocket connected');
        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            onMessage(data);
        };
        this.ws.onerror = (error) => console.error('WebSocket error:', error);
    }
    
    sendWSMessage(type, payload) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({ type, ...payload }));
        }
    }
}