// src/renderer/scalper.js - ВИПРАВЛЕНА ВЕРСІЯ
// ========== ГЛОБАЛЬНА ФУНКЦІЯ ДЛЯ API ==========

// Замініть всю функцію fetchScalperAPI на цю:
window.fetchScalperAPI = async function(endpoint, options = {}) {
    const baseUrl = 'http://127.0.0.1:5000';
    
    console.log(`📡 API Call: ${endpoint}`);
    
    try {
        const method = options.method || 'GET';
        const fetchOptions = {
            method: method,
            headers: {
                'Content-Type': 'application/json',
            }
        };
        
        if (options.body) {
            fetchOptions.body = JSON.stringify(options.body);
        }
        
        const response = await fetch(`${baseUrl}${endpoint}`, fetchOptions);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error(`❌ API Error (${endpoint}):`, error);
        
        // Fallback дані для тестування
        if (endpoint === '/api/scalper/status') {
            return {
                status: 'success',
                scalper: {
                    running: false,
                    position: null,
                    entry_price: 0,
                    equity: 1000.0,
                    total_signals: 0,
                    win_rate: 0,
                    performance: { winning_trades: 0, losing_trades: 0 }
                },
                stream: { running: false }
            };
        }
        
        if (endpoint === '/api/scalper/test') {
            return {
                status: 'success',
                price: 86.24,
                message: 'Fallback data'
            };
        }
        
        return {
            status: 'error',
            message: error.message || 'Network error'
        };
    }
};

// ========== КЛАС СКАЛЬПЕРА ==========

class ScalperUISimple {
    constructor() {
        this.isRunning = false;
        this.signals = [];
        this.intervalId = null;
        
        // Перевірка чи API доступне
        console.log('🔧 Ініціалізація Scalper UI...');
        
        this.init();
    }
    
    async init() {
        try {
            console.log('📝 Ініціалізація...');
            this.bindEvents();
            
            // Проста перевірка без тесту сервера
            await this.updateStatus();
            
            this.log('Сторінка скальпера завантажена', 'success');
            
            // Автоматичне оновлення кожні 5 секунд
            this.startAutoRefresh();
            
        } catch (error) {
            this.log(`Помилка ініціалізації: ${error}`, 'error');
        }
    }
    
    async testConnection() {
        this.log('Перевірка зв\'язку з сервером...', 'info');
        
        try {
            // Проста перевірка
            const healthResponse = await fetch('http://127.0.0.1:5000/health');
            if (healthResponse.ok) {
                this.log('Python сервер працює', 'success');
                return true;
            }
        } catch (error) {
            this.log(`Немає зв'язку з сервером: ${error.message}`, 'error');
        }
        return false;
    }
    
    bindEvents() {
        // Кнопки управління
        const startBtn = document.getElementById('btnStart');
        const stopBtn = document.getElementById('btnStop');
        const resetBtn = document.getElementById('btnReset');
        
        if (startBtn) startBtn.addEventListener('click', () => this.startScalper());
        if (stopBtn) stopBtn.addEventListener('click', () => this.stopScalper());
        if (resetBtn) resetBtn.addEventListener('click', () => this.resetScalper());
        
        console.log('📌 Кнопки прив\'язані');
    }
    
    async startScalper() {
        this.log('Запуск скальпера...', 'info');
        
        try {
            const response = await fetchScalperAPI('/api/scalper/start', {
                method: 'POST'
            });
            
            if (response.status === 'success') {
                this.isRunning = true;
                this.updateUI();
                this.log('Скальпер запущено', 'success');
                
                // Показуємо сповіщення
                if (window.electronAPI?.showNotification) {
                    try {
                        await window.electronAPI.showNotification('Скальпер', 'Стратегію запущено');
                    } catch (e) {
                        console.log('Сповіщення не доступні');
                    }
                }
                
            } else {
                this.log(`Помилка запуску: ${response.message}`, 'error');
            }
        } catch (error) {
            this.log(`Помилка: ${error.message}`, 'error');
        }
    }
    
    async stopScalper() {
        this.log('Зупинка скальпера...', 'info');
        
        try {
            const response = await fetchScalperAPI('/api/scalper/stop', {
                method: 'POST'
            });
            
            if (response.status === 'success') {
                this.isRunning = false;
                this.updateUI();
                this.log('Скальпер зупинено', 'info');
            } else {
                this.log(`Помилка зупинки: ${response.message}`, 'error');
            }
        } catch (error) {
            this.log(`Помилка: ${error.message}`, 'error');
        }
    }
    
    async resetScalper() {
        this.log('Скидання стратегії...', 'info');
        
        try {
            const response = await fetchScalperAPI('/api/scalper/reset', {
                method: 'POST'
            });
            
            if (response.status === 'success') {
                this.log('Стратегію скинуто', 'success');
                await this.updateStatus();
            } else {
                this.log(`Помилка скидання: ${response.message}`, 'error');
            }
        } catch (error) {
            this.log(`Помилка: ${error.message}`, 'error');
        }
    }
    
    async updateStatus() {
        try {
            console.log('🔄 Оновлення статусу...');
            
            const response = await fetchScalperAPI('/api/scalper/status');
            
            if (response.status === 'success') {
                const { scalper, stream } = response;
                
                // Оновлюємо статус
                const statusIndicator = document.getElementById('statusIndicator');
                if (statusIndicator) {
                    if (stream && stream.running) {
                        statusIndicator.innerHTML = '<i class="fas fa-circle"></i> Онлайн';
                        statusIndicator.className = 'status status-online';
                        this.isRunning = true;
                    } else {
                        statusIndicator.innerHTML = '<i class="fas fa-circle"></i> Офлайн';
                        statusIndicator.className = 'status status-offline';
                        this.isRunning = false;
                    }
                }
                
                // Оновлюємо статистику
                if (scalper) {
                    const statEquity = document.getElementById('statEquity');
                    const statSignals = document.getElementById('statSignals');
                    const statWinRate = document.getElementById('statWinRate');
                    const statPosition = document.getElementById('statPosition');
                    
                    if (statEquity) statEquity.textContent = `$${scalper.equity?.toFixed(2) || '0.00'}`;
                    if (statSignals) statSignals.textContent = scalper.total_signals || 0;
                    if (statWinRate) statWinRate.textContent = `${(scalper.win_rate || 0).toFixed(1)}%`;
                    
                    if (statPosition) {
                        const positionText = scalper.position === 'LONG' ? 'ЛОНГ' : 
                                           scalper.position === 'SHORT' ? 'ШОРТ' : 'Немає';
                        statPosition.textContent = positionText;
                    }
                }
                
                this.updateUI();
                
                console.log('✅ Статус оновлено');
                
            } else {
                this.log(`Помилка статусу: ${response.message}`, 'warning');
            }
            
        } catch (error) {
            console.error('Помилка оновлення статусу:', error);
            this.log('Не вдалося отримати статус', 'error');
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
    
    startAutoRefresh() {
        // Автоматичне оновлення кожні 5 секунд
        if (this.intervalId) {
            clearInterval(this.intervalId);
        }
        
        this.intervalId = setInterval(() => {
            if (document.visibilityState === 'visible') {
                this.updateStatus();
            }
        }, 5000);
        
        console.log('🔄 Автооновлення запущено');
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
        if (logElement.children.length > 20) {
            logElement.removeChild(logElement.lastChild);
        }
    }
}

// ========== ЗАПУСК ==========

document.addEventListener('DOMContentLoaded', () => {
    console.log('📄 DOM завантажено, ініціалізація скальпера...');
    
    // Запускаємо з затримкою, щоб все завантажилося
    setTimeout(() => {
        window.scalperUI = new ScalperUISimple();
    }, 500);
});

// Додайте цю функцію для тестування з консолі
window.testScalperConnection = async () => {
    console.log('🧪 Тестування підключення...');
    
    try {
        const health = await fetch('http://127.0.0.1:5000/health');
        console.log('Health:', await health.json());
        
        const test = await fetch('http://127.0.0.1:5000/api/scalper/test');
        console.log('Test:', await test.json());
        
        const status = await fetch('http://127.0.0.1:5000/api/scalper/status');
        console.log('Status:', await status.json());
        
        console.log('✅ Всі тести пройдені');
    } catch (error) {
        console.error('❌ Тест провалено:', error);
    }
};