const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  apiKey: {
    save: (data) => ipcRenderer.invoke('apiKey:save', data),
    load: () => ipcRenderer.invoke('apiKey:load')
  },
  app: {
    exit: () => ipcRenderer.send('app:exit')
  },
  navigate: {
    to: (page) => ipcRenderer.send('navigate:to', page)
  },
  templates: {
    list: () => ipcRenderer.invoke('templates:list')
  },
  fs: {
    read: (filePath) => ipcRenderer.invoke('fs:read', filePath)
  },
  llm: {
    chat: (messages, config) => ipcRenderer.invoke('llm:chat', { messages, config })
  }
});
