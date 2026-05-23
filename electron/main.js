const { app, BrowserWindow, nativeTheme } = require('electron');
const path = require('path');
const { startServer } = require('../server');
const { setupIpcHandlers } = require('./ipc-handlers');

let mainWindow = null;
let gameServer = null;
let gameBaseUrl = '';

function getAppRoot() {
  return app.isPackaged ? app.getAppPath() : path.join(__dirname, '..');
}

async function bootGameServer() {
  const root = getAppRoot();
  const userDataDir = app.getPath('userData');
  const result = await startServer({
    root,
    userDataDir,
    host: '127.0.0.1',
    port: 0,
    silent: !process.env.NODE_ENV || process.env.NODE_ENV === 'production',
  });
  gameServer = result.server;
  gameBaseUrl = result.url.replace(/\/$/, '');
  return gameBaseUrl;
}

function createWindow() {
  nativeTheme.themeSource = 'dark';

  const winOptions = {
    width: 1280,
    height: 800,
    minWidth: 960,
    minHeight: 640,
    show: false,
    title: 'AVG梦工厂',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  };

  if (process.platform === 'darwin') {
    winOptions.titleBarStyle = 'hiddenInset';
    winOptions.titleBarOverlay = {
      color: '#1a1a2e',
      symbolColor: '#e0e0ff',
      height: 32,
    };
  }

  mainWindow = new BrowserWindow(winOptions);
  mainWindow.once('ready-to-show', () => mainWindow.show());
  mainWindow.loadURL(`${gameBaseUrl}/`);

  if (process.env.NODE_ENV === 'development') {
    mainWindow.webContents.openDevTools({ mode: 'detach' });
  }
}

app.whenReady().then(async () => {
  setupIpcHandlers({
    getBaseUrl: () => gameBaseUrl,
    getAppRoot,
  });

  try {
    await bootGameServer();
    createWindow();
  } catch (err) {
    console.error('Failed to start embedded server:', err);
    app.quit();
  }

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0 && gameBaseUrl) createWindow();
  });
});

app.on('before-quit', () => {
  if (gameServer) gameServer.close();
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});
