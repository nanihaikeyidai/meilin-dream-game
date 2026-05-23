const { ipcMain, app } = require('electron');
const fs = require('fs');
const path = require('path');

function getConfigPath() {
  return path.join(app.getPath('userData'), 'config.json');
}

function readConfig() {
  try {
    return JSON.parse(fs.readFileSync(getConfigPath(), 'utf8'));
  } catch {
    return {};
  }
}

function writeConfig(data) {
  fs.writeFileSync(getConfigPath(), JSON.stringify(data, null, 2));
}

function getConfig(key, defaultValue) {
  const data = readConfig();
  return data[key] !== undefined ? data[key] : defaultValue;
}

function setConfig(key, value) {
  const data = readConfig();
  data[key] = value;
  writeConfig(data);
}

function parseTemplateMeta(filePath) {
  const content = fs.readFileSync(filePath, 'utf8');
  const lines = content.split('\n');
  let title = '';
  let tags = '';
  let description = '';

  for (const line of lines) {
    const trimmed = line.trim();
    if (trimmed.startsWith('# ') && !title) {
      title = trimmed.replace(/^#\s*/, '');
    } else if (trimmed.startsWith('## 类型标签') && !tags) {
      continue;
    } else if (!tags && trimmed && !trimmed.startsWith('#') && !trimmed.startsWith('---') && !description) {
      const prevIdx = lines.indexOf(line);
      const prev = lines[prevIdx - 1] ? lines[prevIdx - 1].trim() : '';
      if (prev === '## 类型标签') {
        tags = trimmed;
      }
    } else if (trimmed.startsWith('## 一句话简介')) {
      continue;
    } else if (!description && trimmed && !trimmed.startsWith('#')) {
      const prevIdx = lines.indexOf(line);
      const prev = lines[prevIdx - 1] ? lines[prevIdx - 1].trim() : '';
      if (prev === '## 一句话简介') {
        description = trimmed;
        break;
      }
    }
  }

  return { title, tags, description };
}

function parseTemplateFromDir(dirPath) {
  const storyPath = path.join(dirPath, 'story', 'main.md');
  const templateId = path.basename(dirPath);

  try {
    if (!fs.existsSync(storyPath)) {
      return null;
    }
    const content = fs.readFileSync(storyPath, 'utf8');
    const lines = content.split('\n');
    let title = templateId;
    let description = '';
    let tags = '';

    for (const line of lines) {
      const trimmed = line.trim();
      if (trimmed.startsWith('# ') && !title) {
        title = trimmed.replace(/^#\s*/, '');
      }
      if (trimmed.startsWith('## 类型标签') || trimmed.startsWith('**类型标签**')) {
        continue;
      }
      if (!tags && trimmed && !trimmed.startsWith('#') && !trimmed.startsWith('---') && !trimmed.startsWith('>')) {
        // Look for tag-like content (keywords after 类型标签 heading)
        const prevIdx = lines.indexOf(line);
        const prev = prevIdx > 0 ? lines[prevIdx - 1].trim() : '';
        if (prev.startsWith('## 类型标签') || prev.startsWith('**类型标签**')) {
          tags = trimmed;
        }
      }
      if (trimmed.startsWith('## 一句话简介') || trimmed.startsWith('**一句话简介**')) {
        continue;
      }
      if (!description && trimmed && !trimmed.startsWith('#') && !trimmed.startsWith('>')) {
        const prevIdx = lines.indexOf(line);
        const prev = prevIdx > 0 ? lines[prevIdx - 1].trim() : '';
        if (prev.startsWith('## 一句话简介') || prev.startsWith('**一句话简介**')) {
          description = trimmed;
        }
      }
    }

    // Fallback: use first paragraph as description
    if (!description) {
      for (const line of lines) {
        const trimmed = line.trim();
        if (trimmed && !trimmed.startsWith('#') && !trimmed.startsWith('---') && !trimmed.startsWith('>')) {
          description = trimmed.length > 100 ? trimmed.slice(0, 100) + '…' : trimmed;
          break;
        }
      }
    }

    return { id: templateId, title, tags, description };
  } catch {
    return null;
  }
}

function setupIpcHandlers(options = {}) {
  const getBaseUrl = options.getBaseUrl || (() => null);
  const getAppRoot = options.getAppRoot || (() => path.join(__dirname, '..'));
  ipcMain.handle('apiKey:save', (event, data) => {
    setConfig('apiConfig', data);
    return { success: true };
  });

  ipcMain.handle('apiKey:load', () => {
    return getConfig('apiConfig', { baseUrl: '', apiKey: '', model: '' });
  });

  ipcMain.handle('templates:list', () => {
    const templatesDir = path.join(getAppRoot(), 'templates');
    const entries = fs.readdirSync(templatesDir, { withFileTypes: true });
    const templates = [];

    // First try subdirectories (each template is a dir with story/main.md)
    for (const entry of entries) {
      if (entry.isDirectory() && !entry.name.startsWith('.')) {
        const meta = parseTemplateFromDir(path.join(templatesDir, entry.name));
        if (meta) {
          templates.push(meta);
        }
      }
    }

    // Fallback: try flat .md files (old format)
    if (templates.length === 0) {
      const mdFiles = entries.filter(e => e.isFile() && e.name.endsWith('.md'));
      for (const f of mdFiles) {
        const filePath = path.join(templatesDir, f.name);
        const meta = parseTemplateMeta(filePath);
        templates.push({ id: f.name.replace('.md', ''), ...meta });
      }
    }

    return templates;
  });

  ipcMain.handle('fs:read', (event, filePath) => {
    const templatesDir = path.join(getAppRoot(), 'templates');
    const target = path.resolve(templatesDir, filePath);
    if (!target.startsWith(templatesDir)) {
      throw new Error('Invalid path');
    }
    return fs.readFileSync(target, 'utf8');
  });

  ipcMain.handle('llm:chat', async (event, { messages, config }) => {
    const { baseUrl, apiKey, model, temperature, maxTokens } = config;
    const url = `${baseUrl.replace(/\/$/, '')}/chat/completions`;
    const body = { model, messages };
    if (temperature !== undefined) body.temperature = temperature;
    if (maxTokens !== undefined) body.max_tokens = maxTokens;

    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${apiKey}`
      },
      body: JSON.stringify(body)
    });

    if (!response.ok) {
      const text = await response.text();
      throw new Error(`LLM request failed: ${response.status} ${text}`);
    }

    const data = await response.json();
    return data.choices[0].message.content;
  });

  ipcMain.on('app:exit', () => {
    app.quit();
  });

  ipcMain.on('navigate:to', (event, page) => {
    const win = require('electron').BrowserWindow.fromWebContents(event.sender);
    const base = getBaseUrl();
    if (win && base) {
      win.loadURL(`${base}/${page}.html`);
      return;
    }
    if (win) {
      win.loadFile(path.join(getAppRoot(), 'frontend', `${page}.html`));
    }
  });
}

module.exports = { setupIpcHandlers };
