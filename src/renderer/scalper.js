// src/renderer/scalper.js - З РЕАЛЬНИМИ СВІЧКАМИ ТА СИГНАЛАМИ
// ========== ГЛОБАЛЬНА ФУНКЦІЯ ДЛЯ API ==========

window.fetchScalperAPI = async function(endpoint, options = {}) {
    const baseUrl = 'http://127.0.0.1:5000';
    
    console.log(`📡 API: ${endpoint}`);
    
    try {
        const method = options.method || 'GET';
        const fetchOptions = {
            method: method,
            headers: {
                'Content-Type': 'application/json',
            },
            signal: AbortSignal.timeout(10000)
        };
        
        if (options.body) {
            fetchOptions.body = JSON.stringify(options.body);
        }
        
        const response = await fetch(`${baseUrl}${endpoint}`, fetchOptions);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        console.log(`✅ API ${endpoint}: успішно`);
        return data;
        
    } catch (error) {
        console.error(`❌ API ${endpoint}:`, error);
        return {
            status: 'error',
            message: error.message || 'Помилка мережі'
        };
    }
};

// ========== КЛАС СКАЛЬПЕРА З РЕАЛЬНИМИ ДАНИМИ ==========

class ScalperUISimple {
    constructor() {
        this.isRunning = false;
        this.signals = [];
        this.trades = []; // Історія торгів
        this.intervalId = null;
        this.chart = null;
        this.candleSeries = null;
        this.emaFastSeries = null;
        this.emaSlowSeries = null;
        this.candleData = [];
        this.emaFastData = [];
        this.emaSlowData = [];
        this.currentPosition = null; // { type: 'LONG'/'SHORT', entryPrice: number, entryTime: timestamp }
        this.equity = 1000.00; // Стартовий баланс
        this.performance = { wins: 0, losses: 0 };
        
        console.log('🔧 Ініціалізація Scalper UI...');
        
        this.init();
    }
    
    async init() {
        try {
            console.log('📝 Ініціалізація...');
            
            // Перевірка бібліотеки
            if (typeof LightweightCharts === 'undefined') {
                this.log('❌ Бібліотека LightweightCharts не завантажена!', 'error');
                return;
            }
            
            // Ініціалізація
            this.bindEvents();
            this.initChart();
            
            // Завантаження реальних даних
            await this.loadRealData();
            
            this.log('✅ Сторінка скальпера завантажена', 'success');
            
            // Автооновлення навіть якщо вкладка не активна
            this.startAutoRefresh();
            
        } catch (error) {
            this.log(`❌ Помилка ініціалізації: ${error}`, 'error');
            console.error(error);
        }
    }
    
    initChart() {
        console.log('📊 Ініціалізація графіка...');
        
        const chartContainer = document.getElementById('priceChart');
        if (!chartContainer) {
            this.log('❌ Контейнер для графіка не знайдено!', 'error');
            return;
        }
        
        try {
            // Створюємо графік
            this.chart = LightweightCharts.createChart(chartContainer, {
                layout: {
                    background: { color: '#0f172a' },
                    textColor: '#94a3b8',
                },
                grid: {
                    vertLines: { color: '#1e293b' },
                    horzLines: { color: '#1e293b' },
                },
                width: chartContainer.clientWidth,
                height: 500,
                timeScale: {
                    timeVisible: true,
                    secondsVisible: false,
                    borderColor: '#334155',
                },
                rightPriceScale: {
                    borderColor: '#334155',
                },
                crosshair: {
                    vertLine: {
                        color: '#3b82f6',
                        width: 1,
                        style: 1,
                    },
                    horzLine: {
                        color: '#3b82f6',
                        width: 1,
                        style: 1,
                    },
                },
            });
            
            // Серія свічок
            this.candleSeries = this.chart.addCandlestickSeries({
                upColor: '#26a69a',
                downColor: '#ef5350',
                borderUpColor: '#26a69a',
                borderDownColor: '#ef5350',
                wickUpColor: '#26a69a',
                wickDownColor: '#ef5350',
            });
            
            // Серія для EMA 5
            this.emaFastSeries = this.chart.addLineSeries({
                color: '#2196f3',
                lineWidth: 2,
                title: 'EMA 5',
                priceLineVisible: false,
            });
            
            // Серія для EMA 13
            this.emaSlowSeries = this.chart.addLineSeries({
                color: '#ff9800',
                lineWidth: 2,
                title: 'EMA 13',
                priceLineVisible: false,
            });
            
            console.log('✅ Графік ініціалізовано');
            
        } catch (error) {
            console.error('❌ Помилка ініціалізації графіка:', error);
            this.log(`❌ Помилка графіка: ${error.message}`, 'error');
        }
    }
    
    // ЗАВАНТАЖЕННЯ РЕАЛЬНИХ ДАНИХ З BINANCE
    async loadRealData() {
        try {
            this.log('📥 Завантаження реальних даних з Binance...', 'info');
            
            // Отримуємо реальні свічки
            const response = await fetchScalperAPI('/api/scalper/candles?symbol=SOL/USDT&interval=1m&limit=100');
            
            if (response.status === 'success' && response.candles) {
                // Форматуємо дані
                this.candleData = response.candles.map(candle => ({
                    time: candle.time,
                    open: candle.open,
                    high: candle.high,
                    low: candle.low,
                    close: candle.close
                }));
                
                // Оновлюємо поточну ціну
                this.updateCurrentPrice(response.current_price);
                
                // Розраховуємо EMA
                this.calculateEMA();
                
                // Оновлюємо графік
                this.updateChart();
                
                // Оновлюємо статистику
                this.updateStatistics();
                
                this.log(`✅ Завантажено ${this.candleData.length} реальних свічок`, 'success');
                
            } else {
                throw new Error('Не вдалося отримати дані');
            }
            
        } catch (error) {
            console.error('Помилка завантаження даних:', error);
            this.log('❌ Не вдалося завантажити дані, використовую тестові', 'warning');
            await this.loadTestData();
        }
    }
    
    // ТЕСТОВІ ДАНІ (якщо API не працює)
    async loadTestData() {
        // Генерація реалістичних тестових даних
        const now = Math.floor(Date.now() / 1000);
        this.candleData = [];
        
        let price = 86.0;
        
        for (let i = 100; i >= 0; i--) {
            const time = now - (i * 60);
            
            // Реальна волатильність
            const change = (Math.random() - 0.5) * 0.02;
            const open = price;
            const close = price * (1 + change);
            const range = Math.abs(close - open) * 1.5;
            const high = Math.max(open, close) + range * Math.random();
            const low = Math.min(open, close) - range * Math.random();
            
            this.candleData.push({
                time: time,
                open: parseFloat(open.toFixed(3)),
                high: parseFloat(high.toFixed(3)),
                low: parseFloat(low.toFixed(3)),
                close: parseFloat(close.toFixed(3))
            });
            
            price = close;
        }
        
        // Розраховуємо EMA
        this.calculateEMA();
        this.updateChart();
        this.updateStatistics();
    }
    
    // РОЗРАХУНОК EMA З РЕАЛЬНИХ ДАНИХ
    calculateEMA() {
        if (this.candleData.length < 13) return;
        
        this.emaFastData = [];
        this.emaSlowData = [];
        
        const closes = this.candleData.map(c => c.close);
        
        // EMA 5
        let ema5 = closes.slice(0, 5).reduce((a, b) => a + b) / 5;
        for (let i = 5; i < closes.length; i++) {
            const multiplier = 2 / (5 + 1);
            ema5 = (closes[i] - ema5) * multiplier + ema5;
            this.emaFastData.push({
                time: this.candleData[i].time,
                value: parseFloat(ema5.toFixed(3))
            });
        }
        
        // EMA 13
        let ema13 = closes.slice(0, 13).reduce((a, b) => a + b) / 13;
        for (let i = 13; i < closes.length; i++) {
            const multiplier = 2 / (13 + 1);
            ema13 = (closes[i] - ema13) * multiplier + ema13;
            this.emaSlowData.push({
                time: this.candleData[i].time,
                value: parseFloat(ema13.toFixed(3))
            });
        }
    }
    
    // ОНОВЛЕННЯ ГРАФІКА
    updateChart() {
        if (!this.candleSeries || !this.candleData.length) return;
        
        try {
            // Оновлюємо свічки
            this.candleSeries.setData(this.candleData);
            
            // Оновлюємо EMA
            if (this.emaFastData.length) {
                this.emaFastSeries.setData(this.emaFastData);
            }
            
            if (this.emaSlowData.length) {
                this.emaSlowSeries.setData(this.emaSlowData);
            }
            
            // Автомасштабування
            this.chart.timeScale().fitContent();
            
        } catch (error) {
            console.error('Помилка оновлення графіка:', error);
        }
    }
    
    // ОНОВЛЕННЯ ПОТОЧНОЇ ЦІНИ
    updateCurrentPrice(price) {
        const priceElement = document.getElementById('currentPrice');
        if (priceElement) {
            priceElement.textContent = `$${price.toFixed(3)}`;
        }
    }
    
    // ОНОВЛЕННЯ СТАТИСТИКИ
    updateStatistics() {
        // Оновлюємо статистику позиції
        this.updatePositionInfo();
        
        // Оновлюємо баланс
        const equityElement = document.getElementById('statEquity');
        if (equityElement) {
            equityElement.textContent = `$${this.equity.toFixed(2)}`;
        }
        
        // Оновлюємо сигнали
        const signalsElement = document.getElementById('statSignals');
        if (signalsElement) {
            signalsElement.textContent = this.signals.length;
        }
        
        // Оновлюємо win rate
        const winRateElement = document.getElementById('statWinRate');
        if (winRateElement && this.performance.wins + this.performance.losses > 0) {
            const winRate = (this.performance.wins / (this.performance.wins + this.performance.losses)) * 100;
            winRateElement.textContent = `${winRate.toFixed(1)}%`;
        }
    }
    
    // ОНОВЛЕННЯ ІНФОРМАЦІЇ ПРО ПОЗИЦІЮ
    updatePositionInfo() {
        const positionElement = document.getElementById('statPosition');
        const positionTypeElement = document.getElementById('positionType');
        const positionDetailsElement = document.getElementById('positionDetails');
        
        if (!positionElement || !positionTypeElement || !positionDetailsElement) return;
        
        if (this.currentPosition) {
            const currentPrice = this.candleData.length > 0 ? this.candleData[this.candleData.length - 1].close : 0;
            const pnl = this.currentPosition.type === 'LONG' 
                ? currentPrice - this.currentPosition.entryPrice
                : this.currentPosition.entryPrice - currentPrice;
            
            positionElement.textContent = this.currentPosition.type === 'LONG' ? 'ЛОНГ' : 'ШОРТ';
            
            positionTypeElement.className = 'position-type ' + 
                (this.currentPosition.type === 'LONG' ? 'position-long' : 'position-short');
            positionTypeElement.textContent = this.currentPosition.type === 'LONG' ? 'ЛОНГ ПОЗИЦІЯ' : 'ШОРТ ПОЗИЦІЯ';
            
            positionDetailsElement.innerHTML = `
                <div class="detail-row">
                    <span class="detail-label">Ціна входу:</span>
                    <span class="detail-value">$${this.currentPosition.entryPrice.toFixed(3)}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Поточна ціна:</span>
                    <span class="detail-value">$${currentPrice.toFixed(3)}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">PnL:</span>
                    <span class="detail-value" style="color: ${pnl >= 0 ? '#10b981' : '#ef4444'}">
                        ${pnl >= 0 ? '+' : ''}$${pnl.toFixed(3)}
                    </span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Час відкриття:</span>
                    <span class="detail-value">${new Date(this.currentPosition.entryTime * 1000).toLocaleTimeString()}</span>
                </div>
            `;
        } else {
            positionElement.textContent = 'Немає';
            positionTypeElement.className = 'position-type position-none';
            positionTypeElement.textContent = 'НЕАКТИВНО';
            
            positionDetailsElement.innerHTML = `
                <p style="color: #94a3b8; text-align: center; padding: 10px;">
                    Позиція не відкрита
                </p>
            `;
        }
    }
    
    // ПЕРЕВІРКА ТА ВХІД У ПОЗИЦІЇ
    checkAndEnterPosition() {
        if (!this.isRunning || this.emaFastData.length < 2 || this.emaSlowData.length < 2) return;
        
        const lastEma5 = this.emaFastData[this.emaFastData.length - 1].value;
        const prevEma5 = this.emaFastData[this.emaFastData.length - 2].value;
        const lastEma13 = this.emaSlowData[this.emaSlowData.length - 1].value;
        const prevEma13 = this.emaSlowData[this.emaSlowData.length - 2].value;
        
        const currentPrice = this.candleData.length > 0 ? this.candleData[this.candleData.length - 1].close : 0;
        
        // Сигнал BUY: EMA5 перетинає EMA13 знизу вверх
        if (prevEma5 <= prevEma13 && lastEma5 > lastEma13 && !this.currentPosition) {
            this.enterPosition('LONG', currentPrice);
        }
        
        // Сигнал SELL: EMA5 перетинає EMA13 зверху вниз
        if (prevEma5 >= prevEma13 && lastEma5 < lastEma13 && !this.currentPosition) {
            this.enterPosition('SHORT', currentPrice);
        }
        
        // Закриття позиції (простий варіант - зворотний сигнал)
        if (this.currentPosition) {
            if (this.currentPosition.type === 'LONG' && prevEma5 >= prevEma13 && lastEma5 < lastEma13) {
                this.exitPosition(currentPrice);
            } else if (this.currentPosition.type === 'SHORT' && prevEma5 <= prevEma13 && lastEma5 > lastEma13) {
                this.exitPosition(currentPrice);
            }
        }
    }
    
    // ВХІД У ПОЗИЦІЮ
    enterPosition(type, price) {
        this.currentPosition = {
            type: type,
            entryPrice: price,
            entryTime: Math.floor(Date.now() / 1000)
        };
        
        const signal = {
            timestamp: new Date().toISOString(),
            signal: type === 'LONG' ? 'BUY' : 'SELL',
            price: price,
            fast_ema: this.emaFastData[this.emaFastData.length - 1].value,
            slow_ema: this.emaSlowData[this.emaSlowData.length - 1].value,
            action: 'ENTER'
        };
        
        this.signals.push(signal);
        this.updateSignalsUI();
        
        this.log(`${type === 'LONG' ? '🔼' : '🔽'} ВХІД у ${type === 'LONG' ? 'ЛОНГ' : 'ШОРТ'} по $${price.toFixed(3)}`, 
                type === 'LONG' ? 'success' : 'error');
        
        this.updateStatistics();
    }
    
    // ВИХІД З ПОЗИЦІЇ
    exitPosition(price) {
        if (!this.currentPosition) return;
        
        const pnl = this.currentPosition.type === 'LONG' 
            ? price - this.currentPosition.entryPrice
            : this.currentPosition.entryPrice - price;
        
        // Оновлюємо баланс
        this.equity += pnl;
        
        // Оновлюємо статистику
        if (pnl > 0) {
            this.performance.wins++;
        } else {
            this.performance.losses++;
        }
        
        const trade = {
            entry: this.currentPosition,
            exitPrice: price,
            exitTime: Math.floor(Date.now() / 1000),
            pnl: pnl
        };
        
        this.trades.push(trade);
        
        const signal = {
            timestamp: new Date().toISOString(),
            signal: this.currentPosition.type === 'LONG' ? 'SELL' : 'BUY',
            price: price,
            action: 'EXIT',
            pnl: pnl
        };
        
        this.signals.push(signal);
        this.updateSignalsUI();
        
        this.log(`${this.currentPosition.type === 'LONG' ? '🔽' : '🔼'} ВИХІД з ${this.currentPosition.type === 'LONG' ? 'ЛОНГ' : 'ШОРТ'} по $${price.toFixed(3)} (PnL: ${pnl >= 0 ? '+' : ''}$${pnl.toFixed(3)})`, 
                pnl >= 0 ? 'success' : 'error');
        
        this.currentPosition = null;
        this.updateStatistics();
    }
    
    // ОНОВЛЕННЯ ТАБЛИЦІ СИГНАЛІВ
    updateSignalsUI() {
        const tbody = document.getElementById('signalsBody');
        if (!tbody) return;
        
        tbody.innerHTML = '';
        
        const recentSignals = this.signals.slice(-15).reverse();
        
        if (recentSignals.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="5" style="text-align: center; color: #94a3b8; padding: 20px;">
                        Ще немає сигналів
                    </td>
                </tr>
            `;
            return;
        }
        
        recentSignals.forEach(signal => {
            const row = document.createElement('tr');
            const time = new Date(signal.timestamp).toLocaleTimeString();
            
            let signalType = '';
            if (signal.signal === 'BUY') {
                signalType = signal.action === 'ENTER' ? 
                    '<span style="color:#10b981">🔼 ВХІД ЛОНГ</span>' : 
                    '<span style="color:#10b981">🔼 ВИХІД ШОРТ</span>';
            } else {
                signalType = signal.action === 'ENTER' ? 
                    '<span style="color:#ef4444">🔽 ВХІД ШОРТ</span>' : 
                    '<span style="color:#ef4444">🔽 ВИХІД ЛОНГ</span>';
            }
            
            let pnlCell = '';
            if (signal.pnl !== undefined) {
                const color = signal.pnl >= 0 ? '#10b981' : '#ef4444';
                const sign = signal.pnl >= 0 ? '+' : '';
                pnlCell = `<td style="color: ${color}">${sign}$${signal.pnl.toFixed(3)}</td>`;
            } else {
                pnlCell = '<td>-</td>';
            }
            
            row.innerHTML = `
                <td>${time}</td>
                <td>${signalType}</td>
                <td>$${signal.price?.toFixed(3) || '0.000'}</td>
                ${pnlCell}
                <td>${signal.action || '-'}</td>
            `;
            tbody.appendChild(row);
        });
    }
    
    // АВТООНОВЛЕННЯ (працює навіть якщо вкладка не активна)
    startAutoRefresh() {
        if (this.intervalId) clearInterval(this.intervalId);
        
        // Основний інтервал для оновлення даних
        this.intervalId = setInterval(async () => {
            try {
                // Оновлюємо статус
                await this.updateStatus();
                
                // Якщо скальпер працює
                if (this.isRunning) {
                    // Додаємо нову свічку кожну хвилину
                    this.addNewCandle();
                    
                    // Перевіряємо сигнали
                    this.checkAndEnterPosition();
                    
                    // Оновлюємо статистику
                    this.updateStatistics();
                }
            } catch (error) {
                console.error('Помилка автооновлення:', error);
            }
        }, 60000); // Кожну хвилину (для 1M свічок)
        
        // Швидке оновлення для поточної ціни
        this.priceIntervalId = setInterval(async () => {
            if (this.isRunning && this.candleData.length > 0) {
                try {
                    const response = await fetchScalperAPI('/api/scalper/test');
                    if (response.status === 'success' && response.price) {
                        // Оновлюємо останню свічку
                        const lastCandle = this.candleData[this.candleData.length - 1];
                        lastCandle.close = response.price;
                        lastCandle.high = Math.max(lastCandle.high, response.price);
                        lastCandle.low = Math.min(lastCandle.low, response.price);
                        
                        // Оновлюємо графік
                        this.updateChart();
                        
                        // Оновлюємо поточну ціну
                        this.updateCurrentPrice(response.price);
                    }
                } catch (error) {
                    console.error('Помилка оновлення ціни:', error);
                }
            }
        }, 2000); // Кожні 2 секунди
        
        console.log('🔄 Автооновлення запущено');
    }
    
    // ДОДАВАННЯ НОВОЇ СВІЧКИ
    addNewCandle() {
        if (this.candleData.length === 0) return;
        
        const lastCandle = this.candleData[this.candleData.length - 1];
        const now = Math.floor(Date.now() / 1000);
        
        // Якщо минула хвилина - створюємо нову свічку
        if (now - lastCandle.time >= 60) {
            const newCandle = {
                time: now,
                open: lastCandle.close,
                high: lastCandle.close,
                low: lastCandle.close,
                close: lastCandle.close
            };
            
            this.candleData.push(newCandle);
            
            // Обмежуємо кількість свічок
            if (this.candleData.length > 200) {
                this.candleData.shift();
            }
            
            // Перераховуємо EMA
            this.calculateEMA();
            
            this.log('🕯️ Додано нову свічку', 'info');
        }
    }
    
    // РЕШТА МЕТОДІВ
    bindEvents() {
        const startBtn = document.getElementById('btnStart');
        const stopBtn = document.getElementById('btnStop');
        const resetBtn = document.getElementById('btnReset');
        
        if (startBtn) startBtn.addEventListener('click', () => this.startScalper());
        if (stopBtn) stopBtn.addEventListener('click', () => this.stopScalper());
        if (resetBtn) resetBtn.addEventListener('click', () => this.resetScalper());
    }
    
    async startScalper() {
        this.log('▶️ Запуск скальпера...', 'info');
        
        try {
            const response = await fetchScalperAPI('/api/scalper/start', {
                method: 'POST'
            });
            
            if (response.status === 'success') {
                this.isRunning = true;
                this.updateUI();
                this.log('✅ Скальпер запущено', 'success');
            }
        } catch (error) {
            this.log(`❌ Помилка: ${error.message}`, 'error');
        }
    }
    
    async stopScalper() {
        this.log('⏹️ Зупинка скальпера...', 'info');
        
        try {
            const response = await fetchScalperAPI('/api/scalper/stop', {
                method: 'POST'
            });
            
            if (response.status === 'success') {
                this.isRunning = false;
                this.updateUI();
                this.log('✅ Скальпер зупинено', 'info');
            }
        } catch (error) {
            this.log(`❌ Помилка: ${error.message}`, 'error');
        }
    }
    
    async resetScalper() {
        this.log('🔄 Скидання стратегії...', 'info');
        
        try {
            const response = await fetchScalperAPI('/api/scalper/reset', {
                method: 'POST'
            });
            
            if (response.status === 'success') {
                this.currentPosition = null;
                this.signals = [];
                this.trades = [];
                this.equity = 1000.00;
                this.performance = { wins: 0, losses: 0 };
                
                await this.loadRealData();
                this.updateSignalsUI();
                this.updateStatistics();
                
                this.log('✅ Стратегію скинуто', 'success');
            }
        } catch (error) {
            this.log(`❌ Помилка: ${error.message}`, 'error');
        }
    }
    
    async updateStatus() {
        try {
            const response = await fetchScalperAPI('/api/scalper/status');
            
            if (response.status === 'success') {
                const { scalper, stream } = response;
                
                const statusIndicator = document.getElementById('statusIndicator');
                if (statusIndicator) {
                    if (stream && stream.running) {
                        statusIndicator.innerHTML = '<i class="fas fa-circle"></i> ОНЛАЙН';
                        statusIndicator.className = 'status status-online';
                        this.isRunning = true;
                    } else {
                        statusIndicator.innerHTML = '<i class="fas fa-circle"></i> ОФЛАЙН';
                        statusIndicator.className = 'status status-offline';
                        this.isRunning = false;
                    }
                }
                
                this.updateUI();
            }
        } catch (error) {
            console.error('Помилка оновлення статусу:', error);
        }
    }
    
    updateUI() {
        const startBtn = document.getElementById('btnStart');
        const stopBtn = document.getElementById('btnStop');
        
        if (startBtn && stopBtn) {
            startBtn.disabled = this.isRunning;
            stopBtn.disabled = !this.isRunning;
            
            startBtn.innerHTML = this.isRunning ? 
                '<i class="fas fa-pause"></i> Працює...' : 
                '<i class="fas fa-play"></i> Запустити';
                
            stopBtn.innerHTML = !this.isRunning ? 
                '<i class="fas fa-stop"></i> Зупинено' : 
                '<i class="fas fa-stop"></i> Зупинити';
        }
    }
    
    log(message, type = 'info') {
        const logElement = document.getElementById('eventLog');
        if (!logElement) return;
        
        const entry = document.createElement('div');
        const timestamp = new Date().toLocaleTimeString();
        const icons = { 'info': 'ℹ️', 'success': '✅', 'error': '❌', 'warning': '⚠️' };
        const icon = icons[type] || icons.info;
        const color = type === 'error' ? '#ef4444' : 
                     type === 'success' ? '#10b981' : 
                     type === 'warning' ? '#f59e0b' : '#94a3b8';
        
        entry.innerHTML = `
            <span style="color: #64748b">[${timestamp}]</span>
            <span style="color: ${color}; margin-left: 10px;">${icon} ${message}</span>
        `;
        
        logElement.prepend(entry);
        
        while (logElement.children.length > 20) {
            logElement.removeChild(logElement.lastChild);
        }
    }
}

// ========== ЗАПУСК ==========

document.addEventListener('DOMContentLoaded', () => {
    console.log('📄 DOM завантажено, ініціалізація скальпера...');
    
    const requiredElements = ['priceChart', 'btnStart', 'btnStop', 'statusIndicator'];
    const missingElements = requiredElements.filter(id => !document.getElementById(id));
    
    if (missingElements.length > 0) {
        console.error(`❌ Відсутні елементи: ${missingElements.join(', ')}`);
        return;
    }
    
    setTimeout(() => {
        try {
            window.scalperUI = new ScalperUISimple();
            console.log('✅ Scalper UI ініціалізовано');
        } catch (error) {
            console.error('❌ Помилка ініціалізації Scalper UI:', error);
        }
    }, 1000);
});