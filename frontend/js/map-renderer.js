// js/map-renderer.js
export class MapRenderer {
    constructor(svgElement) {
        this.svg = d3.select(svgElement);
        this.width = svgElement.clientWidth;
        this.height = svgElement.clientHeight;
        
        // Группы для слоёв
        this.edgesGroup = this.svg.append('g').attr('class', 'edges');
        this.nodesGroup = this.svg.append('g').attr('class', 'nodes');
        
        // Zoom и pan
        const zoom = d3.zoom()
            .scaleExtent([0.5, 3])
            .on('zoom', (event) => {
                this.edgesGroup.attr('transform', event.transform);
                this.nodesGroup.attr('transform', event.transform);
            });
        
        this.svg.call(zoom);
        
        // Стили для разных типов локаций
        this.locationIcons = {
            'kith_settlement': '🏘️', // Поселение
            'pulsating_plains': '〰️', // Пульсирующие равнины
            'spore_savanna': '🍄', // Споровая саванна
            'geyser_fields': '💨', // Гейзерные поля
            'biolume_forest': '🌳', // Биолюмный лес
            'neuroflower_meadows': '🌸', // Луга Нейроцветов
            'bone_needles': '🏔️', // Костяные иглы
            'litho-lichen_slopes': '🌄', // Лишайниковые склоны
            'cloud_forest': '☁️', // Облачный лес
            'ruined_spires': '🏛️', // Разрушенные шпили
            'wind_caves': '🌬️', // Ветряные пещеры
            'rolling_hills': ' hills ', // Холмы (текстовая иконка как пример)
            'broken_lands': '🏜️', // Разломы
            'boneyard': '💀', // Костяное кладбище
            'default': '❓' // Иконка по умолчанию
        };
        
        this.locationColors = {
            'kith_settlement': '#4CAF50', // Зеленый (безопасный)
            'pulsating_plains': '#9CCC65', // Светло-зеленый
            'spore_savanna': '#FFB74D', // Оранжевый
            'geyser_fields': '#90A4AE', // Серый
            'biolume_forest': '#00ACC1', // Бирюзовый
            'neuroflower_meadows': '#BA68C8', // Фиолетовый
            'bone_needles': '#E0E0E0', // Белый (кости)
            'litho-lichen_slopes': '#FF8A65', // Коралловый
            'cloud_forest': '#B0BEC5', // Голубовато-серый
            'ruined_spires': '#A1887F', // Коричневый (руины)
            'wind_caves': '#BDBDBD', // Светло-серый
            'boneyard': '#757575', // Темно-серый
            'default': '#616161' // Цвет по умолчанию
        };
    }
    
    render(graphData, currentLocationId, onLocationClick) {
        const { nodes, edges } = graphData;
        
        // Рендерим связи (edges)
        const edgeSelection = this.edgesGroup
            .selectAll('line')
            .data(edges, d => `${d.from}-${d.to}`);
        
        edgeSelection.exit().remove();
        
        edgeSelection.enter()
            .append('line')
            .merge(edgeSelection)
            .attr('x1', d => this._getNode(nodes, d.from).position[0])
            .attr('y1', d => this._getNode(nodes, d.from).position[1])
            .attr('x2', d => this._getNode(nodes, d.to).position[0])
            .attr('y2', d => this._getNode(nodes, d.to).position[1])
            .attr('stroke', d => d.data.locked ? '#B71C1C' : '#757575')
            .attr('stroke-width', 2)
            .attr('stroke-dasharray', d => d.data.locked ? '5,5' : 'none')
            .attr('opacity', 0.6);
        
        // Рендерим локации (nodes)
        const nodeSelection = this.nodesGroup
            .selectAll('g.location-node')
            .data(nodes, d => d.id);
        
        nodeSelection.exit().remove();
        
        const nodeEnter = nodeSelection.enter()
            .append('g')
            .attr('class', 'location-node')
            .attr('transform', d => `translate(${d.position[0]}, ${d.position[1]})`)
            .style('cursor', 'pointer')
            .on('click', (event, d) => onLocationClick(d));
        
        // Круг фона
        nodeEnter.append('circle')
            .attr('r', 30)
            .attr('fill', d => {
                if (d.id === currentLocationId) return '#FFC107'; // Текущая - жёлтая
                if (d.visited) return this.locationColors[d.type] || '#9E9E9E';
                return '#BDBDBD'; // Неоткрытая - серая
            })
            .attr('stroke', d => d.id === currentLocationId ? '#FF6F00' : '#424242')
            .attr('stroke-width', d => d.id === currentLocationId ? 4 : 2);
        
        // Иконка
        nodeEnter.append('text')
            .attr('text-anchor', 'middle')
            .attr('dy', '0.35em')
            .attr('font-size', '24px')
            .text(d => this.locationIcons[d.type] || this.locationIcons['default']); // Используем иконку по умолчанию
        
        // Название
        nodeEnter.append('text')
            .attr('text-anchor', 'middle')
            .attr('dy', '45px')
            .attr('font-size', '12px')
            .attr('fill', '#212121')
            .text(d => d.name);
        
        // Индикатор "новое"
        nodeEnter.filter(d => !d.visited)
            .append('circle')
            .attr('cx', 20)
            .attr('cy', -20)
            .attr('r', 5)
            .attr('fill', '#F44336');
        
        // Обновляем существующие узлы
        nodeSelection.merge(nodeEnter)
            .select('circle')
            .transition()
            .duration(300)
            .attr('fill', d => {
                if (d.id === currentLocationId) return '#FFC107';
                if (d.visited) return this.locationColors[d.type] || '#9E9E9E';
                return '#BDBDBD';
            })
            .attr('stroke', d => d.id === currentLocationId ? '#FF6F00' : '#424242')
            .attr('stroke-width', d => d.id === currentLocationId ? 4 : 2);
    }
    
    _getNode(nodes, nodeId) {
        return nodes.find(n => n.id === nodeId);
    }
    
    centerOnLocation(locationId, nodes) {
        const node = nodes.find(n => n.id === locationId);
        if (!node) return;
        
        const [x, y] = node.position;
        const scale = 1.5;
        
        this.svg.transition()
            .duration(750)
            .call(
                d3.zoom().transform,
                d3.zoomIdentity
                    .translate(this.width / 2, this.height / 2)
                    .scale(scale)
                    .translate(-x, -y)
            );
    }
}
