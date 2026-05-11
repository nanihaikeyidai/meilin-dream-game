/**
 * Girlgame 开发服务器（零依赖版）
 * - 提供前端静态文件
 * - 代理 /proxy/chat/completions → LLM API
 * 
 * 启动: node server.js
 * 默认: http://localhost:8080
 */

const http = require('http');
const fs = require('fs');
const path = require('path');

const PORT = process.env.PORT || 8080;
const LLM_BASE = process.env.LLM_BASE || 'http://localhost:8642';
const FRONTEND_DIR = path.join(__dirname, 'frontend');

const MIME_TYPES = {
  '.html': 'text/html; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.js': 'application/javascript; charset=utf-8',
  '.json': 'application/json',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.svg': 'image/svg+xml',
  '.ico': 'image/x-icon',
};

// 解析 LLM 地址
const llmUrl = new URL(LLM_BASE);

function serveStatic(res, filePath) {
  const ext = path.extname(filePath);
  fs.readFile(filePath, (err, data) => {
    if (err) {
      // SPA fallback: 返回 index.html
      fs.readFile(path.join(FRONTEND_DIR, 'index.html'), (err2, indexData) => {
        if (err2) {
          res.writeHead(500);
          res.end('Internal Server Error');
        } else {
          res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
          res.end(indexData);
        }
      });
      return;
    }
    res.writeHead(200, { 'Content-Type': MIME_TYPES[ext] || 'application/octet-stream' });
    res.end(data);
  });
}

function proxyLLM(reqBody, res) {
  const body = JSON.stringify({
    model: reqBody.model || 'deepseek-v4-flash',
    messages: reqBody.messages || [],
    temperature: reqBody.temperature ?? 0.7,
    max_tokens: reqBody.max_tokens ?? 1024,
  });

  const options = {
    hostname: llmUrl.hostname,
    port: llmUrl.port || 80,
    path: '/v1/chat/completions',
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Content-Length': Buffer.byteLength(body),
    },
  };

  const proxyReq = http.request(options, (proxyRes) => {
    let data = '';
    proxyRes.on('data', chunk => data += chunk);
    proxyRes.on('end', () => {
      // 透传 LLM 的响应给前端
      res.writeHead(proxyRes.statusCode, {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
      });
      res.end(data);
    });
  });

  proxyReq.on('error', (err) => {
    console.error(`[Proxy Error]`, err.message);
    res.writeHead(502, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ error: 'LLM API 不可达', detail: err.message }));
  });

  proxyReq.write(body);
  proxyReq.end();
}

function parseBody(req, callback) {
  let body = '';
  req.on('data', chunk => body += chunk);
  req.on('end', () => {
    try {
      callback(JSON.parse(body));
    } catch {
      callback(null);
    }
  });
}

const server = http.createServer((req, res) => {
  // CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');

  if (req.method === 'OPTIONS') {
    res.writeHead(204);
    res.end();
    return;
  }

  const url = new URL(req.url, `http://localhost:${PORT}`);

  // API 代理路由
  if (url.pathname === '/proxy/chat/completions' && req.method === 'POST') {
    parseBody(req, (body) => {
      if (!body) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: 'Invalid JSON body' }));
        return;
      }
      proxyLLM(body, res);
    });
    return;
  }

  // 健康检查
  if (url.pathname === '/proxy/health') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ status: 'ok', llm: LLM_BASE }));
    return;
  }

  // 静态文件
  let filePath = path.join(FRONTEND_DIR, url.pathname === '/' ? 'index.html' : url.pathname);
  serveStatic(res, filePath);
});

server.listen(PORT, () => {
  console.log(`🚀 Girlgame 开发服务器已启动`);
  console.log(`   📂 前端: http://localhost:${PORT}`);
  console.log(`   🔗 API 代理: /proxy/chat/completions → ${LLM_BASE}/v1/chat/completions`);
  console.log(`   ℹ️  按 Ctrl+C 停止`);
});
