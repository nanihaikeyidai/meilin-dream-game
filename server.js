/**
 * Girlgame 开发服务器（零依赖版）
 * - 前端静态文件
 * - 剧本 markdown（/templates/）
 * - 代理 LLM：/proxy/chat/completions
 * - 代理 TTS：/proxy/tts
 *
 * 启动: node server.js
 * 环境变量: PORT, LLM_BASE, TTS_BASE
 */

const http = require('http');
const fs = require('fs');
const path = require('path');

const PORT = process.env.PORT || 8080;
const LLM_BASE = process.env.LLM_BASE || 'http://localhost:8656';
const TTS_BASE = process.env.TTS_BASE || 'http://localhost:7860';
const ROOT = __dirname;
const FRONTEND_DIR = path.join(ROOT, 'frontend');
const TEMPLATES_DIR = path.join(ROOT, 'templates');

const MIME_TYPES = {
  '.html': 'text/html; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.js': 'application/javascript; charset=utf-8',
  '.json': 'application/json',
  '.md': 'text/markdown; charset=utf-8',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.svg': 'image/svg+xml',
  '.wav': 'audio/wav',
  '.ico': 'image/x-icon',
};

const llmUrl = new URL(LLM_BASE);
const ttsUrl = new URL(TTS_BASE);

function sendJson(res, status, obj) {
  res.writeHead(status, {
    'Content-Type': 'application/json; charset=utf-8',
    'Access-Control-Allow-Origin': '*',
  });
  res.end(JSON.stringify(obj));
}

function serveFile(res, filePath) {
  const ext = path.extname(filePath);
  fs.readFile(filePath, (err, data) => {
    if (err) {
      res.writeHead(404);
      res.end('Not Found');
      return;
    }
    res.writeHead(200, { 'Content-Type': MIME_TYPES[ext] || 'application/octet-stream' });
    res.end(data);
  });
}

function serveStatic(res, filePath) {
  fs.stat(filePath, (err, stat) => {
    if (err || !stat.isFile()) {
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
    serveFile(res, filePath);
  });
}

function proxyRequest(targetUrl, reqBody, res, pathSuffix) {
  const body = JSON.stringify(reqBody);
  const options = {
    hostname: targetUrl.hostname,
    port: targetUrl.port || (targetUrl.protocol === 'https:' ? 443 : 80),
    path: pathSuffix,
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Content-Length': Buffer.byteLength(body),
    },
  };

  const proxyReq = http.request(options, (proxyRes) => {
    const headers = {
      'Access-Control-Allow-Origin': '*',
    };
    const ct = proxyRes.headers['content-type'];
    if (ct) headers['Content-Type'] = ct;

    res.writeHead(proxyRes.statusCode, headers);
    proxyRes.pipe(res);
  });

  proxyReq.on('error', (err) => {
    console.error('[Proxy Error]', err.message);
    sendJson(res, 502, { error: '上游服务不可达', detail: err.message });
  });

  proxyReq.write(body);
  proxyReq.end();
}

function proxyLLM(reqBody, res) {
  proxyRequest(
    llmUrl,
    {
      model: reqBody.model || 'deepseek-v4-flash',
      messages: reqBody.messages || [],
      temperature: reqBody.temperature ?? 0.7,
      max_tokens: reqBody.max_tokens ?? 1024,
    },
    res,
    '/v1/chat/completions'
  );
}

function listTemplatesApi() {
  if (!fs.existsSync(TEMPLATES_DIR)) return [];
  const entries = fs.readdirSync(TEMPLATES_DIR, { withFileTypes: true });
  const templates = [];

  for (const entry of entries) {
    if (!entry.isDirectory() || entry.name.startsWith('.')) continue;
    const storyPath = path.join(TEMPLATES_DIR, entry.name, 'story', 'main.md');
    if (!fs.existsSync(storyPath)) continue;

    const content = fs.readFileSync(storyPath, 'utf8');
    const lines = content.split('\n');
    let title = entry.name;
    let tags = '';
    let description = '';

    for (let i = 0; i < lines.length; i++) {
      const trimmed = lines[i].trim();
      if (trimmed.startsWith('# ') && title === entry.name) {
        title = trimmed.replace(/^#\s*/, '').replace(/^模板\s*[A-Z]：\s*/, '');
      }
      const prev = i > 0 ? lines[i - 1].trim() : '';
      if (prev === '## 类型标签' && trimmed && !trimmed.startsWith('#')) {
        tags = trimmed;
      }
      if (prev === '## 一句话简介' && trimmed && !trimmed.startsWith('#')) {
        description = trimmed;
      }
    }

    templates.push({ id: entry.name, title, tags, description });
  }

  return templates;
}

function parseBody(req, callback) {
  let body = '';
  req.on('data', (chunk) => (body += chunk));
  req.on('end', () => {
    try {
      callback(JSON.parse(body));
    } catch {
      callback(null);
    }
  });
}

const server = http.createServer((req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');

  if (req.method === 'OPTIONS') {
    res.writeHead(204);
    res.end();
    return;
  }

  const url = new URL(req.url, `http://localhost:${PORT}`);

  if (url.pathname === '/proxy/chat/completions' && req.method === 'POST') {
    parseBody(req, (body) => {
      if (!body) return sendJson(res, 400, { error: 'Invalid JSON body' });
      proxyLLM(body, res);
    });
    return;
  }

  if (url.pathname === '/proxy/tts' && req.method === 'POST') {
    parseBody(req, (body) => {
      if (!body) return sendJson(res, 400, { error: 'Invalid JSON body' });
      proxyRequest(ttsUrl, body, res, '/tts');
    });
    return;
  }

  if (url.pathname === '/proxy/health' && req.method === 'GET') {
    sendJson(res, 200, { status: 'ok', llm: LLM_BASE, tts: TTS_BASE });
    return;
  }

  if (url.pathname === '/api/templates' && req.method === 'GET') {
    sendJson(res, 200, listTemplatesApi());
    return;
  }

  if (url.pathname.startsWith('/templates/')) {
    const rel = url.pathname.slice('/templates/'.length);
    const safe = path.normalize(rel).replace(/^(\.\.(\/|\\|$))+/, '');
    const filePath = path.join(TEMPLATES_DIR, safe);
    if (!filePath.startsWith(TEMPLATES_DIR)) {
      res.writeHead(403);
      res.end('Forbidden');
      return;
    }
    serveFile(res, filePath);
    return;
  }

  let filePath = path.join(FRONTEND_DIR, url.pathname === '/' ? 'index.html' : url.pathname);
  serveStatic(res, filePath);
});

server.listen(PORT, () => {
  console.log('🚀 Girlgame 开发服务器已启动');
  console.log(`   📂 前端: http://localhost:${PORT}`);
  console.log(`   📜 剧本: http://localhost:${PORT}/templates/<id>/story/main.md`);
  console.log(`   🔗 LLM 代理: /proxy/chat/completions → ${LLM_BASE}/v1/chat/completions`);
  console.log(`   🔊 TTS 代理: /proxy/tts → ${TTS_BASE}/tts`);
});
