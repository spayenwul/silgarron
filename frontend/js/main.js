// js/main.js
import { MapRenderer } from './map-renderer.js';
import { APIClient } from './api-client.js';

class Game {
    constructor() {
        this.api = new APIClient();
        this.mapRenderer = new MapRenderer(document.getElementById('world-map'));
        this.currentLocationId = null;
        this.currentRegionId = null;
        this.currentView = 'local';
        this.initEventListeners();
    }
    
    initEventListeners() {
        document.getElementById('start-journey-btn').addEventListener('click', () => this.startGame(document.getElementById('player-name').value || 'Странник'));
        document.getElementById('command-input').addEventListener('keypress', e => { if (e.key === 'Enter') { this.handleCommand(e.target.value); e.target.value = ''; } });
        document.getElementById('explore-btn').addEventListener('click', () => this.exploreBoundaries());
        document.getElementById('world-map-btn').addEventListener('click', () => (this.currentView === 'local') ? this.displayWorldMap() : this.displayLocalMap());
    }
    
    async displayWorldMap() {
        this.currentView = 'world';
        document.getElementById('map-title').textContent = '🌍 Карта Мира';
        document.getElementById('world-map-btn').textContent = '↩️ К Региону';
        this.addNarrative("🗺️ Вы смотрите на карту мира.");
        const worldMapData = await this.api.getWorldMap();
        this.mapRenderer.render(worldMapData, (region) => this.handleRegionClick(region), this.currentRegionId);
        this.mapRenderer.centerOnNode(this.currentRegionId, worldMapData.nodes);
    }

    async displayLocalMap(graphData = null) {
        this.currentView = 'local';
        document.getElementById('map-title').textContent = '📍 Карта Региона';
        document.getElementById('world-map-btn').textContent = '🌍 Карта Мира';
        if (!graphData) {
            const state = await this.api.performAction("");
            graphData = state.world_graph;
        }
        this.mapRenderer.render(graphData, (biome) => this.handleBiomeClick(biome), this.currentLocationId);
        this.mapRenderer.centerOnNode(this.currentLocationId, graphData.nodes);
    }
    
    async handleRegionClick(region) {
        if (region.id === this.currentRegionId) {
            this.addNarrative(`↩️ Вы возвращаетесь к исследованию региона "${region.name}".`);
            this.displayLocalMap();
        } else {
            this.addNarrative(`Вы смотрите на далекий регион "${region.name}". Чтобы попасть туда, нужно найти путь на локальной карте.`);
        }
    }

    async handleBiomeClick(biome) {
        if (biome.id === this.currentLocationId) { this.addNarrative("Вы уже здесь."); return; }
        try {
            const result = await this.api.moveToLocation(biome.id);
            if (result.success) {
                this.addNarrative(`🚶 Вы переместились в: ${result.current_location.name}`);
                this.updateUI(result);
            } else { this.addNarrative(`🚫 ${result.message}`); }
        } catch (error) { this.addNarrative("⚠️ Ошибка при перемещении."); }
    }

    async startGame(playerName) {
        document.getElementById('registration-screen').classList.add('hidden');
        document.getElementById('loading-screen').classList.add('active');
        try {
            const data = await this.api.startGame(playerName);
            document.getElementById('loading-screen').classList.remove('active');
            document.getElementById('game-container').classList.add('active');
            this.addNarrative("🎮 Ваше приключение начинается!");
            this.updateUI(data);
        } catch (error) {
            alert('Не удалось запустить игру. Проверьте консоль сервера.');
            document.getElementById('loading-screen').classList.remove('active');
            document.getElementById('registration-screen').classList.remove('hidden');
        }
    }
    
    async handleCommand(command) {
        if (!command.trim()) return;
        this.addNarrative(`> ${command}`, 'player-command');
        try { this.updateUI(await this.api.performAction(command)); } 
        catch (error) { this.addNarrative("⚠️ Произошла ошибка."); }
    }

    async exploreBoundaries() {
        this.addNarrative("🧭 Вы осматриваете горизонт в поисках новых земель...");
        try {
            // ИЗМЕНЕНИЕ: Теперь мы просто получаем сообщение, а не карту.
            const result = await this.api.exploreBoundaries();
            if (result.success) {
                this.addNarrative(result.message);
                // Вид карты больше не переключается автоматически.
            }
        } catch (error) { console.error('Ошибка исследования:', error); }
    }
       
    updateUI(data) {
        if (data.player) this.updatePlayerUI(data.player);
        if (data.current_location) this.updateLocationUI(data.current_location);
        if (data.narrative) this.addNarrative(data.narrative);
        if (data.world_graph && data.world_graph.nodes.length > 0) {
            const currentBiome = data.world_graph.nodes.find(n => n.id === data.world_graph.current_location_id);
            if (currentBiome) {
                // Пытаемся найти ID родительского региона в данных биома (нужно добавить это в API)
                const parentRegionId = this.findParentRegion(currentBiome, data.world_graph);
                if(parentRegionId) this.currentRegionId = parentRegionId;
            }
            this.currentLocationId = data.world_graph.current_location_id;
            this.updateDirections(data.world_graph);
            if (this.currentView === 'local') {
                this.displayLocalMap(data.world_graph);
            }
        }
    }

    findParentRegion(biome, graph) {
        // Это "костыль", т.к. API не отдает ID региона вместе с локальной картой.
        // В идеале, API должен его присылать.
        // Пока мы не можем его найти надежно, но это не критично.
        return null; 
    }
    
    // ... (остальные вспомогательные функции без изменений) ...

    updatePlayerUI(playerData) { 
        document.getElementById('player-name-display').textContent = playerData.name;
        document.getElementById('health-text').textContent = `${playerData.hp}/${playerData.max_hp}`;
        const healthPercent = (playerData.hp / playerData.max_hp) * 100;
        document.getElementById('health-fill').style.width = `${healthPercent}%`;
        const inventoryEl = document.getElementById('inventory');
        inventoryEl.innerHTML = '<h4>Инвентарь:</h4>';
        if (playerData.inventory && playerData.inventory.items) {
            playerData.inventory.items.forEach(item => {
                const itemEl = document.createElement('div');
                itemEl.className = 'inventory-item';
                itemEl.textContent = item.name;
                itemEl.title = item.description;
                inventoryEl.appendChild(itemEl);
            });
        }
    }
    updateLocationUI(locationData) {
        document.getElementById('location-name').textContent = locationData.name;
        document.getElementById('location-description').textContent = locationData.description;
        const tagsEl = document.getElementById('location-tags');
        tagsEl.innerHTML = '';
        if(locationData.tags) locationData.tags.forEach(tag => {
            const tagEl = document.createElement('span');
            tagEl.className = 'tag';
            tagEl.textContent = tag;
            tagsEl.appendChild(tagEl);
        });
    }
    updateDirections(graphData) {
        const directionsEl = document.getElementById('directions-list');
        directionsEl.innerHTML = '';
        const outgoingEdges = graphData.edges.filter(e => e.from === this.currentLocationId);
        const neighborIds = new Set(outgoingEdges.map(e => e.to).concat(graphData.edges.filter(e => e.to === this.currentLocationId).map(e => e.from)));
        const neighbors = Array.from(neighborIds).map(id => graphData.nodes.find(n => n.id === id)).filter(Boolean);

        if (neighbors.length === 0) {
            directionsEl.innerHTML = '<p>Путей не видно. Попробуйте исследовать окрестности.</p>';
            return;
        }
        neighbors.sort((a, b) => a.name.localeCompare(b.name)).forEach(neighbor => {
            const dirEl = document.createElement('div');
            dirEl.className = 'direction-item';
            const visitedTag = neighbor.visited ? '' : ' <span class="new-tag">НОВОЕ</span>';
            dirEl.innerHTML = `➡️ <strong>${neighbor.name}</strong>${visitedTag}`;
            dirEl.addEventListener('click', () => this.handleBiomeClick(neighbor));
            directionsEl.appendChild(dirEl);
        });
    }
    addNarrative(text, className = '') {
        const logEl = document.getElementById('narrative-log');
        const entry = document.createElement('div');
        entry.className = `narrative-entry ${className}`;
        entry.textContent = text;
        logEl.appendChild(entry);
        logEl.scrollTop = logEl.scrollHeight;
    }
}

window.addEventListener('DOMContentLoaded', () => { window.game = new Game(); });