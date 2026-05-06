#!/usr/bin/env node
/**
 * 快速批量存档
 * 用法：node batch-save.mjs '<json>'
 * 一次性写入 session + 所有视角文件 + 自动存档
 */
import fs from 'fs/promises';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, '..');
const SAVE_DIR = path.join(ROOT, '.galgame', 'saves');

async function main() {
  const raw = process.argv[2];
  if (!raw) { console.log(JSON.stringify({ error: 'no data' })); process.exit(1); }

  const data = JSON.parse(raw);
  const saveName = data.save_name;
  const dir = path.join(SAVE_DIR, saveName);

  await fs.mkdir(dir, { recursive: true });

  // session
  const sessionPath = path.join(dir, 'session.json');
  let session = {};
  try { session = JSON.parse(await fs.readFile(sessionPath, 'utf8')); } catch {}
  Object.assign(session, data.session || {});
  session.last_played = new Date().toISOString().split('T')[0];
  await fs.writeFile(sessionPath, JSON.stringify(session, null, 2));

  // perspectives
  if (data.perspectives) {
    const pd = path.join(dir, 'perspectives');
    await fs.mkdir(pd, { recursive: true });
    for (const [k, v] of Object.entries(data.perspectives)) {
      await fs.writeFile(path.join(pd, `${k}.md`), v);
    }
  }

  // auto-save
  if (data.autoSave) {
    const idx = data.autoSave.index || Date.now();
    await fs.writeFile(
      path.join(dir, `save_${idx}.json`),
      JSON.stringify(data.autoSave, null, 2)
    );
  }

  console.log(JSON.stringify({ ok: true }));
}

main().catch(e => { console.log(JSON.stringify({ error: e.message })); process.exit(1); });
