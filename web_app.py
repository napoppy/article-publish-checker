from flask import Flask, render_template_string, request, jsonify
import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
from datetime import datetime
import concurrent.futures

app = Flask(__name__)

PLATFORMS = {
    'csdn': ['csdn.net', 'blog.csdn.net'],
    'juejin': ['juejin.cn', 'juejin.im'],
    'freebuf': ['freebuf.com'],
    'zhihu': ['zhihu.com'],
    'xiaohongshu': ['xiaohongshu.com', 'xhslink.com'],
    '51cto': ['51cto.com'],
    'tencent_cloud': ['cloud.tencent.com', 'developer.tencent.com'],
    'aliyun': ['aliyun.com', 'developer.aliyun.com'],
    'jianshu': ['jianshu.com'],
    'cnblogs': ['cnblogs.com'],
    'huawei_cloud': ['huaweicloud.com'],
}

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>多平台文章监测系统</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f0f2f5; min-height: 100vh; }
        .header { background: #1890ff; color: white; padding: 20px; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.15); }
        .header h1 { font-size: 24px; }
        .container { max-width: 1200px; margin: 20px auto; padding: 0 20px; }
        .card { background: white; border-radius: 8px; padding: 24px; margin-bottom: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }
        .form-group { margin-bottom: 15px; }
        label { display: block; margin-bottom: 5px; font-weight: 500; color: #333; }
        input[type="text"], textarea { width: 100%; padding: 10px; border: 1px solid #d9d9d9; border-radius: 4px; font-size: 14px; font-family: inherit; }
        textarea { height: 120px; resize: vertical; }
        .btn { background: #1890ff; color: white; border: none; padding: 10px 24px; border-radius: 4px; cursor: pointer; font-size: 14px; }
        .btn:hover { background: #40a9ff; }
        .btn:disabled { background: #d9d9d9; cursor: not-allowed; }
        .stats { display: flex; gap: 20px; margin-bottom: 20px; flex-wrap: wrap; }
        .stat-box { flex: 1; min-width: 120px; background: white; padding: 20px; border-radius: 8px; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }
        .stat-value { font-size: 28px; font-weight: bold; color: #1890ff; }
        .stat-label { color: #666; margin-top: 5px; }
        table { width: 100%; border-collapse: collapse; }
        th { background: #1890ff; color: white; padding: 12px; text-align: left; }
        td { padding: 10px 12px; border-bottom: 1px solid #f0f0f0; }
        tr:hover { background: #fafafa; }
        .status-ok { color: #52c41a; font-weight: bold; }
        .status-fail { color: #ff4d4f; font-weight: bold; }
        .keyword-tag { display: inline-block; background: #e6f7ff; color: #1890ff; padding: 2px 8px; border-radius: 4px; margin: 2px; font-size: 12px; }
        .tabs { display: flex; gap: 10px; margin-bottom: 20px; }
        .tab { padding: 10px 20px; background: white; border: 1px solid #d9d9d9; border-radius: 4px; cursor: pointer; }
        .tab.active { background: #1890ff; color: white; border-color: #1890ff; }
        .hidden { display: none; }
        .history-item { padding: 10px; border-bottom: 1px solid #f0f0f0; cursor: pointer; }
        .history-item:hover { background: #fafafa; }
        .progress { margin: 10px 0; color: #666; }
        .url-item { padding: 8px 12px; background: #fafafa; border-radius: 4px; margin: 4px 0; display: flex; align-items: center; gap: 10px; }
        .url-item .status-icon { font-size: 16px; }
        .url-item .url-text { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
        .batch-result { max-height: 400px; overflow-y: auto; }
    </style>
</head>
<body>
    <div class="header"><h1>多平台文章发布状态监测系统</h1></div>
    <div class="container">
        <div class="tabs">
            <div class="tab active" onclick="showTab('check')">URL检测</div>
            <div class="tab" onclick="showTab('history')">历史报告</div>
        </div>
        
        <div id="check-tab">
            <div class="card">
                <h3 style="margin-bottom: 15px;">输入URL进行检测 (支持批量，每行一个)</h3>
                <div class="form-group">
                    <label>URL地址 (每行一个)</label>
                    <textarea id="urls" placeholder="https://blog.csdn.net/example/article/details/123456&#10;https://juejin.cn/post/123456789&#10;https://www.freebuf.com/articles/web/789012.html"></textarea>
                </div>
                <div class="form-group">
                    <label>关键词 (逗号分隔)</label>
                    <input type="text" id="keywords" value="pandawiki, monkeycode, 开源">
                </div>
                <button class="btn" id="checkBtn" onclick="checkUrls()">开始检测</button>
            </div>
            
            <div id="progress-area" class="card hidden">
                <div class="progress" id="progress-text">准备中...</div>
            </div>
            
            <div id="result-area" class="hidden">
                <div class="stats" id="stats"></div>
                <div class="card batch-result">
                    <h4 style="margin-bottom: 15px;">检测结果</h4>
                    <div id="result-list"></div>
                </div>
            </div>
        </div>
        
        <div id="history-tab" class="hidden">
            <div class="card">
                <h3 style="margin-bottom: 15px;">历史报告</h3>
                <div id="file-list"></div>
            </div>
            <div id="history-content" class="hidden">
                <div class="stats" id="history-stats"></div>
                <div class="card">
                    <table id="history-table"></table>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        function showTab(tab) {
            document.querySelectorAll('.tab').ForEach(t => t.classList.remove('active'));
            event.target.classList.add('active');
            document.getElementById('check-tab').classList.toggle('hidden', tab !== 'check');
            document.getElementById('history-tab').classList.toggle('hidden', tab !== 'history');
            if (tab === 'history') loadHistory();
        }
        
        async function checkUrls() {
            const urlsText = document.getElementById('urls').value.trim();
            const keywords = document.getElementById('keywords').value;
            if (!urlsText) { alert('请输入URL'); return; }
            
            const urls = urlsText.split('\\n').filter(u => u.trim());
            if (urls.length === 0) { alert('请输入有效的URL'); return; }
            
            const btn = document.getElementById('checkBtn');
            btn.disabled = true;
            btn.textContent = '检测中...';
            
            document.getElementById('progress-area').classList.remove('hidden');
            document.getElementById('result-area').classList.add('hidden');
            
            try {
                const res = await fetch('/api/check-batch', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({urls, keywords})
                });
                const data = await res.json();
                showResults(data);
            } catch (e) {
                alert('检测失败: ' + e);
            } finally {
                btn.disabled = false;
                btn.textContent = '开始检测';
                document.getElementById('progress-area').classList.add('hidden');
            }
        }
        
        function showResults(data) {
            document.getElementById('result-area').classList.remove('hidden');
            document.getElementById('stats').innerHTML = `
                <div class="stat-box"><div class="stat-value">${data.total}</div><div class="stat-label">总URL</div></div>
                <div class="stat-box"><div class="stat-value">${data.accessible}</div><div class="stat-label">可访问</div></div>
                <div class="stat-box"><div class="stat-value">${data.inaccessible}</div><div class="stat-label">不可访问</div></div>
                <div class="stat-box"><div class="stat-value">${data.with_keywords}</div><div class="stat-label">命中关键词</div></div>
            `;
            
            document.getElementById('result-list').innerHTML = data.results.map(r => `
                <div class="url-item">
                    <span class="status-icon">${r['发布状态'] === '可访问' ? '✓' : '✗'}</span>
                    <span class="url-text" title="${r['URL']}">${r['URL']}</span>
                    <span class="${r['发布状态'] === '可访问' ? 'status-ok' : 'status-fail'}">${r['发布状态']}</span>
                    <span>${r['状态码'] || '-'}</span>
                    ${r['命中关键词'] ? r['命中关键词'].split(',').map(k => `<span class="keyword-tag">${k.trim()}</span>`).join('') : '<span style="color:#999;">无</span>'}
                </div>
            `).join('');
        }
        
        async function loadHistory() {
            const res = await fetch('/api/history');
            const files = await res.json();
            const list = document.getElementById('file-list');
            if (files.length === 0) {
                list.innerHTML = '<p style="color:#666;">暂无历史报告</p>';
                return;
            }
            list.innerHTML = files.map(f => `<div class="history-item" onclick="loadFile('${f}')">${f}</div>`).join('');
        }
        
        async function loadFile(filename) {
            const res = await fetch('/api/history/' + filename);
            const data = await res.json();
            document.getElementById('history-content').classList.remove('hidden');
            document.getElementById('history-stats').innerHTML = `
                <div class="stat-box"><div class="stat-value">${data.total}</div><div class="stat-label">总URL</div></div>
                <div class="stat-box"><div class="stat-value">${data.accessible}</div><div class="stat-label">可访问</div></div>
                <div class="stat-box"><div class="stat-value">${data.with_keywords}</div><div class="stat-label">命中关键词</div></div>
            `;
            document.getElementById('history-table').innerHTML = `
                <thead><tr><th>平台</th><th>URL</th><th>状态</th><th>关键词</th></tr></thead>
                <tbody>${data.rows.map(r => `
                    <tr>
                        <td>${r['平台']}</td>
                        <td><a href="${r['URL']}" target="_blank">${r['URL'].substring(0, 50)}...</a></td>
                        <td class="${r['发布状态'] === '可访问' ? 'status-ok' : 'status-fail'}">${r['发布状态']}</td>
                        <td>${r['命中关键词'] || '-'}</td>
                    </tr>
                `).join('')}</tbody>
            `;
        }
    </script>
</body>
</html>
'''

def detect_platform(url):
    url_lower = url.lower()
    for platform, patterns in PLATFORMS.items():
        for pattern in patterns:
            if pattern in url_lower:
                return platform
    return 'unknown'

def check_single_url(url, keywords):
    result = {
        'URL': url.strip(),
        '平台': detect_platform(url.strip()),
        '监测时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        r = requests.get(url.strip(), timeout=10, headers=headers)
        result['状态码'] = r.status_code
        result['发布状态'] = '可访问' if 200 <= r.status_code < 400 else '不可访问'
        
        if result['发布状态'] == '可访问':
            soup = BeautifulSoup(r.text, 'html.parser')
            for tag in soup.find_all(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                tag.decompose()
            text = soup.get_text(separator=' ', strip=True).lower()
            matched = [k for k in keywords if k.lower() in text]
            result['命中关键词'] = ', '.join(matched)
        else:
            result['命中关键词'] = ''
    except Exception as e:
        result['发布状态'] = '不可访问'
        result['状态码'] = None
        result['命中关键词'] = ''
        result['error'] = str(e)
    
    return result

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/check-batch', methods=['POST'])
def check_batch():
    data = request.json
    urls = data['urls']
    keywords = [k.strip() for k in data.get('keywords', '').split(',') if k.strip()]
    
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(check_single_url, url, keywords): url for url in urls}
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())
    
    return jsonify({
        'total': len(results),
        'accessible': sum(1 for r in results if r['发布状态'] == '可访问'),
        'inaccessible': sum(1 for r in results if r['发布状态'] == '不可访问'),
        'with_keywords': sum(1 for r in results if r.get('命中关键词')),
        'results': results
    })

@app.route('/api/history')
def history():
    files = sorted([f for f in os.listdir('.') if f.startswith('monitor_result_') and f.endswith('.csv')], reverse=True)
    return jsonify(files)

@app.route('/api/history/<filename>')
def history_file(filename):
    df = pd.read_csv(filename)
    return jsonify({
        'total': len(df),
        'accessible': len(df[df['发布状态'] == '可访问']),
        'with_keywords': len(df[df['命中关键词'].notna() & (df['命中关键词'] != '')]),
        'rows': df.to_dict('records')
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8501)
