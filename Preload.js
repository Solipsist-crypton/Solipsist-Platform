const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  // Арбітраж
  getArbitrage: () => ipcRenderer.invoke('get-arbitrage'),
  updateArbitrage: () => ipcRenderer.invoke('update-arbitrage'),
  
  // Налаштування
  getExchanges: () => ipcRenderer.invoke('get-exchanges'),
  setFilters: (filters) => ipcRenderer.invoke('set-filters', filters),
  
  // UI події
  onRefreshArbitrage: (callback) => 
    ipcRenderer.on('refresh-arbitrage', callback),
  
  // Файли
  saveConfig: (config) => ipcRenderer.invoke('save-config', config),
  loadConfig: () => ipcRenderer.invoke('load-config'),
  
  // Додатково
  openUrl: (url) => ipcRenderer.invoke('open-url', url),
  
  // МЕТОДИ ДЛЯ СКАЛЬПЕРА
  startScalper: () => ipcRenderer.invoke('scalper-start'),
  stopScalper: () => ipcRenderer.invoke('scalper-stop'),
  getScalperStatus: () => ipcRenderer.invoke('scalper-status'),
  
  // Універсальний метод для запитів до Python API (для скальпера)
  fetchPythonAPI: (endpoint, options) => 
    ipcRenderer.invoke('fetch-python-api', endpoint, options),
  
  // АБО спеціальний метод для скальпера
  fetchScalperAPI: (endpoint, method = 'GET', data = null) => 
    ipcRenderer.invoke('fetch-scalper-api', endpoint, method, data),
  
  // Сповіщення (ТІЛЬКИ ОДИН РАЗ!)
  showNotification: (title, body) => 
    ipcRenderer.invoke('show-notification', title, body)
});