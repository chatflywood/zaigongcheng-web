const { app, BrowserWindow } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

let mainWindow;
let backendProcess;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true
    },
    title: '工程建设数据驾舱',
    icon: path.join(__dirname, '../public/favicon.svg')
  });

  // 开发模式用 localhost:5173，生产模式用打包后的文件
  const isDev = process.env.NODE_ENV === 'development' || !app.isPackaged;

  if (isDev) {
    mainWindow.loadURL('http://localhost:5173');
    mainWindow.webContents.openDevTools();
  } else {
    mainWindow.loadFile(path.join(__dirname, '../dist/index.html'));
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

function startBackend() {
  const backendPath = path.join(__dirname, '../../backend');
  const pythonCmd = process.platform === 'darwin' ? 'python3' : 'python';

  backendProcess = spawn(pythonCmd, ['-m', 'uvicorn', 'main:app', '--host', '0.0.0.0', '--port', '8000'], {
    cwd: backendPath,
    stdio: 'pipe'
  });

  backendProcess.stdout.on('data', (data) => {
    console.log(`[后端] ${data}`);
  });

  backendProcess.stderr.on('data', (data) => {
    console.error(`[后端错误] ${data}`);
  });

  backendProcess.on('close', (code) => {
    console.log(`[后端进程退出] code: ${code}`);
  });
}

function stopBackend() {
  if (backendProcess) {
    backendProcess.kill();
    backendProcess = null;
  }
}

app.whenReady().then(() => {
  startBackend();
  createWindow();

  // 等待后端启动后再加载页面
  setTimeout(() => {
    if (mainWindow) {
      mainWindow.webContents.on('did-fail-load', (event, errorCode, errorDescription) => {
        console.error(`[页面加载失败] ${errorCode}: ${errorDescription}`);
      });
    }
  }, 3000);
});

app.on('window-all-closed', () => {
  stopBackend();
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (mainWindow === null) {
    createWindow();
  }
});

app.on('before-quit', () => {
  stopBackend();
});
