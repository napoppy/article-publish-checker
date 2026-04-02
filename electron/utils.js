const https = require('https');
const http = require('http');
const { URL } = require('url');

function detectPlatform(url) {
    const urlLower = url.toLowerCase();
    const PLATFORMS = {
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
    };
    
    for (const [platform, patterns] of Object.entries(PLATFORMS)) {
        for (const pattern of patterns) {
            if (urlLower.includes(pattern)) {
                return platform;
            }
        }
    }
    return 'unknown';
}

function parseHTML(text) {
    const scripts = [];
    const styles = [];
    let depth = 0;
    let current = '';
    let inTag = false;
    let tagName = '';
    
    for (let i = 0; i < text.length; i++) {
        const char = text[i];
        
        if (char === '<') {
            inTag = true;
            current += char;
            tagName = '';
        } else if (char === '>' && inTag) {
            inTag = false;
            current += char;
            
            const tagMatch = tagName.match(/^\/?(\w+)/);
            if (tagMatch) {
                const name = tagMatch[1].toLowerCase();
                if (name === 'script') {
                    if (tagName.startsWith('/')) {
                        scripts.push(current);
                    } else {
                        tagName = '';
                        current = '';
                        continue;
                    }
                } else if (name === 'style') {
                    if (tagName.startsWith('/')) {
                        styles.push(current);
                    } else {
                        tagName = '';
                        current = '';
                        continue;
                    }
                }
            }
            
            current = '';
            tagName = '';
        } else if (inTag) {
            tagName += char;
            current += char;
        }
    }
    
    let result = text;
    scripts.forEach(s => result = result.replace(s, ''));
    styles.forEach(s => result = result.replace(s, ''));
    
    result = result.replace(/<[^>]+>/g, ' ');
    result = result.replace(/\s+/g, ' ').trim();
    
    return result;
}

function checkSingleUrl(url, keywords) {
    return new Promise((resolve) => {
        const result = {
            URL: url.trim(),
            平台: detectPlatform(url.trim()),
            监测时间: new Date().toLocaleString('zh-CN')
        };
        
        try {
            const parsedUrl = new URL(url.trim());
            const options = {
                hostname: parsedUrl.hostname,
                port: parsedUrl.port || (parsedUrl.protocol === 'https:' ? 443 : 80),
                path: parsedUrl.pathname + parsedUrl.search,
                method: 'GET',
                headers: {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                    'Accept-Encoding': 'gzip, deflate',
                    'Connection': 'keep-alive',
                }
            };
            
            const req = (parsedUrl.protocol === 'https:' ? https : http).request(options, (res) => {
                result.状态码 = res.statusCode;
                
                if (res.statusCode >= 200 && res.statusCode < 400) {
                    const chunks = [];
                    res.on('data', chunk => chunks.push(chunk));
                    res.on('end', () => {
                        const body = Buffer.concat(chunks).toString('utf8');
                        
                        if (body.length < 5000) {
                            result.blocked = true;
                            result.可访问 = '可访问(疑似拦截)';
                        } else {
                            result.可访问 = '可访问';
                            const text = parseHTML(body.toLowerCase());
                            const matched = keywords.filter(k => text.includes(k.toLowerCase()));
                            result.命中关键词 = matched.join(', ');
                        }
                        resolve(result);
                    });
                } else {
                    result.可访问 = '不可访问';
                    result.命中关键词 = '';
                    resolve(result);
                }
            });
            
            req.on('error', (e) => {
                result.可访问 = '不可访问';
                result.状态码 = null;
                result.命中关键词 = '';
                result.error = e.message;
                resolve(result);
            });
            
            req.setTimeout(10000, () => {
                req.destroy();
                result.可访问 = '不可访问';
                result.状态码 = null;
                result.命中关键词 = '';
                result.error = 'Timeout';
                resolve(result);
            });
            
            req.end();
        } catch (e) {
            result.可访问 = '不可访问';
            result.状态码 = null;
            result.命中关键词 = '';
            result.error = e.message;
            resolve(result);
        }
    });
}

module.exports = { checkSingleUrl, detectPlatform };
