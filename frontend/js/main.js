// js/main.js
import { MapRenderer } from './map-renderer.js';
import { APIClient } from './api-client.js';

class Game {
    constructor() {
        this.api = new APIClient();
        this.mapRenderer = new MapRenderer(document.getElementById('world-map'));
        this.currentLocationId = null;
        
        this.initEventListeners();
    }
    
    initEventListeners() {
        // Старт игры
        document.getElementById('start-game-btn').addEventListener('click', () => {
            const playerName = document.getElementById('player-name-input').value || 'Авантюрист';
            this.startGame(playerName);
        });
        
        // Команда игрока
        document.getElementById('command-input').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.handleCommand(e.target.value);
                e.target.value = '';
            }
        });
        
        // Исследование окрестностей
        document.getElementById('explore-btn').addEventListener('click', () => {
            this.exploreBoundaries();
        });
    }
    
    updateUI(data) {
        if (data.player) {
            this.updatePlayerUI(data.player);
        }
        if (data.current_location) {
            this.updateLocationUI(data.current_location);
        }
        if (data.world_graph) {
            // Обновляем ID текущей локации ПЕРЕД отрисовкой
            this.currentLocationId = data.world_graph.current_location_id;

            this.mapRenderer.render(
                data.world_graph,
                this.currentLocationId,
                (location) => this.handleLocationClick(location)
            );
            this.updateDirections(data.world_graph);
        }
        if (data.narrative) {
            this.addNarrative(data.narrative);
        }
    }

    async startGame(playerName) {
        try {
            const data = await this.api.startGame(playerName);
            
            // Скрываем модалку
            document.getElementById('start-modal').style.display = 'none';
            
            // Используем новый центральный метод
            this.updateUI(data);
            
            this.addNarrative("🎮 Ваше приключение начинается!");

            // Центрируем камеру после первой отрисовки
            this.mapRenderer.centerOnLocation(this.currentLocationId, data.world_graph.nodes);
            
        } catch (error) {
            console.error('Ошибка запуска игры:', error);
            alert('Не удалось подключиться к серверу');
        }
    }
    
    
    async handleLocationClick(location) {
        // Если мы уже в этой локации, ничего не делаем
        if (location.id === this.currentLocationId) {
            this.addNarrative("Вы уже находитесь здесь.");
            return;
        }
        
        // УДАЛЯЕМ СЛОМАННУЮ И НЕНУЖНУЮ ПРОВЕРКУ 'isNeighbor'
        // Если на локацию можно кликнуть, значит, она в списке доступных.
        
        try {
            // Сразу отправляем запрос на перемещение
            const result = await this.api.moveToLocation(location.id);
            
            if (result.success) {
                // Сервер прислал полное обновленное состояние мира
                this.addNarrative(`🚶 Вы переместились в: ${result.current_location.name}`);
                
                // Используем централизованный метод для обновления всего UI
                this.updateUI({
                    player: result.player,
                    current_location: result.current_location,
                    world_graph: result.world_graph,
                    narrative: result.current_location.description
                });

            } else {
                // Если сервер по какой-то причине отклонил перемещение
                this.addNarrative(`🚫 ${result.message}`);
            }
        } catch (error) {
            console.error('Ошибка перемещения:', error);
            this.addNarrative("⚠️ Произошла ошибка при попытке перемещения.");
        }
    }

    async handleCommand(command) {
        if (!command.trim()) return;
        this.addNarrative(`> ${command}`, 'player-command');
        try {
            const result = await this.api.performAction(command);
            this.updateUI(result); // Используем центральный метод
        } catch (error) {
            console.error('Ошибка выполнения команды:', error);
            this.addNarrative("⚠️ Произошла ошибка. Попробуйте ещё раз.");
        }
    }

    async exploreBoundaries() {
        try {
            const result = await this.api.exploreBoundaries();
            if (result.success) {
                this.addNarrative(result.message);
                this.updateUI({ world_graph: result.world_graph }); // Обновляем только карту
            }
        } catch (error) {
            console.error('Ошибка исследования:', error);
        }
    }
       
    updatePlayerUI(playerData) {
        document.getElementById('player-name').textContent = playerData.name;
        document.getElementById('health-text').textContent = `${playerData.hp}/${playerData.max_hp}`;
        
        const healthPercent = (playerData.hp / playerData.max_hp) * 100;
        document.getElementById('health-fill').style.width = `${healthPercent}%`;
        
        // Инвентарь
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
        
        // Теги
        const tagsEl = document.getElementById('location-tags');
        tagsEl.innerHTML = '';
        locationData.tags.forEach(tag => {
            const tagEl = document.createElement('span');
            tagEl.className = 'tag';
            tagEl.textContent = tag;
            tagsEl.appendChild(tagEl);
        });
    }
    
    updateDirections(graphData) {
        const directionsEl = document.getElementById('directions-list');
        directionsEl.innerHTML = '';
        
        // --- ФИНАЛЬНОЕ ИСПРАВЛЕНИЕ ДЛЯ УСТРАНЕНИЯ ДУБЛИКАТОВ ---

        // 1. Находим все рёбра, исходящие из текущей локации
        const outgoingEdges = graphData.edges.filter(e => e.from === this.currentLocationId);
        
        // 2. Создаем Set с ID соседей, чтобы гарантировать уникальность
        const neighborIds = new Set(outgoingEdges.map(e => e.to));
        
        // 3. Собираем полный массив данных о соседях
        const neighbors = [];
        for (const neighborId of neighborIds) {
            const neighborNode = graphData.nodes.find(n => n.id === neighborId);
            const edge = outgoingEdges.find(e => e.to === neighborId); // Находим первое подходящее ребро
            
            if (neighborNode && edge) {
                neighbors.push({
                    ...neighborNode,
                    ...edge.data // Добавляем данные из ребра (distance, condition и т.д.)
                });
            }
        }

        if (neighbors.length === 0) {
            directionsEl.innerHTML = '<p>Исследуйте окрестности, чтобы найти новые пути.</p>';
            return;
        }
        
        // Сортируем соседей по имени для стабильного порядка
        neighbors.sort((a, b) => a.name.localeCompare(b.name));
        
        neighbors.forEach(neighbor => {
            const dirEl = document.createElement('div');
            // Убеждаемся, что locked берется из данных ребра
            const isLocked = neighbor.locked || neighbor.condition;
            dirEl.className = 'direction-item' + (isLocked ? ' locked' : '');
            
            const icon = isLocked ? '🔒' : '➡️';
            const visitedTag = neighbor.visited ? '' : ' <span class="new-tag">НОВОЕ</span>';
            
            dirEl.innerHTML = `
                ${icon} <strong>${neighbor.name}</strong>${visitedTag}
                <br><small>Расстояние: ${neighbor.distance ? Math.round(neighbor.distance) : '?'} шагов</small>
                ${isLocked ? `<br><small class="condition">Требуется: ${neighbor.condition}</small>` : ''}
            `;
            
            if (!isLocked) {
                dirEl.style.cursor = 'pointer';
                dirEl.addEventListener('click', () => this.handleLocationClick(neighbor));
            }
            
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
    
    handleWSMessage(data) {
        // Обработка real-time сообщений
        if (data.type === 'action_result') {
            this.addNarrative(data.narrative);
            this.updatePlayerUI(data.player);
        }
    }
}

// Запуск при загрузке страницы
window.addEventListener('DOMContentLoaded', () => {
    window.game = new Game();
});