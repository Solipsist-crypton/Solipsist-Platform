// src/renderer/scalper.js - ПОВНИЙ КОД

class ScalperUISimple {
    constructor() {
        this.isRunning = false;
        this.signals = [];
        this.intervalId = null;
        
        this.init();
    }
    
    async init() {
        try {
            this.bindEvents();
            await this.testConnection();
            await this.updateStatus();
            
            this.log('🚀 Сторінка скальпера завантажена', 'success');
            
            // Автоматичне оновлення статусу кожні 3 секунди
            this.startAutoRefresh();
            
        } catch (error) {
            this.log(`❌ Помилка ініціалізації: ${error}`, 'error');
        }
    }
    
    async testConnection() {
        this.log('🔍 Перевірка зв\'язку з сервером...', 'info');
        
        try {
            // Тест основного сервера
            const healthResponse = await fetch('http://127.0.0.1:5000/health');
            const healthData = await healthResponse.json();
            
            if (healthData.status === 'ok') {
                this.log('✅ Python сервер працює', 'success');
            } else {
                this.log('⚠️ Python сервер має проблеми', 'warning');
            }
            
            // Тест модуля скальпера
            const scalperTest = await fetchScalperAPI('/api/scalper/test');
            
            if (scalperTest.status === 'success') {
                this.log('✅ Модуль скальпера працює', 'success');
                if (scalperTest.price) {
                    this.updatePriceDisplay(scalperTest.price);
                    this.log(`💰 Поточна ціна SOL: $${scalperTest.price}`, 'info');
                }
            } else {
                this.log('⚠️ Модуль скальпера не відповідає', 'warning');
            }
            
        } catch (error) {
            this.log(`❌ Немає зв'язку з сервером: ${error.message}`, 'error');
            this.showError('Не вдалося підключитися до сервера на порті 5000');
        }
    }
    
    bindEvents() {
        // Кнопки управління
        document.getElementById('btnStart').addEventListener('click', () => this.startScalper());
        document.getElementById('btnStop').addEventListener('click', () => this.stopScalper());
        document.getElementById('btnReset').addEventListener('click', () => this.resetScalper());
        
        // Кнопка оновлення статусу
        const btnRefresh = document.createElement('button');
        btnRefresh.innerHTML = '<i class="fas fa-sync-alt"></i> Оновити';
        btnRefresh.className = 'btn btn-secondary';
        btnRefresh.style.marginLeft = '10px';
        btnRefresh.addEventListener('click', () => this.updateStatus());
        
        document.querySelector('.controls').appendChild(btnRefresh);
        
        // Обробка помилок API
        window.addEventListener('online', () => {
            this.log('🌐 Інтернет-з\'єднання відновлено', 'success');
            this.updateStatus();
        });
        
        window.addEventListener('offline', () => {
            this.log('📵 Втрачено інтернет-з\'єднання', 'error');
        });
    }
    
    async startScalper() {
        this.log('▶️ Запуск скальпера...', 'info');
        
        const response = await fetchScalperAPI('/api/scalper/start', {
            method: 'POST'
        });
        
        if (response.status === 'success') {
            this.isRunning = true;
            this.updateUI();
            this.log('✅ Скальпер запущено', 'success');
            this.log(`📊 Стратегія: ${response.strategy || 'EMA 5/13 на SOLUSDT'}`, 'info');
            
            // Показуємо сповіщення
            if (window.electronAPI && window.electronAPI.showNotification) {
                try {
                    await window.electronAPI.showNotification('Скальпер', 'Стратегію запущено');
                } catch (e) {
                    console.log('Сповіщення не доступні');
                }
            }
            
            // Запускаємо оновлення сигналів
            this.startSignalPolling();
            
        } else {
            this.log(`❌ Помилка запуску: ${response.message}`, 'error');
        }
    }
    
    async stopScalper() {
        this.log('⏸️ Зупинка скальпера...', 'info');
        
        const response = await fetchScalperAPI('/api/scalper/stop', {
            method: 'POST'
        });
        
        if (response.status === 'success') {
            this.isRunning = false;
            this.updateUI();
            this.log('✅ Скальпер зупинено', 'info');
            
            // Зупиняємо оновлення сигналів
            this.stopSignalPolling();
            
        } else {
            this.log(`❌ Помилка зупинки: ${response.message}`, 'error');
        }
    }
    
    async resetScalper() {
        this.log('🔄 Скидання стратегії...', 'info');
        
        const response = await fetchScalperAPI('/api/scalper/reset', {
            method: 'POST'
        });
        
        if (response.status === 'success') {
            this.log('✅ Стратегію скинуто', 'success');
            await this.updateStatus();
            
        } else {
            this.log(`❌ Помилка скидання: ${response.message}`, 'error');
        }
    }
    
    async updateStatus() {
        try {
            const response = await fetchScalperAPI('/api/scalper/status');
            
            if (response.status === 'success') {
                const { scalper, stream } = response;
                
                // Оновлюємо статус
                const statusIndicator = document.getElementById('statusIndicator');
                if (stream && stream.running) {
                    statusIndicator.innerHTML = '<i class="fas fa-circle"></i> Онлайн';
                    statusIndicator.className = 'status status-online';
                    this.isRunning = true;
                } else {
                    statusIndicator.innerHTML = '<i class="fas fa-circle"></i> Офлайн';
                    statusIndicator.className = 'status status-offline';
                    this.isRunning = false;
                }
                
                // Оновлюємо статистику
                if (scalper) {
                    document.getElementById('statEquity').textContent = `$${scalper.equity?.toFixed(2) || '0.00'}`;
                    document.getElementById('statSignals').textContent = scalper.total_signals || 0;
                    
                    const winRate = scalper.win_rate || (scalper.performance?.winning_trades / 
                        (scalper.performance?.winning_trades + scalper.performance?.losing_trades) * 100) || 0;
                    document.getElementById('statWinRate').textContent = `${winRate.toFixed(1)}%`;
                    
                    const positionText = scalper.position === 'LONG' ? 'ЛОНГ' : 
                                       scalper.position === 'SHORT' ? 'ШОРТ' : 'Немає';
                    document.getElementById('statPosition').textContent = positionText;
                    
                    // Оновлюємо позицію
                    this.updatePosition(scalper.position, scalper.entry_price);
                    
                    // Оновлюємо PnL
                    this.updatePnlDisplay(scalper.equity - 1000);
                }
                
                this.updateUI();
                
            } else {
                this.log(`❌ Помилка статусу: ${response.message}`, 'warning');
            }
            
        } catch (error) {
            console.error('Помилка оновлення статусу:', error);
        }
    }
    
    updatePosition(position, entryPrice) {
        const positionType = document.getElementById('positionType');
        const positionDetails = document.getElementById('positionDetails');
        
        if (position && entryPrice) {
            const positionText = position === 'LONG' ? 'ЛОНГ' : 'ШОРТ';
            const positionClass = position === 'LONG' ? 'position-long' : 'position-short';
            const positionColor = position === 'LONG' ? '#10b981' : '#ef4444';
            
            positionType.textContent = positionText;
            positionType.className = `position-type ${positionClass}`;
            
            positionDetails.innerHTML = `
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-top: 10px;">
                    <div>
                        <div style="color: #94a3b8; font-size: 0.9em;">Тип позиції:</div>
                        <div style="color: ${positionColor}; font-weight: bold; font-size: 1.2em;">
                            ${position === 'LONG' ? '🟢 КУПІВЛЯ' : '🔴 ПРОДАЖ'}
                        </div>
                    </div>
                    <div>
                        <div style="color: #94a3b8; font-size: 0.9em;">Ціна входу:</div>
                        <div style="color: white; font-weight: bold; font-size: 1.2em;">
                            $${entryPrice.toFixed(4)}
                        </div>
                    </div>
                </div>
            `;
        } else {
            positionType.textContent = 'Немає';
            positionType.className = 'position-type position-none';
            positionDetails.innerHTML = `
                <p style="color: #94a3b8; text-align: center; padding: 10px;">
                    Позиція не відкрита
                </p>
            `;
        }
    }
    
    updatePriceDisplay(price) {
        // Можна додати відображення ціни, якщо потрібно
        // Наприклад: document.getElementById('currentPrice').textContent = `$${price.toFixed(4)}`;
    }
    
    updatePnlDisplay(pnl) {
        const pnlElement = document.getElementById('statPnl') || document.createElement('div');
        if (!pnlElement.id) {
            pnlElement.id = 'statPnl';
            pnlElement.className = 'stat-value';
            document.querySelector('.stats-grid').innerHTML += `
                <div class="stat-card">
                    <div class="stat-label">PnL</div>
                    <div id="statPnl" class="stat-value ${pnl >= 0 ? 'positive' : 'negative'}">
                        ${pnl >= 0 ? '+' : ''}$${pnl.toFixed(2)}
                    </div>
                </div>
            `;
        } else {
            pnlElement.textContent = `${pnl >= 0 ? '+' : ''}$${pnl.toFixed(2)}`;
            pnlElement.className = `stat-value ${pnl >= 0 ? 'positive' : 'negative'}`;
        }
    }
    
    updateUI() {
        const startBtn = document.getElementById('btnStart');
        const stopBtn = document.getElementById('btnStop');
        
        if (startBtn && stopBtn) {
            startBtn.disabled = this.isRunning;
            stopBtn.disabled = !this.isRunning;
        }
    }
    
    async loadSignals() {
        try {
            const response = await fetchScalperAPI('/api/scalper/signals?limit=10');
            
            if (response.status === 'success' && response.signals) {
                this.signals = response.signals;
                this.updateSignalsList();
            }
        } catch (error) {
            console.error('Помилка завантаження сигналів:', error);
        }
    }
    
    updateSignalsList() {
        const signalsList = document.getElementById('signalsList');
        
        if (!this.signals || this.signals.length === 0) {
            signalsList.innerHTML = '<p style="color: #94a3b8; text-align: center; padding: 20px;">Сигнали з\'являться після запуску</p>';
            return;
        }
        
        signalsList.innerHTML = '';
        
        // Сортуємо сигнали за часом (новіші зверху)
        const sortedSignals = [...this.signals].reverse();
        
        sortedSignals.forEach(signal => {
            const signalElement = document.createElement('div');
            signalElement.className = `signal-item signal-${signal.signal.toLowerCase()}`;
            
            const time = new Date(signal.timestamp).toLocaleTimeString();
            const price = parseFloat(signal.price).toFixed(4);
            
            signalElement.innerHTML = `
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <strong style="font-size: 1.1em; color: ${signal.signal === 'BUY' ? '#10b981' : '#ef4444'}">
                        ${signal.signal === 'BUY' ? '🟢 КУПІВЛЯ' : '🔴 ПРОДАЖ'}
                    </strong>
                    <span style="color: #64748b; font-size: 0.9em;">${time}</span>
                </div>
                <div style="display: flex; justify-content: space-between; margin-top: 8px;">
                    <span>Ціна: <strong>$${price}</strong></span>
                    <span>EMA: ${signal.fast_ema?.toFixed(4) || '0'}/${signal.slow_ema?.toFixed(4) || '0'}</span>
                </div>
            `;
            
            signalsList.appendChild(signalElement);
        });
    }
    
    startAutoRefresh() {
        // Автоматичне оновлення статусу кожні 3 секунди
        if (this.intervalId) {
            clearInterval(this.intervalId);
        }
        
        this.intervalId = setInterval(() => {
            if (document.visibilityState === 'visible') {
                this.updateStatus();
            }
        }, 3000);
    }
    
    startSignalPolling() {
        // Оновлюємо сигнали кожні 5 секунд
        if (this.signalInterval) {
            clearInterval(this.signalInterval);
        }
        
        this.signalInterval = setInterval(async () => {
            if (this.isRunning) {
                await this.loadSignals();
            }
        }, 5000);
        
        // Перше завантаження одразу
        this.loadSignals();
    }
    
    stopSignalPolling() {
        if (this.signalInterval) {
            clearInterval(this.signalInterval);
            this.signalInterval = null;
        }
    }
    
    log(message, type = 'info') {
        const logElement = document.getElementById('eventLog');
        if (!logElement) {
            console.log(`[${type}] ${message}`);
            return;
        }
        
        const entry = document.createElement('div');
        entry.className = 'log-entry';
        
        const timestamp = new Date().toLocaleTimeString();
        const icons = {
            'info': 'ℹ️',
            'success': '✅',
            'error': '❌',
            'warning': '⚠️'
        };
        
        const icon = icons[type] || icons.info;
        const color = type === 'error' ? '#ef4444' : 
                     type === 'success' ? '#10b981' : 
                     type === 'warning' ? '#f59e0b' : '#94a3b8';
        
        entry.innerHTML = `
            <span style="color: #64748b">[${timestamp}]</span>
            <span style="color: ${color}; margin-left: 10px;">${icon} ${message}</span>
        `;
        
        logElement.prepend(entry);
        
        // Обмежуємо кількість записів
        if (logElement.children.length > 50) {
            logElement.removeChild(logElement.lastChild);
        }
    }
    
    showError(message) {
        const errorDiv = document.createElement('div');
        errorDiv.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #ef4444;
            color: white;
            padding: 15px 20px;
            border-radius: 8px;
            z-index: 1000;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            animation: slideIn 0.3s ease;
        `;
        
        errorDiv.innerHTML = `
            <strong>❌ Помилка:</strong><br>
            ${message}
        `;
        
        document.body.appendChild(errorDiv);
        
        setTimeout(() => {
            errorDiv.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => errorDiv.remove(), 300);
        }, 5000);
    }
}

// Стилі для анімацій
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
`;
document.head.appendChild(style);

// Запускаємо UI при завантаженні сторінки
document.addEventListener('DOMContentLoaded', () => {
    console.log('📄 DOM завантажено, ініціалізація скальпера...');
    window.scalperUI = new ScalperUISimple();
});

// Глобальні функції для тестування
window.testScalperAPI = async () => {
    console.log('🧪 Тестування API скальпера...');
    
    const endpoints = [
        '/api/scalper/health',
        '/api/scalper/status',
        '/api/scalper/test'
    ];
    
    for (const endpoint of endpoints) {
        try {
            const response = await fetchScalperAPI(endpoint);
            console.log(`${endpoint}:`, response);
        } catch (error) {
            console.error(`${endpoint}:`, error);
        }
    }
};

window.forceUpdateStatus = () => {
    if (window.scalperUI) {
        window.scalperUI.updateStatus();
    }
};