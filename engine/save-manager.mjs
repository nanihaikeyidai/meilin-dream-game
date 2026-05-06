#!/usr/bin/env node
/**
 * Galgame Save Manager
 * 统一存档接口：读、写、初始化、自动存档
 * 用法：node save-manager.mjs <cmd> [args]
 */
import fs from 'fs/promises';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, '..');
const SAVE_DIR = path.join(ROOT, '.galgame', 'saves');

async function ensureDir(dir) {
  await fs.mkdir(dir, { recursive: true });
}

function now() {
  return new Date().toISOString().split('T')[0];
}

/* ---------- init ---------- */
async function cmdInit(data) {
  const saveName = data.save_name;
  const dir = path.join(SAVE_DIR, saveName);
  await ensureDir(dir);
  await ensureDir(path.join(dir, 'perspectives'));

  // session.json
  const session = {
    save_name: saveName,
    template: data.template,
    created_at: now(),
    last_played: now(),
    protagonist: data.protagonist,
    affection: data.affection || {},
    flags: data.flags || {},
    stats: data.stats || { decisions_made: 0, total_estimated_decisions: 25 },
    current_route: data.current_route || null,
    current_act: data.current_act || 0,
    scene_progress: data.scene_progress || [],
    unlocked_routes: data.unlocked_routes || [],
    weather: data.weather || '晴',
    time_of_day: data.time_of_day || '午后',
    inventory: data.inventory || [],
    location: data.location || '校门口'
  };
  await fs.writeFile(path.join(dir, 'session.json'), JSON.stringify(session, null, 2), 'utf8');

  // perspectives/*.md
  const npcs = data.npcs || [];
  for (const npc of npcs) {
    const tmpl = `---\nnpc: ${npc}\n---\n\n## 亲眼所见\n- （空）\n\n## 亲口所说\n- （空）\n\n## 听闻（从他人处得知）\n- （空）\n\n## 内心（仅自己知道）\n- （空）\n`;
    await fs.writeFile(path.join(dir, 'perspectives', `${npc}.md`), tmpl, 'utf8');
  }

  return { ok: true, save_name: saveName };
}

/* ---------- save ---------- */
async function cmdSave(data) {
  const saveName = data.save_name;
  const dir = path.join(SAVE_DIR, saveName);
  await ensureDir(dir);

  // merge into session
  const sessionPath = path.join(dir, 'session.json');
  let session = {};
  try {
    session = JSON.parse(await fs.readFile(sessionPath, 'utf8'));
  } catch { /* fresh */ }

  Object.assign(session, data.patch || {});
  session.last_played = now();
  await fs.writeFile(sessionPath, JSON.stringify(session, null, 2), 'utf8');

  // perspectives
  if (data.perspectives) {
    await ensureDir(path.join(dir, 'perspectives'));
    for (const [npc, content] of Object.entries(data.perspectives)) {
      await fs.writeFile(path.join(dir, 'perspectives', `${npc}.md`), content, 'utf8');
    }
  }

  // auto-save snapshot
  if (data.auto_save) {
    const idx = data.auto_save.index || 1;
    const snap = {
      save_point: data.auto_save.label || `save_${idx}`,
      timestamp: now(),
      scene: session.scene_progress?.at(-1) || session.location,
      act: session.current_act,
      location: session.location,
      affection: session.affection,
      flags: session.flags,
      recent_events: data.auto_save.recent_events || [],
      protagonist: session.protagonist
    };
    await fs.writeFile(
      path.join(dir, `save_${idx}.json`),
      JSON.stringify(snap, null, 2),
      'utf8'
    );
  }

  return { ok: true };
}

/* ---------- load ---------- */
async function cmdLoad(saveName) {
  const dir = path.join(SAVE_DIR, saveName);
  const sessionPath = path.join(dir, 'session.json');
  const session = JSON.parse(await fs.readFile(sessionPath, 'utf8'));

  // load all perspectives
  const perspDir = path.join(dir, 'perspectives');
  const perspectives = {};
  try {
    const files = await fs.readdir(perspDir);
    for (const f of files.filter(x => x.endsWith('.md'))) {
      perspectives[f.replace('.md', '')] = await fs.readFile(path.join(perspDir, f), 'utf8');
    }
  } catch { /* no perspectives */ }

  return { session, perspectives };
}

/* ---------- list ---------- */
async function cmdList() {
  await ensureDir(SAVE_DIR);
  const dirs = await fs.readdir(SAVE_DIR, { withFileTypes: true });
  const saves = [];
  for (const d of dirs.filter(x => x.isDirectory())) {
    try {
      const s = JSON.parse(await fs.readFile(path.join(SAVE_DIR, d.name, 'session.json'), 'utf8'));
      saves.push({ name: d.name, template: s.template, last_played: s.last_played, protagonist: s.protagonist?.name });
    } catch { /* skip broken */ }
  }
  return { saves };
}

/* ---------- main ---------- */
async function main() {
  const cmd = process.argv[2];
  const raw = process.argv[3];

  if (!cmd) {
    console.log(JSON.stringify({ error: 'no command' }));
    process.exit(1);
  }

  let data = {};
  if (raw) {
    try { data = JSON.parse(raw); } catch { data = raw; }
  }

  let result;
  switch (cmd) {
    case 'init': result = await cmdInit(data); break;
    case 'save': result = await cmdSave(data); break;
    case 'load': result = await cmdLoad(data); break;
    case 'list': result = await cmdList(); break;
    default:
      console.log(JSON.stringify({ error: `unknown command: ${cmd}` }));
      process.exit(1);
  }

  console.log(JSON.stringify(result));
}

main().catch(e => {
  console.log(JSON.stringify({ error: e.message }));
  process.exit(1);
});
