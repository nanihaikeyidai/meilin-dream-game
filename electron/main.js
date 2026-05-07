const { app, BrowserWindow, ipcMain, nativeTheme } = require('electron');
const path = require('path');
const { setupIpcHandlers } = require('./ipc-handlers');

function createWindow() {
  nativeTheme.themeSource = 'dark';

  const win = new BrowserWindow({
    width: 1200,
    height: 800,
    titleBarStyle: 'hiddenInset',
    titleBarOverlay: {
      color: '#1a1a2e',
      symbolColor: '#e0e0ff',
      height: 32
    },
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false
    }
  });

  win.loadFile(path.join(__dirname, '..', 'frontend', 'index.html'));

  if (process.env.NODE_ENV === 'development') {
    win.webContents.openDevTools();
  }
}

app.whenReady().then(() => {
  setupIpcHandlers();
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});
