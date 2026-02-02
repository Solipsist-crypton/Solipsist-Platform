// main.js
const { app, BrowserWindow, ipcMain, Menu } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const isDev = !app.isPackaged;
const fetch = require('node-fetch');
let mainWindow;
let pythonProcess;

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
        const response = await fetch('http://localhost:5000/arbitrage');
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

ipcMain.handle('update-arbitrage', async () => {
  return await fetchPythonAPI('/update', { method: 'POST' });
});

ipcMain.handle('get-exchanges', async () => {
  return await fetchPythonAPI('/exchanges');
});

// Функція для запитів до Python API
async function fetchPythonAPI(endpoint, options = {}) {
  try {
    const response = await fetch(`http://localhost:5000${endpoint}`, {
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