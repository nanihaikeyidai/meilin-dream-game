/**
 * Girlgame 开发服务器（零依赖版）
 * - 前端静态文件
 * - 剧本 markdown（/templates/）
 * - 代理 LLM：/proxy/chat/completions
 * - 代理 TTS：/proxy/tts
 *
 * 启动: node server.js
 * 环境变量: PORT, LLM_BASE, LLM_API_KEY, LLM_MODEL, TTS_BASE, AVG_MOCK_LLM
 */

const http = require('http');
const https = require('https');
const fs = require('fs');
const path = require('path');

const ROOT = __dirname;

function loadDotEnv() {
  const envPath = path.join(ROOT, '.env');
  if (!fs.existsSync(envPath)) return;
  for (const line of fs.readFileSync(envPath, 'utf8').split('\n')) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith('#')) continue;
    const eq = trimmed.indexOf('=');
    if (eq <= 0) continue;
    const key = trimmed.slice(0, eq).trim();
    const val = trimmed.slice(eq + 1).trim().replace(/^["']|["']$/g, '');
    if (!process.env[key]) process.env[key] = val;
  }
}

loadDotEnv();

const PORT = process.env.PORT || 8080;
const LLM_BASE = process.env.LLM_BASE || 'http://localhost:8656';
const LLM_API_KEY = process.env.LLM_API_KEY || '';
const LLM_MODEL = process.env.LLM_MODEL || 'deepseek-chat';
const TTS_BASE = process.env.TTS_BASE || 'http://localhost:7860';
const AVG_MOCK_LLM = process.env.AVG_MOCK_LLM === '1' || process.env.AVG_MOCK_LLM === 'true';
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

function getHttpLib(targetUrl) {
  return targetUrl.protocol === 'https:' ? https : http;
}

function getLlmChatPath() {
  const base = LLM_BASE.replace(/\/+$/, '');
  return base.endsWith('/v1') ? '/chat/completions' : '/v1/chat/completions';
}

function getLlmChatPathForBase(base) {
  const normalized = base.replace(/\/+$/, '');
  return normalized.endsWith('/v1') ? '/chat/completions' : '/v1/chat/completions';
}

function buildLlmHeaders(body, apiKey) {
  const headers = {
    'Content-Type': 'application/json',
    'Content-Length': Buffer.byteLength(body),
  };
  const key = apiKey || LLM_API_KEY;
  if (key) headers.Authorization = `Bearer ${key}`;
  return headers;
}

function resolveLlmTarget(reqHeaders) {
  const clientBase = reqHeaders?.['x-llm-base'];
  const clientKey = reqHeaders?.['x-llm-key'] || '';
  if (clientBase) {
    try {
      const targetUrl = new URL(clientBase);
      return {
        targetUrl,
        chatPath: getLlmChatPathForBase(clientBase),
        apiKey: clientKey,
      };
    } catch (err) {
      console.warn('[LLM] Invalid X-LLM-Base:', clientBase);
    }
  }
  return {
    targetUrl: llmUrl,
    chatPath: getLlmChatPath(),
    apiKey: LLM_API_KEY,
  };
}

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

function proxyRequest(targetUrl, reqBody, res, pathSuffix, apiKey, extraHeaders) {
  const body = JSON.stringify(reqBody);
  const lib = getHttpLib(targetUrl);
  const options = {
    hostname: targetUrl.hostname,
    port: targetUrl.port || (targetUrl.protocol === 'https:' ? 443 : 80),
    path: pathSuffix,
    method: 'POST',
    headers: { ...buildLlmHeaders(body, apiKey), ...(extraHeaders || {}) },
  };

  const proxyReq = lib.request(options, (proxyRes) => {
    const headers = { 'Access-Control-Allow-Origin': '*' };
    const ct = proxyRes.headers['content-type'];
    if (ct) headers['Content-Type'] = ct;
    res.writeHead(proxyRes.statusCode, headers);
    proxyRes.pipe(res);
  });

  proxyReq.on('error', (err) => {
    console.error('[Proxy Error]', err.message);
    const hint = LLM_API_KEY || apiKey
      ? '请检查 Base URL 与 API Key 是否正确'
      : '请在游戏内配置 API，或于 .env 设置 LLM_BASE + LLM_API_KEY';
    sendJson(res, 502, { error: '上游服务不可达', detail: err.message, hint, needsClientConfig: !LLM_API_KEY && !AVG_MOCK_LLM });
  });

  proxyReq.write(body);
  proxyReq.end();
}

function mockLLMResponse(reqBody, res) {
  const stream = reqBody.stream === true;
  const userMsg = (reqBody.messages || []).filter((m) => m.role === 'user').pop();
  const choice = userMsg?.content?.slice(0, 20) || '继续';
  const text =
    '### 自测场景\n\n' +
    '林雪 [MOOD: warm] [EXPR: smile]「你好，这是本地 Mock 叙事。」\n\n' +
    '你选择了：' + choice + '。蝉鸣与夕阳把教室染成金色。\n\n' +
    '1.【在教室里多待一会儿】\n' +
    '2.【去天台看看】\n' +
    '3.【给苏云溪发消息】';

  if (stream) {
    res.writeHead(200, {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      Connection: 'keep-alive',
      'Access-Control-Allow-Origin': '*',
    });
    const chunk = {
      choices: [{ delta: { content: text } }],
    };
    res.write(`data: ${JSON.stringify(chunk)}\n\n`);
    res.write('data: [DONE]\n\n');
    res.end();
    return;
  }

  sendJson(res, 200, {
    choices: [{ message: { role: 'assistant', content: text } }],
  });
}

function proxyLLM(reqBody, reqHeaders, res) {
  if (AVG_MOCK_LLM) {
    mockLLMResponse(reqBody, res);
    return;
  }

  const { targetUrl, chatPath, apiKey } = resolveLlmTarget(reqHeaders);

  const payload = {
    model: reqBody.model || LLM_MODEL,
    messages: reqBody.messages || [],
    temperature: reqBody.temperature ?? 0.7,
    max_tokens: reqBody.max_tokens ?? 1024,
  };
  if (reqBody.stream) payload.stream = true;
  proxyRequest(targetUrl, payload, res, chatPath, apiKey);
}

function proxyGet(targetUrl, pathSuffix, res) {
  const lib = getHttpLib(targetUrl);
  const options = {
    hostname: targetUrl.hostname,
    port: targetUrl.port || (targetUrl.protocol === 'https:' ? 443 : 80),
    path: pathSuffix,
    method: 'GET',
  };

  const proxyReq = lib.request(options, (proxyRes) => {
    const headers = { 'Access-Control-Allow-Origin': '*' };
    const ct = proxyRes.headers['content-type'];
    if (ct) headers['Content-Type'] = ct;
    res.writeHead(proxyRes.statusCode, headers);
    proxyRes.pipe(res);
  });

  proxyReq.on('error', (err) => {
    sendJson(res, 502, { error: '上游服务不可达', detail: err.message });
  });

  proxyReq.end();
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
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-LLM-Base, X-LLM-Key');

  if (req.method === 'OPTIONS') {
    res.writeHead(204);
    res.end();
    return;
  }

  const url = new URL(req.url, `http://localhost:${PORT}`);

  if (url.pathname === '/proxy/chat/completions' && req.method === 'POST') {
    parseBody(req, (body) => {
      if (!body) return sendJson(res, 400, { error: 'Invalid JSON body' });
      proxyLLM(body, req.headers, res);
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

  if (url.pathname === '/proxy/tts/status' && req.method === 'GET') {
    proxyGet(ttsUrl, '/tts/status', res);
    return;
  }

  if (url.pathname === '/proxy/health' && req.method === 'GET') {
    sendJson(res, 200, {
      status: 'ok',
      llm: LLM_BASE,
      llmModel: LLM_MODEL,
      llmAuth: !!LLM_API_KEY,
      mockLlm: AVG_MOCK_LLM,
      needsClientConfig: !LLM_API_KEY && !AVG_MOCK_LLM,
      tts: TTS_BASE,
      stream: true,
    });
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
  console.log(`   🔗 LLM 代理: /proxy/chat/completions → ${LLM_BASE}${getLlmChatPath()}`);
  if (LLM_API_KEY) console.log('   🔑 LLM_API_KEY 已配置');
  if (AVG_MOCK_LLM) console.log('   🧪 AVG_MOCK_LLM=1（本地 Mock 叙事）');
  else if (!LLM_API_KEY && llmUrl.hostname === 'localhost') {
    console.log('   ⚠️  未检测到 LLM_API_KEY；若 :8656 未启动将 502。可复制 .env.example → .env');
  }
  console.log(`   🔊 TTS 代理: /proxy/tts → ${TTS_BASE}/tts`);
});
