// src/renderer/renderer.js - ФІКСОВАНА ВЕРСІЯ
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
        if (refreshBtn) {
            refreshBtn.addEventListener('click', fetchArbitrageData);
        }
        
        if (themeToggle) {
            themeToggle.addEventListener('change', toggleTheme);
        }
        
        if (autoRefreshToggle) {
            autoRefreshToggle.addEventListener('change', (e) => {
                if (e.target.checked) {
                    startAutoRefresh();
                } else {
                    stopAutoRefresh();
                }
            });
        }
        
        // Пошук
        const searchInput = document.getElementById('search-input');
        if (searchInput) {
            searchInput.addEventListener('input', filterTable);
        }
        
        // Сортування
        const sortSelect = document.getElementById('sort-select');
        if (sortSelect) {
            sortSelect.addEventListener('change', sortTable);
        }
    }
    
    // Отримання даних арбітражу
    async function fetchArbitrageData() {
        showLoading(true);
        
        try {
            // Перевіряємо чи API доступний
            if (!window.electronAPI || !window.electronAPI.getArbitrage) {
                showError('API не доступне');
                return;
            }
            
            const data = await window.electronAPI.getArbitrage();
            
            if (data.error) {
                showError(data.error);
                return;
            }
            
            currentData = data.opportunities || [];
            updateUI(data);
            updateTable(currentData);
            
            // Показати сповіщення
            if (currentData.length > 0 && window.electronAPI.showNotification) {
                window.electronAPI.showNotification(
                    `Знайдено ${currentData.length} можливостей`, 
                    `Максимальний спред: ${Math.max(...currentData.map(d => d.spread)).toFixed(2)}%`
                );
            }
            
        } catch (error) {
            console.error('Помилка отримання даних:', error);
            showError('Не вдалося отримати дані: ' + error.message);
        } finally {
            showLoading(false);
        }
    }
    
    // Оновлення UI
    function updateUI(data) {
        const opportunities = data.opportunities || [];
        
        if (foundCount) {
            foundCount.textContent = opportunities.length;
        }
        
        if (opportunities.length > 0) {
            const spreads = opportunities.map(o => o.spread || 0);
            const maxSpreadValue = Math.max(...spreads);
            const avgSpreadValue = spreads.reduce((a, b) => a + b, 0) / spreads.length;
            
            if (maxSpread) {
                maxSpread.textContent = `${maxSpreadValue.toFixed(2)}%`;
            }
            
            if (avgSpread) {
                avgSpread.textContent = `${avgSpreadValue.toFixed(2)}%`;
            }
        } else {
            if (maxSpread) maxSpread.textContent = '0%';
            if (avgSpread) avgSpread.textContent = '0%';
        }
        
        if (updateTime) {
            updateTime.textContent = new Date().toLocaleTimeString('uk-UA');
        }
    }
    
    // Оновлення таблиці
    function updateTable(data) {
        if (!tableBody) return;
        
        tableBody.innerHTML = '';
        
        if (!data || data.length === 0) {
            tableBody.innerHTML = `
                <tr>
                    <td colspan="7" class="empty-state">
                        <p>Арбітражних можливостей не знайдено</p>
                    </td>
                </tr>
            `;
            return;
        }
        
        data.forEach(opportunity => {
            if (!opportunity) return;
            
            const row = document.createElement('tr');
            const spreadClass = getSpreadClass(opportunity.spread || 0);
            
            row.innerHTML = `
                <td>
                    <div class="pair-cell">
                        <span class="pair-symbol">${opportunity.pair || 'N/A'}</span>
                        <span class="pair-exchanges">${opportunity.exchanges || 0} бірж</span>
                    </div>
                </td>
                <td>
                    <span class="spread-badge ${spreadClass}">
                        ${(opportunity.spread || 0).toFixed(2)}%
                    </span>
                </td>
                <td>
                    <div class="exchange-cell">
                        <span>${opportunity.buy || 'N/A'}</span>
                    </div>
                </td>
                <td>
                    <div class="exchange-cell">
                        <span>${opportunity.sell || 'N/A'}</span>
                    </div>
                </td>
                <td>
                    <div class="price-cell">
                        <span class="buy-price">$${(opportunity.buy_price || 0).toFixed(6)}</span>
                        <span> → </span>
                        <span class="sell-price">$${(opportunity.sell_price || 0).toFixed(6)}</span>
                    </div>
                </td>
                <td>
                    <div class="volume-cell">
                        <span class="volume-buy">$${formatVolume(opportunity.buy_volume || 0)}</span>
                        <span> → </span>
                        <span class="volume-sell">$${formatVolume(opportunity.sell_volume || 0)}</span>
                    </div>
                </td>
                <td>
                    <button class="action-btn action-buy" onclick="window.open('https://www.binance.com/en/trade/${opportunity.pair || 'BTCUSDT'}', '_blank')">
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
        const searchInput = document.getElementById('search-input');
        if (!searchInput) return;
        
        const searchTerm = searchInput.value.toLowerCase();
        const filtered = currentData.filter(opp => {
            if (!opp) return false;
            return (opp.pair && opp.pair.toLowerCase().includes(searchTerm)) ||
                   (opp.buy && opp.buy.toLowerCase().includes(searchTerm)) ||
                   (opp.sell && opp.sell.toLowerCase().includes(searchTerm));
        });
        updateTable(filtered);
    }
    
    function sortTable() {
        const sortSelect = document.getElementById('sort-select');
        if (!sortSelect) return;
        
        const sortBy = sortSelect.value;
        let sorted = [...currentData].filter(item => item); // Фільтруємо null/undefined
        
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
        }
        
        updateTable(sorted);
    }
    
    // Автооновлення
    function startAutoRefresh() {
        if (autoRefreshInterval) clearInterval(autoRefreshInterval);
        autoRefreshInterval = setInterval(fetchArbitrageData, 60000);
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
        if (window.electronAPI && window.electronAPI.saveConfig) {
            window.electronAPI.saveConfig({ 
                theme: document.body.classList.contains('light-theme') ? 'light' : 'dark' 
            });
        }
    }
    
    function loadConfig() {
        if (window.electronAPI && window.electronAPI.loadConfig) {
            window.electronAPI.loadConfig().then(config => {
                if (config && config.theme === 'light' && themeToggle) {
                    document.body.classList.add('light-theme');
                    document.body.classList.remove('dark-theme');
                    themeToggle.checked = true;
                }
            }).catch(err => {
                console.log('Не вдалося завантажити конфігурацію:', err);
            });
        }
    }
    
    // UI стани
    function showLoading(show) {
        const overlay = document.getElementById('loading-overlay');
        if (overlay) {
            overlay.style.display = show ? 'flex' : 'none';
        }
    }
    
    function showError(message) {
        console.error('Error:', message);
        // Простий спосіб показати помилку
        if (tableBody) {
            tableBody.innerHTML = `
                <tr>
                    <td colspan="7" class="error-state">
                        <p style="color: #ef4444;">Помилка: ${message}</p>
                    </td>
                </tr>
            `;
        }
    }
    
    // Додаємо обробник для кнопки торгівлі
    window.trade = (pair, exchange) => {
        window.open(`https://www.binance.com/en/trade/${pair || 'BTCUSDT'}`, '_blank');
    };
});