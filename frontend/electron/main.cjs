const { app, BrowserWindow, shell } = require('electron');
const path = require('path');
const { pathToFileURL } = require('url');
const { spawn } = require('child_process');

let mainWindow;
let backendProcess;

function isSafeExternalUrl(rawUrl) {
  try {
    const url = new URL(rawUrl);
    return ['https:', 'http:', 'mailto:'].includes(url.protocol);
  } catch {
    return false;
  }
}

function isAppNavigation(rawUrl) {
  try {
    const url = new URL(rawUrl);
    if (url.protocol === 'file:') {
      const appIndex = pathToFileURL(path.join(__dirname, '../dist/index.html'));
      return url.origin === appIndex.origin && url.pathname === appIndex.pathname;
    }
    return url.protocol === 'http:' && ['localhost', '127.0.0.1'].includes(url.hostname) && url.port === '5173';
  } catch {
    return false;
  }
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      sandbox: true,
      webSecurity: true
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

  // 文档预览中的链接不得把应用窗口导航到不可信页面，也不得创建新窗口。
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    if (isSafeExternalUrl(url)) {
      void shell.openExternal(url);
    }
    return { action: 'deny' };
  });

  mainWindow.webContents.on('will-navigate', (event, url) => {
    if (!isAppNavigation(url)) {
      event.preventDefault();
      if (isSafeExternalUrl(url)) {
        void shell.openExternal(url);
      }
    }
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

function startBackend() {
  const backendPath = path.join(__dirname, '../../backend');
  const pythonCmd = process.platform === 'darwin' ? 'python3' : 'python';

  // 默认仅本机可达，避免局域网无鉴权暴露上传/删除/推送接口
  backendProcess = spawn(pythonCmd, ['-m', 'uvicorn', 'main:app', '--host', '127.0.0.1', '--port', '8000'], {
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
