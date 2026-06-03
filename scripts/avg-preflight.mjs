#!/usr/bin/env node
/**
 * AVG 自测预检：HTTP 健康、立绘资产、页面关键标记
 * 用法: node scripts/avg-preflight.mjs [--base http://localhost:8080]
 */
import http from 'http';
import https from 'https';

const BASE = process.argv.find((a) => a.startsWith('--base='))?.slice(7)
  || process.env.AVG_BASE
  || 'http://localhost:8080';

const PORTRAIT_SETS = [
  { template: 'changan-moon', chars: ['huayingyue', 'shenmingyue', 'xieyunlan', 'lihuaijin', 'guqianfan', 'gongsunlan'] },
  { template: 'campus-summer', chars: ['linxue', 'suyunxi', 'shenqingci', 'jiangxiaoyu', 'xiazhiyao', 'chengnianci', 'yexiaoman'] },
  { template: 'cafe-night', chars: ['linyu', 'suwan', 'gunian', 'zhaozhu', 'zhoudoctor', 'qinyutong'] },
  { template: 'suspense-mansion', chars: ['linyingxue', 'chenwu', 'suwanqing', 'gunianan', 'zhaomingshen', 'jingzhongren'] },
];
const EXPRS = ['default', 'smile', 'happy', 'sad', 'angry', 'blush', 'cold', 'surprised'];

const results = [];

function record(name, ok, detail = '') {
  results.push({ name, ok, detail });
  const tag = ok ? 'PASS' : 'FAIL';
  console.log('[' + tag + '] ' + name + (detail ? ' — ' + detail : ''));
}

function fetchUrl(url, opts = {}) {
  return new Promise((resolve, reject) => {
    const lib = url.startsWith('https') ? https : http;
    const headers = { ...(opts.headers || {}) };
    if (opts.body && !headers['Content-Type']) headers['Content-Type'] = 'application/json';
    const req = lib.request(url, { method: opts.method || 'GET', timeout: 8000, headers }, (res) => {
      const chunks = [];
      res.on('data', (c) => chunks.push(c));
      res.on('end', () => resolve({ status: res.statusCode, body: Buffer.concat(chunks).toString('utf8') }));
    });
    req.on('error', reject);
    req.on('timeout', () => { req.destroy(); reject(new Error('timeout')); });
    if (opts.body) req.write(opts.body);
    req.end();
  });
}

async function headOk(path) {
  const url = `${BASE.replace(/\/$/, '')}${path}`;
  try {
    const r = await fetchUrl(url, { method: 'GET' });
    return r.status === 200;
  } catch {
    return false;
  }
}

async function main() {
  console.log(`\n=== AVG Preflight @ ${BASE} ===\n`);

  // 1. Dev server
  try {
    const health = await fetchUrl(`${BASE}/proxy/health`);
    const data = JSON.parse(health.body);
    record('dev-server /proxy/health', health.status === 200, `llm=${data.llm}`);
  } catch (e) {
    record('dev-server /proxy/health', false, e.message);
  }

  // 2. LLM via dev proxy (matches browser game path)
  let healthData = {};
  try {
    const health = await fetchUrl(`${BASE}/proxy/health`);
    healthData = JSON.parse(health.body);
  } catch { /* ignore */ }

  const chatBody = JSON.stringify({
    model: healthData.llmModel || 'deepseek-v4-flash',
    messages: [{ role: 'user', content: 'ping' }],
    max_tokens: 8,
    stream: false,
  });
  try {
    const chat = await fetchUrl(`${BASE}/proxy/chat/completions`, {
      method: 'POST',
      body: chatBody,
    });
    const ok = chat.status === 200;
    let detail = `status=${chat.status}`;
    if (healthData.mockLlm) detail += ' (AVG_MOCK_LLM)';
    else if (healthData.llmAuth) detail += ' (LLM_API_KEY set)';
    else detail += ` → ${healthData.llm || 'http://localhost:8656'}`;
    record('llm /proxy/chat/completions', ok, detail);
  } catch (e) {
    record('llm /proxy/chat/completions', false, e.message);
  }

  // 3. TTS (optional)
  try {
    const tts = await fetchUrl(`${BASE}/proxy/tts/status`);
    record('tts /proxy/tts/status', tts.status === 200, 'optional');
  } catch (e) {
    record('tts /proxy/tts/status', false, `optional — ${e.message}`);
  }

  // 4. game.html markers
  try {
    const game = await fetchUrl(`${BASE}/game.html`);
    const html = game.body;
    const markers = ['character-layer', 'left: 0', 'bottom: 0', 'choices-panel', 'z-index: 2', 'bootstrap.js', 'mood.js'];
    const missing = markers.filter((m) => !html.includes(m));
    record('game.html layout markers', missing.length === 0, missing.length ? 'missing: ' + missing.join(', ') : markers.length + ' ok');
  } catch (e) {
    record('game.html layout markers', false, e.message);
  }

  // 5. Portraits HTTP
  let found = 0;
  let missing = [];
  let total = 0;
  for (const { template, chars } of PORTRAIT_SETS) {
    for (const char of chars) {
      for (const expr of EXPRS) {
        total++;
        const rel = '/assets/portraits/' + template + '/' + char + '/' + expr + '.png';
        const ok = await headOk(rel);
        if (ok) found++;
        else missing.push(template + '/' + char + '/' + expr + '.png');
      }
    }
  }
  const missHint = missing.length
    ? ` missing ${missing.slice(0, 3).join(', ')}${missing.length > 3 ? '...' : ''}`
    : '';
  record('portraits PNG via HTTP', found >= total, `${found}/${total}${missHint}`);

  // 6. Templates API
  try {
    const tpl = await fetchUrl(`${BASE}/api/templates`);
    const list = JSON.parse(tpl.body);
    const ids = list.map((t) => t.id);
    const need = ['changan-moon', 'campus-summer'];
    const has = need.every((id) => ids.includes(id));
    record('templates API', tpl.status === 200 && has, ids.join(', '));
  } catch (e) {
    record('templates API', false, e.message);
  }

  const pass = results.filter((r) => r.ok).length;
  const fail = results.filter((r) => !r.ok).length;
  const llmFail = results.find((r) => r.name === 'llm /proxy/chat/completions' && !r.ok);

  console.log(`\n=== Summary: ${pass} PASS / ${fail} FAIL ===`);
  if (llmFail) {
    console.log('\nNote: LLM 502 时：复制 .env.example → .env 填 DeepSeek Key，或 AVG_MOCK_LLM=1 后重启 npm run dev');
  }

  const blockingFails = results.filter((r) => {
    if (r.ok) return false;
    if (r.name.startsWith('tts ')) return false;
    if (r.name === 'llm /proxy/chat/completions' && process.argv.includes('--allow-llm-fail')) return false;
    return true;
  });

  process.exit(blockingFails.length > 0 ? 1 : 0);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
