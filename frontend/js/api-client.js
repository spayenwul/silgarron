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
    
    // ИЗМЕНЕНО: Метод для получения глобальной карты
    async getWorldMap() {
        const response = await fetch(`${API_BASE}/game/world_map/${this.sessionId}`);
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
}