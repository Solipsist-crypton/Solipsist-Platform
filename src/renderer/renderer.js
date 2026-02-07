// src/renderer/renderer.js - ВЕРСІЯ БЕЗ UPDATE
document.addEventListener('DOMContentLoaded', () => {
    // Елементи UI
    const uiElements = {
        refreshBtn: document.getElementById('refresh-btn'),
        tableBody: document.getElementById('table-body'),
        foundCount: document.getElementById('found-count'),
        maxSpread: document.getElementById('max-spread'),
        avgSpread: document.getElementById('avg-spread'),
        updateTime: document.getElementById('update-time'),
        themeToggle: document.getElementById('theme-toggle'),
        autoRefreshToggle: document.getElementById('auto-refresh'),
        searchInput: document.getElementById('search-input'),
        sortSelect: document.getElementById('sort-select'),
        loadingOverlay: document.getElementById('loading-overlay')
    };

    let state = {
        autoRefreshInterval: null,
        currentData: [],
        isLoading: false,
        config: {
            theme: 'dark',
            autoRefresh: true
        }
    };

    // Ініціалізація
    init();

    async function init() {
        console.log('🔵 Ініціалізація додатку...');
        setupEventListeners();
        await loadConfig();
        await fetchArbitrageData();
        if (state.config.autoRefresh) {
            startAutoRefresh();
        }
    }

    function setupEventListeners() {
        // Кнопка оновлення
        if (uiElements.refreshBtn) {
            uiElements.refreshBtn.addEventListener('click', fetchArbitrageData);
        }

        // Перемикач теми
        if (uiElements.themeToggle) {
            uiElements.themeToggle.addEventListener('change', toggleTheme);
        }

        // Автоматичне оновлення
        if (uiElements.autoRefreshToggle) {
            uiElements.autoRefreshToggle.checked = state.config.autoRefresh;
            uiElements.autoRefreshToggle.addEventListener('change', (e) => {
                state.config.autoRefresh = e.target.checked;
                if (state.config.autoRefresh) {
                    startAutoRefresh();
                } else {
                    stopAutoRefresh();
                }
                saveConfig();
            });
        }

        // Пошук
        if (uiElements.searchInput) {
            uiElements.searchInput.addEventListener('input', debounce(filterTable, 300));
        }

        // Сортування
        if (uiElements.sortSelect) {
            uiElements.sortSelect.addEventListener('change', sortTable);
        }

        // Обробник для кнопок торгівлі
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('action-buy')) {
                const pair = e.target.dataset.pair || 'BTCUSDT';
                window.open(`https://www.binance.com/en/trade/${pair}`, '_blank');
            }
        });
    }

    // Основна функція отримання даних
    async function fetchArbitrageData() {
        if (state.isLoading) return;
        
        state.isLoading = true;
        showLoading(true);

        try {
            console.log('🔄 Отримання даних арбітражу...');
            
            // Перевірка доступності API
            if (!window.electronAPI?.getArbitrage) {
                throw new Error('API не доступне');
            }

            const data = await window.electronAPI.getArbitrage();
            
            if (data.error) {
                throw new Error(data.error);
            }

            state.currentData = data.opportunities || [];
            
            // Оновлення UI
            updateUI(data);
            updateTable(state.currentData);
            
            // Сповіщення про успіх
            if (state.currentData.length > 0) {
                showNotification(
                    `Знайдено ${state.currentData.length} можливостей`,
                    `Максимальний спред: ${Math.max(...state.currentData.map(d => d.spread || 0)).toFixed(2)}%`
                );
            }
            
            console.log(`✅ Отримано ${state.currentData.length} можливостей`);

        } catch (error) {
            console.error('❌ Помилка отримання даних:', error);
            showError(`Не вдалося отримати дані: ${error.message}`);
        } finally {
            state.isLoading = false;
            showLoading(false);
        }
    }

    // Оновлення статистики
    function updateUI(data) {
        const opportunities = data.opportunities || [];
        const stats = data.stats || {};

        // Оновлення статистики
        if (uiElements.foundCount) {
            uiElements.foundCount.textContent = opportunities.length;
        }

        if (uiElements.maxSpread) {
            uiElements.maxSpread.textContent = stats.max_spread 
                ? `${stats.max_spread.toFixed(2)}%` 
                : '0%';
        }

        if (uiElements.avgSpread) {
            uiElements.avgSpread.textContent = stats.avg_spread 
                ? `${stats.avg_spread.toFixed(2)}%` 
                : '0%';
        }

        // Час оновлення
        if (uiElements.updateTime) {
            const now = new Date();
            uiElements.updateTime.textContent = now.toLocaleTimeString('uk-UA');
            uiElements.updateTime.title = now.toLocaleString('uk-UA');
        }

        // Оновлення заголовка вікна
        if (opportunities.length > 0) {
            document.title = `Solipsist Platform (${opportunities.length} можливостей)`;
        }
    }

    // Оновлення таблиці
    function updateTable(data) {
        if (!uiElements.tableBody) return;

        uiElements.tableBody.innerHTML = '';

        if (!data || data.length === 0) {
            uiElements.tableBody.innerHTML = `
                <tr>
                    <td colspan="7" class="empty-state">
                        <div class="empty-icon">🔍</div>
                        <p>Арбітражних можливостей не знайдено</p>
                        <small>Спробуйте оновити дані або змінити фільтри</small>
                    </div>
                </tr>
            `;
            return;
        }

        data.forEach((opportunity, index) => {
            if (!opportunity) return;

            const row = document.createElement('tr');
            row.className = 'opportunity-row';
            row.dataset.index = index;
            
            const spreadClass = getSpreadClass(opportunity.spread || 0);
            const formattedPair = formatPair(opportunity.pair || 'N/A');
            const profitPercent = ((opportunity.sell_price - opportunity.buy_price) / opportunity.buy_price * 100).toFixed(2);

            row.innerHTML = `
                <td>
                    <div class="pair-cell">
                        <span class="pair-symbol">${formattedPair}</span>
                        <span class="pair-exchanges">${opportunity.exchanges || 0} бірж</span>
                    </div>
                </td>
                <td>
                    <div class="spread-cell">
                        <span class="spread-badge ${spreadClass}">
                            ${(opportunity.spread || 0).toFixed(2)}%
                        </span>
                        <div class="profit-indicator">
                            <span class="profit-arrow">↗</span>
                            <span class="profit-text">${profitPercent}%</span>
                        </div>
                    </div>
                </td>
                <td>
                    <div class="exchange-cell buy-exchange">
                        <span class="exchange-badge">${opportunity.buy || 'N/A'}</span>
                        <span class="exchange-price">$${(opportunity.buy_price || 0).toFixed(4)}</span>
                    </div>
                </td>
                <td>
                    <div class="exchange-cell sell-exchange">
                        <span class="exchange-badge">${opportunity.sell || 'N/A'}</span>
                        <span class="exchange-price">$${(opportunity.sell_price || 0).toFixed(4)}</span>
                    </div>
                </td>
                <td>
                    <div class="volume-cell">
                        <div class="volume-bars">
                            <div class="volume-bar buy-volume" style="width: ${getVolumePercentage(opportunity.buy_volume, opportunity.sell_volume)}%">
                                <span>$${formatVolume(opportunity.buy_volume || 0)}</span>
                            </div>
                            <div class="volume-bar sell-volume" style="width: ${100 - getVolumePercentage(opportunity.buy_volume, opportunity.sell_volume)}%">
                                <span>$${formatVolume(opportunity.sell_volume || 0)}</span>
                            </div>
                        </div>
                    </div>
                </td>
                <td>
                    <div class="liquidity-indicator">
                        <span class="liquidity-dot ${getLiquidityClass(opportunity.buy_volume)}"></span>
                        <span>${getLiquidityText(opportunity.buy_volume)}</span>
                    </div>
                </td>
                <td>
                    <button class="action-btn action-buy" data-pair="${opportunity.pair || 'BTCUSDT'}">
                        Торгувати
                    </button>
                </td>
            `;

            uiElements.tableBody.appendChild(row);
        });
    }

    // Фільтрація таблиці
    function filterTable() {
        if (!uiElements.searchInput) return;

        const searchTerm = uiElements.searchInput.value.toLowerCase().trim();
        
        if (!searchTerm) {
            updateTable(state.currentData);
            return;
        }

        const filtered = state.currentData.filter(opportunity => {
            if (!opportunity) return false;
            
            return (
                (opportunity.pair && opportunity.pair.toLowerCase().includes(searchTerm)) ||
                (opportunity.buy && opportunity.buy.toLowerCase().includes(searchTerm)) ||
                (opportunity.sell && opportunity.sell.toLowerCase().includes(searchTerm))
            );
        });

        updateTable(filtered);
    }

    // Сортування таблиці
    function sortTable() {
        if (!uiElements.sortSelect) return;

        const sortBy = uiElements.sortSelect.value;
        let sorted = [...state.currentData].filter(item => item);

        switch (sortBy) {
            case 'spread-desc':
                sorted.sort((a, b) => (b.spread || 0) - (a.spread || 0));
                break;
            case 'spread-asc':
                sorted.sort((a, b) => (a.spread || 0) - (b.spread || 0));
                break;
            case 'volume-desc':
                sorted.sort((a, b) => (b.buy_volume || 0) - (a.buy_volume || 0));
                break;
            case 'pair-asc':
                sorted.sort((a, b) => (a.pair || '').localeCompare(b.pair || ''));
                break;
        }

        updateTable(sorted);
    }

    // Автоматичне оновлення
    function startAutoRefresh() {
        stopAutoRefresh();
        state.autoRefreshInterval = setInterval(() => {
            if (!state.isLoading) {
                fetchArbitrageData();
            }
        }, 60000); // Кожну хвилину
        
        console.log('🔄 Автоматичне оновлення увімкнено (60 сек)');
    }

    function stopAutoRefresh() {
        if (state.autoRefreshInterval) {
            clearInterval(state.autoRefreshInterval);
            state.autoRefreshInterval = null;
            console.log('⏹️ Автоматичне оновлення вимкнено');
        }
    }

    // Тема
    function toggleTheme() {
        const isLight = document.body.classList.toggle('light-theme');
        document.body.classList.toggle('dark-theme', !isLight);
        
        state.config.theme = isLight ? 'light' : 'dark';
        saveConfig();
    }

    async function loadConfig() {
        try {
            if (window.electronAPI?.loadConfig) {
                const config = await window.electronAPI.loadConfig();
                state.config = { ...state.config, ...config };
                
                // Застосування теми
                if (state.config.theme === 'light' && uiElements.themeToggle) {
                    document.body.classList.add('light-theme');
                    document.body.classList.remove('dark-theme');
                    uiElements.themeToggle.checked = true;
                }
            }
        } catch (error) {
            console.log('Не вдалося завантажити конфігурацію:', error);
        }
    }

    function saveConfig() {
        if (window.electronAPI?.saveConfig) {
            window.electronAPI.saveConfig(state.config);
        }
    }

    // Допоміжні функції
    function getSpreadClass(spread) {
        if (spread < 2) return 'spread-low';
        if (spread < 5) return 'spread-medium';
        if (spread < 10) return 'spread-high';
        return 'spread-extreme';
    }

    function formatVolume(volume) {
        if (volume >= 1000000) return `${(volume / 1000000).toFixed(2)}M`;
        if (volume >= 1000) return `${(volume / 1000).toFixed(1)}K`;
        return volume.toFixed(0);
    }

    function formatPair(pair) {
        return pair.replace('USDT', '');
    }

    function getVolumePercentage(buyVolume, sellVolume) {
        const total = (buyVolume || 0) + (sellVolume || 0);
        return total > 0 ? ((buyVolume || 0) / total * 100) : 50;
    }

    function getLiquidityClass(volume) {
        if (volume >= 1000000) return 'high';
        if (volume >= 100000) return 'medium';
        return 'low';
    }

    function getLiquidityText(volume) {
        if (volume >= 1000000) return 'Висока';
        if (volume >= 100000) return 'Середня';
        return 'Низька';
    }

    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    // UI стани
    function showLoading(show) {
        if (uiElements.loadingOverlay) {
            uiElements.loadingOverlay.style.display = show ? 'flex' : 'none';
        }
        
        if (uiElements.refreshBtn) {
            uiElements.refreshBtn.disabled = show;
            uiElements.refreshBtn.innerHTML = show 
                ? '<span class="spinner"></span> Оновлення...' 
                : '🔄 Оновити';
        }
    }

    function showError(message) {
        console.error('Error:', message);
        
        if (uiElements.tableBody) {
            uiElements.tableBody.innerHTML = `
                <tr>
                    <td colspan="7" class="error-state">
                        <div class="error-icon">⚠️</div>
                        <p style="color: #ef4444;">Помилка: ${message}</p>
                        <button onclick="fetchArbitrageData()" class="retry-btn">Спробувати знову</button>
                    </td>
                </tr>
            `;
        }
    }

    function showNotification(title, message) {
        if (window.electronAPI?.showNotification) {
            window.electronAPI.showNotification(title, message);
        }
        
        // Фолбек для браузера
        if (Notification.permission === 'granted') {
            new Notification(title, { body: message });
        }
    }

    // Глобальні функції
    window.fetchArbitrageData = fetchArbitrageData;
    window.toggleTheme = toggleTheme;
    
    // Запит дозволу на сповіщення
    if (Notification.permission === 'default') {
        Notification.requestPermission();
    }
});