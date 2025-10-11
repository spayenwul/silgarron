/**
 * Body Visualizer - Визуализация состояния тела персонажа
 * Отображает части тела, раны, кровопотерю и эффекты
 */

export class BodyVisualizer {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.bodyParts = ['head', 'neck', 'torso', 'left_arm', 'right_arm', 'left_leg', 'right_leg'];

        // Позиции частей тела для отрисовки (простая схема)
        this.partPositions = {
            head: { x: 150, y: 50, r: 30 },
            neck: { x: 150, y: 90, w: 20, h: 15 },
            torso: { x: 150, y: 130, w: 60, h: 80 },
            left_arm: { x: 90, y: 140, w: 15, h: 70 },
            right_arm: { x: 210, y: 140, w: 15, h: 70 },
            left_leg: { x: 130, y: 220, w: 20, h: 80 },
            right_leg: { x: 170, y: 220, w: 20, h: 80 }
        };
    }

    render(bodyData) {
        if (!bodyData || !bodyData.parts) {
            console.warn('[BodyVisualizer] No body data provided');
            return;
        }

        // Очистить контейнер
        this.container.innerHTML = '';

        // Создать SVG
        const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        svg.setAttribute('width', '300');
        svg.setAttribute('height', '320');
        svg.style.margin = '0 auto';
        svg.style.display = 'block';

        // Отрисовать каждую часть тела
        for (const [partName, partData] of Object.entries(bodyData.parts)) {
            this.drawBodyPart(svg, partName, partData);
        }

        this.container.appendChild(svg);
    }

    drawBodyPart(svg, partName, partData) {
        const pos = this.partPositions[partName];
        if (!pos) return;

        // Определить цвет на основе integrity
        const integrity = partData.integrity || 1.0;
        const color = this.getIntegrityColor(integrity);

        let element;

        // Голова - круг
        if (partName === 'head') {
            element = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
            element.setAttribute('cx', pos.x);
            element.setAttribute('cy', pos.y);
            element.setAttribute('r', pos.r);
        } else {
            // Остальные части - прямоугольники
            element = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
            element.setAttribute('x', pos.x - (pos.w || 20) / 2);
            element.setAttribute('y', pos.y);
            element.setAttribute('width', pos.w || 20);
            element.setAttribute('height', pos.h || 20);
            element.setAttribute('rx', 5); // Скругление
        }

        element.setAttribute('fill', color);
        element.setAttribute('stroke', '#5cd9a8');
        element.setAttribute('stroke-width', partData.functional ? '2' : '1');
        element.setAttribute('opacity', partData.functional ? '0.9' : '0.5');
        element.classList.add('body-part');
        element.setAttribute('data-part', partName);

        // Tooltip
        element.addEventListener('mouseenter', (e) => {
            this.showTooltip(e, partName, partData);
        });
        element.addEventListener('mouseleave', () => {
            this.hideTooltip();
        });

        svg.appendChild(element);

        // Лейбл
        const label = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        label.setAttribute('x', pos.x);
        label.setAttribute('y', pos.y + (pos.h ? pos.h + 15 : pos.r + 20));
        label.setAttribute('text-anchor', 'middle');
        label.setAttribute('class', 'body-part-label');
        label.textContent = this.translatePartName(partName);

        svg.appendChild(label);
    }

    getIntegrityColor(integrity) {
        // Зелёный -> Жёлтый -> Красный
        if (integrity > 0.7) {
            return `rgb(${Math.floor((1 - integrity) * 255 * 3)}, 200, 100)`;
        } else if (integrity > 0.3) {
            return `rgb(255, ${Math.floor(integrity * 200)}, 50)`;
        } else {
            return `rgb(199, ${Math.floor(integrity * 100)}, 68)`;
        }
    }

    translatePartName(name) {
        const translations = {
            head: 'Голова',
            neck: 'Шея',
            torso: 'Торс',
            left_arm: 'Л.Рука',
            right_arm: 'П.Рука',
            left_leg: 'Л.Нога',
            right_leg: 'П.Нога'
        };
        return translations[name] || name;
    }

    showTooltip(event, partName, partData) {
        // Создать всплывающую подсказку
        const tooltip = document.createElement('div');
        tooltip.id = 'body-tooltip';
        tooltip.style.position = 'absolute';
        tooltip.style.background = 'rgba(15, 22, 33, 0.95)';
        tooltip.style.border = '1px solid var(--border-glow)';
        tooltip.style.borderRadius = '8px';
        tooltip.style.padding = '10px';
        tooltip.style.fontSize = '12px';
        tooltip.style.zIndex = '9999';
        tooltip.style.pointerEvents = 'none';
        tooltip.style.maxWidth = '200px';

        tooltip.innerHTML = `
            <strong style="color: var(--accent-glow)">${this.translatePartName(partName)}</strong><br>
            Целостность: ${(partData.integrity * 100).toFixed(0)}%<br>
            Раны: ${partData.wounds_count || 0}<br>
            Кровотечение: ${(partData.total_bleeding || 0).toFixed(1)} мл/сек<br>
            Боль: ${(partData.pain_level || 0).toFixed(1)}/10<br>
            ${partData.functional ? '<span style="color: #5cd9a8">✓ Функционирует</span>' : '<span style="color: #c74444">✗ Не функционирует</span>'}
        `;

        document.body.appendChild(tooltip);

        // Позиционировать рядом с курсором
        tooltip.style.left = (event.pageX + 10) + 'px';
        tooltip.style.top = (event.pageY + 10) + 'px';
    }

    hideTooltip() {
        const tooltip = document.getElementById('body-tooltip');
        if (tooltip) {
            tooltip.remove();
        }
    }

    updateBloodVolume(current, max) {
        const bloodFill = document.getElementById('blood-fill');
        const bloodText = document.getElementById('blood-text');

        if (bloodFill && bloodText) {
            const percentage = (current / max) * 100;
            bloodFill.style.width = percentage + '%';
            bloodText.textContent = `${Math.floor(current)} / ${Math.floor(max)} мл`;
        }
    }

    updateConsciousness(value) {
        const consciousnessSpan = document.getElementById('consciousness');
        if (consciousnessSpan) {
            const percentage = (value * 100).toFixed(0);
            consciousnessSpan.textContent = percentage + '%';

            // Цвет в зависимости от уровня
            if (value > 0.7) {
                consciousnessSpan.style.color = '#5cd9a8';
            } else if (value > 0.3) {
                consciousnessSpan.style.color = '#ff9800';
            } else {
                consciousnessSpan.style.color = '#c74444';
            }
        }
    }

    updateWounds(wounds) {
        const woundsList = document.getElementById('wounds-list');
        if (!woundsList) return;

        if (!wounds || wounds.length === 0) {
            woundsList.innerHTML = '<li style="color: var(--text-secondary); font-style: italic;">Нет активных ран</li>';
            return;
        }

        woundsList.innerHTML = wounds.map(wound => `
            <li>
                <strong>${this.translatePartName(wound.body_part)}</strong>:
                ${wound.type} (${wound.depth_cm}см) -
                ${wound.bleeding_rate.toFixed(1)} мл/сек
            </li>
        `).join('');
    }

    updateStatusEffects(effects) {
        const effectsList = document.getElementById('effects-list');
        if (!effectsList) return;

        if (!effects || effects.length === 0) {
            effectsList.innerHTML = '<span style="color: var(--text-secondary); font-size: 12px;">Нет активных эффектов</span>';
            return;
        }

        effectsList.innerHTML = effects.map(effect => {
            const isDanger = effect.type === 'bleeding' || effect.type === 'shock';
            return `
                <span class="effect-badge ${isDanger ? 'danger' : ''}">
                    ${effect.type} (${(effect.severity * 100).toFixed(0)}%)
                </span>
            `;
        }).join('');
    }
}
