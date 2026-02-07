// main.js
const { app, BrowserWindow, ipcMain, Menu } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const isDev = !app.isPackaged;
const fetch = require('node-fetch');
let mainWindow;
let pythonProcess;
const SERVER_URL = 'http://127.0.0.1:5000'; // Використовуйте явно IPv4

const { Notification } = require('electron');

ipcMain.handle('show-notification', async (event, title, body) => {
    // Створюємо сповіщення
    const notification = new Notification({
        title: title || 'Solipsist Platform',
        body: body || 'Оновлення даних',
        icon: path.join(__dirname, 'assets/icon.png'),
        silent: false
    });
    
    notification.show();
    return { success: true };
});

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1200,
    minHeight: 700,
    icon: path.join(__dirname, 'assets/icon.png'),
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js')
    }
  });

  // Завантажуємо UI
  mainWindow.loadFile('src/renderer/index.html');
  
  if (isDev) {
    mainWindow.webContents.openDevTools();
  }
  
  // Запускаємо Python backend
  startPythonBackend();
  
  // Створюємо меню
  createMenu();
}

// Запуск Python
function startPythonBackend() {
  const pythonPath = isDev 
    ? path.join(__dirname, 'src/python/api_bridge.py')
    : path.join(process.resourcesPath, 'python/api_bridge.py');
  
  pythonProcess = spawn('python', [pythonPath]);
  
  pythonProcess.stdout.on('data', (data) => {
    console.log(`Python: ${data}`);
  });
  
  pythonProcess.stderr.on('data', (data) => {
    console.error(`Python Error: ${data}`);
  });
  
  pythonProcess.on('close', (code) => {
    console.log(`Python process exited with code ${code}`);
  });
}

// Меню додатку
function createMenu() {
  const template = [
    {
      label: 'Файл',
      submenu: [
        {
          label: 'Оновити арбітраж',
          accelerator: 'CmdOrCtrl+R',
          click: () => mainWindow.webContents.send('refresh-arbitrage')
        },
        { type: 'separator' },
        {
          label: 'Вихід',
          accelerator: 'CmdOrCtrl+Q',
          role: 'quit'
        }
      ]
    },
    {
      label: 'Торгівля',  // ← НОВИЙ РОЗДІЛ
      submenu: [
        {
          label: 'Арбітраж',
          click: () => mainWindow.loadFile('src/renderer/index.html')
        },
        {
          label: 'Скальпер SOL/USDT',
          click: () => mainWindow.loadFile('src/renderer/scalper.html')
        }
      ]
    },
    {
      label: 'Налаштування',
      submenu: [
        {
          label: 'Фільтри',
          click: () => mainWindow.webContents.send('open-filters')
        },
        {
          label: 'Біржі',
          click: () => mainWindow.webContents.send('open-exchanges')
        }
      ]
    },
    {
      label: 'Допомога',
      submenu: [
        {
          label: 'Документація',
          click: () => require('electron').shell.openExternal('https://github.com/Solipsist-crypton')
        },
        { type: 'separator' },
        {
          label: 'Про додаток',
          click: () => mainWindow.webContents.send('show-about')
        }
      ]
    }
  ];
  
  const menu = Menu.buildFromTemplate(template);
  Menu.setApplicationMenu(menu);
}

// Обробники IPC
ipcMain.handle('get-arbitrage', async () => {
    try {
        const response = await fetch('http://127.0.0.1:5000/arbitrage');
        return await response.json();
    } catch (error) {
        return { error: error.message };
    }
});
ipcMain.handle('save-config', async (event, config) => {
    // Зберегти конфігурацію
    return { status: 'saved' };
});

ipcMain.handle('load-config', async () => {
    // Завантажити конфігурацію
    return { theme: 'dark' };
});

ipcMain.handle('refresh-arbitrage', async () => {
  return await fetchPythonAPI('/arbitrage');
});

ipcMain.handle('get-exchanges', async () => {
  return await fetchPythonAPI('/exchanges');
});

// Обробники для скальпера
ipcMain.handle('scalper-start', async () => {
    console.log('[IPC] Запуск скальпера');
    try {
        const response = await fetch('http://127.0.0.1:5000/api/scalper/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        return await response.json();
    } catch (error) {
        return { status: 'error', message: error.message };
    }
});

ipcMain.handle('scalper-stop', async () => {
    console.log('[IPC] Зупинка скальпера');
    try {
        const response = await fetch('http://127.0.0.1:5000/api/scalper/stop', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        return await response.json();
    } catch (error) {
        return { status: 'error', message: error.message };
    }
});

ipcMain.handle('scalper-status', async () => {
    try {
        const response = await fetch('http://127.0.0.1:5000/api/scalper/status');
        return await response.json();
    } catch (error) {
        return { status: 'error', message: error.message };
    }
});



// Функція для запитів до Python API
async function fetchPythonAPI(endpoint, options = {}) {
  try {
    const response = await fetch(`http://127.0.0.1:5000${endpoint}`, {
      headers: { 'Content-Type': 'application/json' },
      ...options
    });
    return await response.json();
  } catch (error) {
    console.error('API Error:', error);
    return { error: 'Не вдалося підключитися до сервера' };
  }
}

// Життєвий цикл додатку
app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
  if (pythonProcess) pythonProcess.kill();
  if (process.platform !== 'darwin') app.quit();
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) createWindow();
});

// Завершення Python процесу
app.on('before-quit', () => {
  if (pythonProcess) pythonProcess.kill();
});