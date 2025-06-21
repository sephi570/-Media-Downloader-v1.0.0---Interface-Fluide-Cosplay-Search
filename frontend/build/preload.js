const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld('electronAPI', {
  getAppVersion: () => ipcRenderer.invoke('get-app-version'),
  showSaveDialog: () => ipcRenderer.invoke('show-save-dialog'),
  openDownloadsFolder: () => ipcRenderer.invoke('open-downloads-folder'),
  
  // Listen to menu events
  onNewDownload: (callback) => ipcRenderer.on('new-download', callback),
  
  // Platform info
  platform: process.platform,
  
  // App info
  versions: {
    node: process.versions.node,
    chrome: process.versions.chrome,
    electron: process.versions.electron
  }
});