// src/renderer/renderer.js
document.addEventListener('DOMContentLoaded', () => {
    // Елементи
    const refreshBtn = document.getElementById('refresh-btn');
    const tableBody = document.getElementById('table-body');
    const foundCount = document.getElementById('found-count');
    const maxSpread = document.getElementById('max-spread');
    const avgSpread = document.getElementById('avg-spread');
    const updateTime = document.getElementById('update-time');
    const themeToggle = document.getElementById('theme-toggle');
    const autoRefreshToggle = document.getElementById('auto-refresh');
    
    let autoRefreshInterval;
    let currentData = [];
    
    // Ініціалізація
    init();
    
    // Основний функціонал
    async function init() {
        setupEventListeners();
        loadConfig();
        await fetchArbitrageData();
        startAutoRefresh();
    }
    
    function setupEventListeners() {
        refreshBtn.addEventListener('click', fetchArbitrageData);
        
        themeToggle.addEventListener('change', toggleTheme);
        
        autoRefreshToggle.addEventListener('change', (e) => {
            if (e.target.checked) {
                startAutoRefresh();
            } else {
                stopAutoRefresh();
            }
        });
        
        // Пошук
        document.getElementById('search-input').addEventListener('input', filterTable);
        
        // Сортування
        document.getElementById('sort-select').addEventListener('change', sortTable);
        
        // Пагінація
        document.getElementById('prev-page').addEventListener('click', prevPage);
        document.getElementById('next-page').addEventListener('click', nextPage);
    }
    
    // Отримання даних арбітражу
    async function fetchArbitrageData() {
        showLoading(true);
        
        try {
            const data = await window.electronAPI.getArbitrage();
            
            if (data.error) {
                showError(data.error);
                return;
            }
            
            currentData = data.opportunities || [];
            updateUI(data);
            updateTable(currentData);
            
            // Показати сповіщення
            if (currentData.length > 0) {
                showNotification(`Знайдено ${currentData.length} можливостей`, 
                               `Максимальний спред: ${Math.max(...currentData.map(d => d.spread)).toFixed(2)}%`);
            }
            
        } catch (error) {
            console.error('Помилка отримання даних:', error);
            showError('Не вдалося отримати дані');
        } finally {
            showLoading(false);
        }
    }
    
    // Оновлення UI
    function updateUI(data) {
        const opportunities = data.opportunities || [];
        const stats = data.stats || {};
        
        foundCount.textContent = opportunities.length;
        
        if (opportunities.length > 0) {
            const spreads = opportunities.map(o => o.spread);
            maxSpread.textContent = `${Math.max(...spreads).toFixed(2)}%`;
            avgSpread.textContent = `${(spreads.reduce((a, b) => a + b, 0) / spreads.length).toFixed(2)}%`;
        } else {
            maxSpread.textContent = '0%';
            avgSpread.textContent = '0%';
        }
        
        updateTime.textContent = new Date().toLocaleTimeString();
    }
    
    // Оновлення таблиці
    function updateTable(data) {
        tableBody.innerHTML = '';
        
        if (data.length === 0) {
            tableBody.innerHTML = `
                <tr>
                    <td colspan="7" class="empty-state">
                        <i class="fas fa-search"></i>
                        <p>Арбітражних можливостей не знайдено</p>
                    </td>
                </tr>
            `;
            return;
        }
        
        data.forEach(opportunity => {
            const row = document.createElement('tr');
            const spreadClass = getSpreadClass(opportunity.spread);
            
            row.innerHTML = `
                <td>
                    <div class="pair-cell">
                        <span class="pair-symbol">${opportunity.pair}</span>
                        <span class="pair-exchanges">${opportunity.exchanges} бірж</span>
                    </div>
                </td>
                <td>
                    <span class="spread-badge ${spreadClass}">
                        ${opportunity.spread.toFixed(2)}%
                    </span>
                </td>
                <td>
                    <div class="exchange-cell">
                        <i class="fas fa-shopping-cart"></i>
                        <span>${opportunity.buy}</span>
                    </div>
                </td>
                <td>
                    <div class="exchange-cell">
                        <i class="fas fa-cash-register"></i>
                        <span>${opportunity.sell}</span>
                    </div>
                </td>
                <td>
                    <div class="price-cell">
                        <span class="buy-price">$${opportunity.buy_price.toFixed(6)}</span>
                        <i class="fas fa-arrow-right"></i>
                        <span class="sell-price">$${opportunity.sell_price.toFixed(6)}</span>
                    </div>
                </td>
                <td>
                    <div class="volume-cell">
                        <span class="volume-buy">$${formatVolume(opportunity.buy_volume)}</span>
                        <i class="fas fa-arrow-right"></i>
                        <span class="volume-sell">$${formatVolume(opportunity.sell_volume)}</span>
                    </div>
                </td>
                <td>
                    <button class="action-btn action-buy" onclick="trade('${opportunity.pair}', '${opportunity.buy}')">
                        <i class="fas fa-bolt"></i>
                        Торгувати
                    </button>
                </td>
            `;
            
            tableBody.appendChild(row);
        });
    }
    
    // Допоміжні функції
    function getSpreadClass(spread) {
        if (spread < 5) return 'spread-low';
        if (spread < 20) return 'spread-medium';
        return 'spread-high';
    }
    
    function formatVolume(volume) {
        if (volume >= 1000000) return `${(volume / 1000000).toFixed(1)}M`;
        if (volume >= 1000) return `${(volume / 1000).toFixed(0)}K`;
        return volume.toFixed(0);
    }
    
    function filterTable() {
        const searchTerm = document.getElementById('search-input').value.toLowerCase();
        const filtered = currentData.filter(opp => 
            opp.pair.toLowerCase().includes(searchTerm) ||
            opp.buy.toLowerCase().includes(searchTerm) ||
            opp.sell.toLowerCase().includes(searchTerm)
        );
        updateTable(filtered);
    }
    
    function sortTable() {
        const sortBy = document.getElementById('sort-select').value;
        let sorted = [...currentData];
        
        switch (sortBy) {
            case 'spread-desc':
                sorted.sort((a, b) => b.spread - a.spread);
                break;
            case 'spread-asc':
                sorted.sort((a, b) => a.spread - b.spread);
                break;
            case 'volume-desc':
                sorted.sort((a, b) => b.buy_volume - a.buy_volume);
                break;
        }
        
        updateTable(sorted);
    }
    
    // Автооновлення
    function startAutoRefresh() {
        if (autoRefreshInterval) clearInterval(autoRefreshInterval);
        autoRefreshInterval = setInterval(fetchArbitrageData, 60000); // Кожні 60 секунд
    }
    
    function stopAutoRefresh() {
        if (autoRefreshInterval) {
            clearInterval(autoRefreshInterval);
            autoRefreshInterval = null;
        }
    }
    
    // Тема
    function toggleTheme() {
        document.body.classList.toggle('light-theme');
        document.body.classList.toggle('dark-theme');
        saveConfig({ theme: document.body.classList.contains('light-theme') ? 'light' : 'dark' });
    }
    
    function loadConfig() {
        window.electronAPI.loadConfig().then(config => {
            if (config.theme === 'light') {
                document.body.classList.add('light-theme');
                document.body.classList.remove('dark-theme');
                themeToggle.checked = true;
            }
        });
    }
    
    function saveConfig(config) {
        window.electronAPI.saveConfig(config);
    }
    
    // UI стани
    function showLoading(show) {
        const overlay = document.getElementById('loading-overlay');
        overlay.style.display = show ? 'flex' : 'none';
    }
    
    function showError(message) {
        // Можна додати гарні тоасти
        console.error('Error:', message);
    }
    
    function showNotification(title, body) {
        window.electronAPI.showNotification(title, body);
    }
    
    // Глобальні функції для кнопок
    window.trade = (pair, exchange) => {
        window.electronAPI.openUrl(`https://www.binance.com/en/trade/${pair}`);
    };
});