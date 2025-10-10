export class MapRenderer {
    constructor(svgElement) {
        this.svg = d3.select(svgElement);
        this.width = svgElement.clientWidth;
        this.height = svgElement.clientHeight;

        this.cameraGroup = this.svg.append('g');
        this.edgesGroup = this.cameraGroup.append('g').attr('class', 'edges');
        this.nodesGroup = this.cameraGroup.append('g').attr('class', 'nodes');

        const zoom = d3.zoom().scaleExtent([0.2, 5]).on('zoom', (event) => {
            this.cameraGroup.attr('transform', event.transform);
        });
        this.svg.call(zoom);
        this.zoom = zoom;

        this._setupStyles();
    }

    _getHexagonPath(size) {
        let path = "M";
        for (let i = 0; i < 6; i++) {
            const angle_rad = Math.PI / 180 * (60 * i);
            path += ` ${size * Math.cos(angle_rad)},${size * Math.sin(angle_rad)} L`;
        }
        return path.slice(0, -2) + " Z";
    }
    
    _setupStyles() {
        // ИЗМЕНЕНИЕ: Заменяем эмодзи на надежные буквенные обозначения
        this.locationIcons = {
            'kith_settlement': '[П]', // Поселение
            'pulsating_plains': '[Р]', // Равнины
            'spore_savanna': '[С]',    // Саванна
            'geyser_fields': '[Г]',    // Гейзеры
            'crystal_scar': '[К]',     // Кристаллы
            'megatherium_pastures': '[М]', // Мегатерии
            'biolume_forest': '[Л]',   // Лес
            'neuroflower_meadows': '[Ц]', // Цветы
            'fungal_mangroves': '[Г]', // Грибы
            'silt_flats': '[И]',       // Ил
            'blood_clot_thicket': '[Т]', // Тромб
            'bone_needles': '[Ш]',     // Шпили
            'litho-lichen_slopes': '[Ск]',// Склоны
            'cloud_forest': '[О]',     // Облака
            'ruined_spires': '[Р]',    // Руины
            'wind_caves': '[В]',       // Ветер
            'rolling_hills': '[Х]',    // Холмы
            'broken_lands': '[Рз]',    // Разломы
            'boneyard': '[Ч]',         // Череп
            'fortress_hills': '[Кр]',  // Крепость
            'springheads': '[И]',      // Истоки
            'luminous_fungi_caves': '[ПГ]', // Пещера Грибов
            'wind_tunnels': '[ВТ]',       // Ветровые туннели
            'subterranean_lymph_lake': '[Оз]', // Озеро
            'crystal_geode': '[Ж]',       // Жеода
            'geode_ruins': '[РГ]',        // Руины Геодов
            'default': '[?]'
        };
        this.locationColors = { 'kith_settlement': '#4CAF50', 'pulsating_plains': '#9CCC65', 'spore_savanna': '#FFB74D', 'geyser_fields': '#90A4AE', 'crystal_scar': '#B2EBF2', 'megatherium_pastures': '#A1887F', 'biolume_forest': '#00ACC1', 'neuroflower_meadows': '#BA68C8', 'bone_needles': '#E0E0E0', 'litho-lichen_slopes': '#FF8A65', 'cloud_forest': '#B0BEC5', 'ruined_spires': '#A1887F', 'wind_caves': '#BDBDBD', 'boneyard': '#757575', 'rolling_hills': '#A5D6A7', 'broken_lands': '#BCAAA4', 'fortress_hills': '#795548', 'springheads': '#81C784', 'luminous_fungi_caves': '#FFEB3B', 'wind_tunnels': '#B0BEC5', 'subterranean_lymph_lake': '#4FC3F7', 'crystal_geode': '#E1BEE7', 'geode_ruins': '#A1887F', 'default': '#616161' };
    }

    render(graphData, onNodeClick, current_id = null) {
        const { nodes, edges } = graphData;
        if (!nodes || nodes.length === 0) { this.clear(); return; }

        const isWorldMap = nodes[0].type === 'region';
        const hexSize = isWorldMap ? 100 : 50;
        const fontSize = isWorldMap ? "16px" : "14px";
        const iconFontSize = isWorldMap ? "0px" : "22px";

        // Рендерим СВЯЗИ
        const edgeSelection = this.edgesGroup.selectAll('line').data(edges, d => `${d.from}-${d.to}`);
        edgeSelection.exit().remove();
        const findNodePos = (id) => nodes.find(n => n.id === id)?.position || [0,0];
        edgeSelection.enter().append('line').merge(edgeSelection)
            .attr('x1', d => findNodePos(d.from)[0]).attr('y1', d => findNodePos(d.from)[1])
            .attr('x2', d => findNodePos(d.to)[0]).attr('y2', d => findNodePos(d.to)[1])
            .attr('stroke', '#a0a0a0').attr('stroke-width', isWorldMap ? 2 : 1.5).attr('opacity', 0.5);

        // Рендерим УЗЛЫ
        const nodeGroupSelection = this.nodesGroup.selectAll('g.node').data(nodes, d => d.id);
        nodeGroupSelection.exit().remove();

        const nodeEnter = nodeGroupSelection.enter().append('g').attr('class', 'node')
            .style('cursor', 'pointer')
            .on('click', (event, d) => onNodeClick(d));
            
        nodeEnter.append('path');
        nodeEnter.append('text').attr('class', 'icon').attr('text-anchor', 'middle').attr('dy', '0.35em').attr('fill', 'white').style('pointer-events', 'none');
        nodeEnter.append('text').attr('class', 'label').attr('text-anchor', 'middle').attr('fill', '#e8e8e8').style('opacity', 0).style('pointer-events', 'none');
        
        // ИЗМЕНЕНИЕ: Показываем/скрываем название при наведении
        nodeEnter.on('mouseover', function() {
            d3.select(this).select('text.label').transition().duration(200).style('opacity', 1);
        }).on('mouseout', function() {
            d3.select(this).select('text.label').transition().duration(200).style('opacity', 0);
        });

        const allNodes = nodeGroupSelection.merge(nodeEnter);
        allNodes.attr('transform', d => `translate(${d.position[0]}, ${d.position[1]})`);

        allNodes.select('path')
            .attr('d', this._getHexagonPath(hexSize)) // Устанавливаем размер гекса
            .transition().duration(300)
            .attr('fill', d => isWorldMap ? 'rgba(61, 139, 111, 0.3)' : (this.locationColors[d.type] || this.locationColors['default']))
            .attr('stroke', d => d.id === current_id ? '#ffd700' : 'rgba(150, 150, 150, 0.5)')
            .attr('stroke-width', d => d.id === current_id ? 4 : 2);
        
        allNodes.select('text.icon').attr('font-size', iconFontSize).text(d => isWorldMap ? '' : (this.locationIcons[d.type] || this.locationIcons['default']));
        allNodes.select('text.label').attr('font-size', fontSize).attr('dy', `${hexSize + 20}px`).text(d => d.name).attr('font-weight', d => d.id === current_id ? 'bold' : 'normal');
    }

    centerOnNode(nodeId, nodes) {
        const node = nodes.find(n => n.id === nodeId);
        if (!node) return;
        const [x, y] = node.position;
        const scale = node.type === 'region' ? 0.7 : 1.2;
        const transform = d3.zoomIdentity.translate(this.width / 2, this.height / 2).scale(scale).translate(-x, -y);
        this.svg.transition().duration(750).call(this.zoom.transform, transform);
    }
    
    clear() {
        this.nodesGroup.selectAll('*').remove();
        this.edgesGroup.selectAll('*').remove();
    }
}
