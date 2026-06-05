#!/usr/bin/env node
/**
 * 一键启动：TTS 服务 + AVG 开发服
 * 用法: npm run dev:all
 *
 * 环境变量（也可写在 .env）:
 *   PORT          开发服端口，默认 8080
 *   TTS_PORT      TTS 端口，默认 7860
 *   TTS_PYTHON    Python 解释器（需含 voxcpm），默认 ComfyUI Python 3.12.6
 *   VOXCPM2_PATH  VoxCPM2 模型目录
 *   TTS_BASE      开发服 TTS 代理目标，默认 http://localhost:7860
 *   SKIP_TTS=1    仅启动开发服，不拉起 server_tts.py
 */
import { spawn } from 'child_process';
import fs from 'fs';
import http from 'http';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, '..');

const DEFAULT_PYTHON = 'F:\\ComfyUI_V6.0\\ComfyUI-WorkFisher-V2\\Python3.12.6\\python.exe';
const DEFAULT_VOXCPM = 'F:\\ComfyUI_V6.0\\ComfyUI-WorkFisher-V2\\ComfyUI\\models\\VoxCPM2';

const children = [];

function loadDotEnv(envPath) {
  if (!envPath || !fs.existsSync(envPath)) return;
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

function fetchJson(url, timeoutMs = 5000) {
  return new Promise((resolve, reject) => {
    const req = http.get(url, { timeout: timeoutMs }, (res) => {
      const chunks = [];
      res.on('data', (c) => chunks.push(c));
      res.on('end', () => {
        try {
          resolve({ status: res.statusCode, body: JSON.parse(Buffer.concat(chunks).toString('utf8')) });
        } catch (e) {
          reject(e);
        }
      });
    });
    req.on('error', reject);
    req.on('timeout', () => {
      req.destroy();
      reject(new Error('timeout'));
    });
  });
}

async function isTtsReady(ttsBase) {
  try {
    const { status, body } = await fetchJson(`${ttsBase.replace(/\/$/, '')}/tts/status`);
    return status === 200 && body?.model_loaded === true;
  } catch {
    return false;
  }
}

async function waitForTts(ttsBase, timeoutMs) {
  const deadline = Date.now() + timeoutMs;
  process.stdout.write('[dev:all] 等待 TTS 就绪');
  while (Date.now() < deadline) {
    if (await isTtsReady(ttsBase)) {
      process.stdout.write('\n');
      return true;
    }
    process.stdout.write('.');
    await new Promise((r) => setTimeout(r, 2000));
  }
  process.stdout.write('\n');
  return false;
}

function killProcessTree(proc) {
  if (!proc?.pid) return;
  if (process.platform === 'win32') {
    spawn('taskkill', ['/PID', String(proc.pid), '/T', '/F'], { stdio: 'ignore', shell: true });
  } else {
    try {
      proc.kill('SIGTERM');
    } catch {
      /* ignore */
    }
  }
}

function cleanup() {
  for (const proc of children) killProcessTree(proc);
}

function track(proc, label) {
  children.push(proc);
  proc.on('exit', (code, signal) => {
    const idx = children.indexOf(proc);
    if (idx >= 0) children.splice(idx, 1);
    if (label === 'dev' && code !== 0 && signal !== 'SIGTERM' && signal !== 'SIGINT') {
      console.error(`[dev:all] 开发服退出 code=${code} signal=${signal || ''}`);
      cleanup();
      process.exit(code ?? 1);
    }
  });
}

async function startTts() {
  const ttsPort = process.env.TTS_PORT || '7860';
  const ttsBase = process.env.TTS_BASE || `http://127.0.0.1:${ttsPort}`;
  const python = process.env.TTS_PYTHON || DEFAULT_PYTHON;
  const modelPath = process.env.VOXCPM2_PATH || DEFAULT_VOXCPM;
  const serverTts = path.join(ROOT, 'frontend', 'server_tts.py');

  if (await isTtsReady(ttsBase)) {
    console.log(`[dev:all] TTS 已在运行: ${ttsBase} (model_loaded=true)`);
    return;
  }

  if (!fs.existsSync(python)) {
    console.error(`[dev:all] 未找到 Python: ${python}`);
    console.error('请设置 TTS_PYTHON 为已安装 voxcpm 的解释器（如 ComfyUI Python 3.12.6）');
    process.exit(1);
  }

  if (!fs.existsSync(serverTts)) {
    console.error(`[dev:all] 未找到 ${serverTts}`);
    process.exit(1);
  }

  console.log(`[dev:all] 启动 TTS: ${python}`);
  console.log(`[dev:all] 模型路径: ${modelPath}`);

  const proc = spawn(python, ['-u', serverTts], {
    cwd: path.join(ROOT, 'frontend'),
    env: {
      ...process.env,
      TTS_PORT: ttsPort,
      VOXCPM2_PATH: modelPath,
    },
    stdio: 'inherit',
  });
  track(proc, 'tts');

  const ready = await waitForTts(ttsBase, Number(process.env.TTS_READY_TIMEOUT_MS || 180000));
  if (!ready) {
    console.error('[dev:all] TTS 启动超时。可单独运行 server_tts.py 排查，或设 SKIP_TTS=1 仅开开发服');
    cleanup();
    process.exit(1);
  }
  console.log(`[dev:all] TTS 就绪: ${ttsBase}`);
}

function startDevServer() {
  const serverJs = path.join(ROOT, 'server.js');
  const port = process.env.PORT || '8080';
  process.env.PORT = port;

  console.log(`[dev:all] 启动开发服: http://127.0.0.1:${port}`);

  const proc = spawn(process.execPath, [serverJs], {
    cwd: ROOT,
    env: process.env,
    stdio: 'inherit',
  });
  track(proc, 'dev');
}

async function main() {
  loadDotEnv(path.join(ROOT, '.env'));

  process.on('SIGINT', () => {
    console.log('\n[dev:all] 正在停止…');
    cleanup();
    process.exit(0);
  });
  process.on('SIGTERM', () => {
    cleanup();
    process.exit(0);
  });

  console.log('=== AVG 开发环境（TTS + 开发服）===\n');

  if (process.env.SKIP_TTS === '1') {
    console.log('[dev:all] SKIP_TTS=1，跳过 TTS');
  } else {
    await startTts();
  }

  startDevServer();
}

main().catch((err) => {
  console.error('[dev:all]', err);
  cleanup();
  process.exit(1);
});
