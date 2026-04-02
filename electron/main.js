const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const log = require('electron-log');
const { checkSingleUrl, detectPlatform } = require('./utils');

log.transports.file.level = 'info';
log.transports.console.level = 'info';

let mainWindow;

async function checkUrlsBatch(urls, keywords) {
    const promises = urls.map(url => checkSingleUrl(url, keywords));
    return Promise.all(promises);
}

ipcMain.handle('check-urls', async (event, urls, keywords) => {
    log.info(`开始检测 ${urls.length} 个URL`);
    const keywordList = keywords.split(',').map(k => k.trim()).filter(k => k);
    const results = await checkUrlsBatch(urls, keywordList);
    
    return {
        total: results.length,
        accessible: results.filter(r => r.可访问 === '可访问').length,
        blocked: results.filter(r => r.blocked).length,
        inaccessible: results.filter(r => r.可访问 === '不可访问').length,
        with_keywords: results.filter(r => r.命中关键词).length,
        results: results
    };
});

ipcMain.handle('get-history', async () => {
    const fs = require('fs');
    const outputDir = path.join(app.getPath('userData'), 'monitor_results');
    
    try {
        if (!fs.existsSync(outputDir)) {
            return [];
        }
        const files = fs.readdirSync(outputDir)
            .filter(f => f.startsWith('monitor_result_') && f.endsWith('.csv'))
            .sort()
            .reverse();
        return files;
    } catch (e) {
        log.error('读取历史失败:', e);
        return [];
    }
});

ipcMain.handle('get-history-file', async (event, filename) => {
    const fs = require('fs');
    const outputDir = path.join(app.getPath('userData'), 'monitor_results');
    const filepath = path.join(outputDir, filename);
    
    try {
        if (!fs.existsSync(filepath)) {
            return { total: 0, accessible: 0, with_keywords: 0, rows: [] };
        }
        const content = fs.readFileSync(filepath, 'utf-8');
        const lines = content.split('\n').filter(l => l.trim());
        if (lines.length < 2) {
            return { total: 0, accessible: 0, with_keywords: 0, rows: [] };
        }
        
        const headers = lines[0].split(',');
        const rows = [];
        for (let i = 1; i < lines.length; i++) {
            const values = lines[i].split(',');
            const row = {};
            headers.forEach((h, idx) => {
                row[h.trim()] = values[idx] ? values[idx].trim() : '';
            });
            rows.push(row);
        }
        
        return {
            total: rows.length,
            accessible: rows.filter(r => r['发布状态'] === '可访问').length,
            with_keywords: rows.filter(r => r['命中关键词'] && r['命中关键词'].trim()).length,
            rows: rows
        };
    } catch (e) {
        log.error('读取文件失败:', e);
        return { total: 0, accessible: 0, with_keywords: 0, rows: [] };
    }
});

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1200,
        height: 800,
        minWidth: 900,
        minHeight: 600,
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true,
            preload: path.join(__dirname, 'preload.js')
        },
        show: false
    });

    mainWindow.loadFile('index.html');

    mainWindow.once('ready-to-show', () => {
        mainWindow.show();
        log.info('主窗口已显示');
    });

    mainWindow.on('closed', () => {
        mainWindow = null;
    });
}

app.whenReady().then(() => {
    log.info('应用启动');
    createWindow();

    app.on('activate', () => {
        if (BrowserWindow.getAllWindows().length === 0) {
            createWindow();
        }
    });
});

app.on('window-all-closed', () => {
    log.info('所有窗口已关闭');
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

process.on('uncaughtException', (error) => {
    log.error('未捕获异常:', error);
});
