const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  checkUrls: (urls, keywords) => ipcRenderer.invoke('check-urls', urls, keywords),
  getHistory: () => ipcRenderer.invoke('get-history'),
  getHistoryFile: (filename) => ipcRenderer.invoke('get-history-file', filename)
});

ipcRenderer.on('log', (event, message) => {
  console.log('[Renderer]', message);
});
