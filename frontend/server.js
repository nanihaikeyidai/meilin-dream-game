/**
 * 月下长安 — 开发服务器 + API 代理
 * 
 * 浏览器模式下所需：
 *   - 静态文件服务 (game.html → js/*.js → assets/*)
 *   - /proxy/chat/completions → LLM API 代理 (SSE 流式 + 非流式)
 *   - /proxy/tts → TTS 服务代理 (server_tts.py :7860)
 *   - /proxy/tts/status → TTS 健康检查
 *   - /api/templates → 模板列表
 *   - /templates/{id}/story/main.md → 模板剧本
 *
 * 启动方式：
 *   npm run dev    (需要 node server.js 先)
 *   node frontend/server.js
 */

const http = require('http');
const fs = require('fs');
const path = require('path');

// ── 配置 ───────────────────────────────────────────────
const PORT = parseInt(process.env.PORT || '8080', 10);
const ROOT = path.resolve(__dirname);               // frontend/
const PROJECT_ROOT = path.resolve(__dirname, '..');  // girlgame-skill/
const TTS_BASE = process.env.TTS_BASE || 'http://127.0.0.1:7860';
const LLM_BASE = process.env.LLM_BASE || 'http://127.0.0.1:8656/v1';
const LLM_MODEL = process.env.LLM_MODEL || 'july';

// ── MIME 映射 ───────────────────────────────────────────
const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.js':   'application/javascript; charset=utf-8',
  '.css':  'text/css; charset=utf-8',
  '.png':  'image/png',
  '.jpg':  'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.webp': 'image/webp',
  '.gif':  'image/gif',
  '.svg':  'image/svg+xml',
  '.ico':  'image/x-icon',
  '.json': 'application/json; charset=utf-8',
  '.md':   'text/markdown; charset=utf-8',
  '.wav':  'audio/wav',
  '.mp3':  'audio/mpeg',
  '.woff2':'font/woff2',
  '.ttf':  'font/ttf',
};

// ── 静态文件服务 ─────────────────────────────────────────
function serveStatic(req, res) {
  let urlPath = req.url.split('?')[0];
  if (urlPath.endsWith('/')) urlPath += 'index.html';

  // 安全检查：禁止跳出 ROOT
  let filePath = path.normalize(path.join(ROOT, urlPath));
  if (!filePath.startsWith(ROOT)) {
    res.writeHead(403);
    res.end('Forbidden');
    return;
  }

  const ext = path.extname(filePath).toLowerCase();
  const contentType = MIME[ext] || 'application/octet-stream';

  fs.readFile(filePath, (err, data) => {
    if (err) {
      // 尝试 templates 目录
      const tplPath = path.normalize(path.join(PROJECT_ROOT, urlPath));
      if (tplPath.startsWith(PROJECT_ROOT)) {
        fs.readFile(tplPath, (err2, data2) => {
          if (err2) {
            res.writeHead(404);
            res.end('Not Found');
            return;
          }
          res.writeHead(200, { 'Content-Type': MIME[ext] || 'text/plain; charset=utf-8' });
          res.end(data2);
        });
        return;
      }
      res.writeHead(404);
      res.end('Not Found');
      return;
    }
    res.writeHead(200, { 'Content-Type': contentType });
    res.end(data);
  });
}

// ── LLM API 代理 ────────────────────────────────────────
function proxyChat(req, res) {
  let body = '';
  req.on('data', (chunk) => (body += chunk));
  req.on('end', () => {
    let parsed;
    try { parsed = JSON.parse(body); } catch {
      res.writeHead(400);
      res.end(JSON.stringify({ error: 'Invalid JSON' }));
      return;
    }

    if (!parsed.model) parsed.model = LLM_MODEL;
    const isStream = parsed.stream === true;
    const urlObj = new URL(LLM_BASE);

    const options = {
      method: 'POST',
      hostname: urlObj.hostname,
      port: urlObj.port || 80,
      path: urlObj.pathname.replace(/\/+$/, '') + '/chat/completions',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(JSON.stringify(parsed)),
      },
    };

    const proxyReq = http.request(options, (proxyRes) => {
      if (isStream) {
        res.writeHead(proxyRes.statusCode, {
          'Content-Type': 'text/event-stream',
          'Cache-Control': 'no-cache',
          'Connection': 'keep-alive',
          'Access-Control-Allow-Origin': '*',
        });
        proxyRes.pipe(res);
      } else {
        let data = '';
        proxyRes.on('data', (chunk) => (data += chunk));
        proxyRes.on('end', () => {
          res.writeHead(proxyRes.statusCode, {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
          });
          res.end(data);
        });
      }
    });

    proxyReq.on('error', (err) => {
      res.writeHead(502);
      res.end(JSON.stringify({ error: 'LLM proxy error: ' + err.message }));
    });

    proxyReq.write(JSON.stringify(parsed));
    proxyReq.end();
  });
}

// ── TTS 代理 ─────────────────────────────────────────────
function proxyTts(req, res) {
  const method = req.method;
  const pathname = req.url;

  if (method === 'GET' && pathname === '/proxy/tts/status') {
    const pReq = http.get(`${TTS_BASE}/tts/status`, (pRes) => {
      let data = '';
      pRes.on('data', (chunk) => (data += chunk));
      pRes.on('end', () => {
        res.writeHead(pRes.statusCode, {
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*',
        });
        res.end(data);
      });
    });
    pReq.on('error', () => {
      res.writeHead(200, { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' });
      res.end(JSON.stringify({ status: 'unavailable', model_loaded: false, uptime: 0 }));
    });
  } else if (method === 'POST' && pathname === '/proxy/tts') {
    let body = '';
    req.on('data', (chunk) => (body += chunk));
    req.on('end', () => {
      const options = {
        method: 'POST',
        hostname: '127.0.0.1',
        port: 7860,
        path: '/tts',
        headers: {
          'Content-Type': 'application/json',
          'Content-Length': Buffer.byteLength(body),
        },
      };

      const pReq = http.request(options, (pRes) => {
        res.writeHead(pRes.statusCode, {
          'Content-Type': pRes.headers['content-type'] || 'audio/wav',
          'Access-Control-Allow-Origin': '*',
        });
        pRes.pipe(res);
      });

      pReq.on('error', (err) => {
        res.writeHead(502);
        res.end(JSON.stringify({ error: 'TTS proxy error: ' + err.message }));
      });

      pReq.write(body);
      pReq.end();
    });
  } else {
    res.writeHead(405);
    res.end('Method Not Allowed');
  }
}

// ── /api/templates 模板列表 ──────────────────────────────
function listTemplates(req, res) {
  const templatesDir = path.join(PROJECT_ROOT, 'templates');
  const templates = [];

  if (fs.existsSync(templatesDir)) {
    const entries = fs.readdirSync(templatesDir, { withFileTypes: true });
    for (const entry of entries) {
      if (entry.isDirectory() && !entry.name.startsWith('.')) {
        const storyPath = path.join(templatesDir, entry.name, 'story', 'main.md');
        if (fs.existsSync(storyPath)) {
          templates.push({
            id: entry.name,
            title: entry.name
              .replace(/-/g, ' ')
              .replace(/\b\w/g, (c) => c.toUpperCase()),
            description: entry.name,
          });
        }
      }
    }
  }

  res.writeHead(200, {
    'Content-Type': 'application/json',
    'Access-Control-Allow-Origin': '*',
  });
  res.end(JSON.stringify(templates));
}

// ── 健康检查 ─────────────────────────────────────────────
function healthCheck(req, res) {
  res.writeHead(200, {
    'Content-Type': 'application/json',
    'Access-Control-Allow-Origin': '*',
  });
  res.end(JSON.stringify({
    status: 'ok',
    uptime: process.uptime(),
    port: PORT,
    llm: LLM_BASE,
    tts: TTS_BASE,
  }));
}

// ── 路由器 ───────────────────────────────────────────────
function handleRequest(req, res) {
  if (req.method === 'OPTIONS') {
    res.writeHead(204, {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    });
    res.end();
    return;
  }

  const url = req.url.split('?')[0];
  const method = req.method;

  if (url === '/proxy/health')                      { healthCheck(req, res); return; }
  if (url === '/api/templates')                     { listTemplates(req, res); return; }
  if (method === 'POST' && url === '/proxy/chat/completions') { proxyChat(req, res); return; }
  if (url.startsWith('/proxy/tts'))                  { proxyTts(req, res); return; }

  serveStatic(req, res);
}

// ── 启动 ─────────────────────────────────────────────────
const server = http.createServer(handleRequest);
server.on('error', (err) => {
  console.error('[FATAL] Server error:', err.message);
  process.exit(1);
});

try {
  server.listen(PORT, '0.0.0.0', () => {
    const msg = [
      `[${new Date().toISOString()}]`,
      `  月下长安 · 开发服务器启动`,
      `  静态服务: http://localhost:${PORT}`,
      `  LLM 代理: ${LLM_BASE} → /proxy/chat/completions`,
      `  TTS 代理: ${TTS_BASE} → /proxy/tts`,
      `  模型名:   ${LLM_MODEL}`,
    ].join('\n');
    process.stdout.write(msg + '\n');
  });
} catch (e) {
  process.stderr.write('Startup failed: ' + e.message + '\n');
  process.exit(1);
}
