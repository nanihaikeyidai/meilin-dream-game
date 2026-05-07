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

function setupIpcHandlers() {
  ipcMain.handle('apiKey:save', (event, data) => {
    setConfig('apiConfig', data);
    return { success: true };
  });

  ipcMain.handle('apiKey:load', () => {
    return getConfig('apiConfig', { baseUrl: '', apiKey: '' });
  });

  ipcMain.handle('templates:list', () => {
    const templatesDir = path.join(__dirname, '..', 'templates');
    const files = fs.readdirSync(templatesDir).filter(f => f.endsWith('.md') && f !== 'perspective-template.md');
    return files.map(f => {
      const id = f.replace('.md', '');
      const meta = parseTemplateMeta(path.join(templatesDir, f));
      return { id, ...meta };
    });
  });

  ipcMain.handle('fs:read', (event, filePath) => {
    const templatesDir = path.join(__dirname, '..', 'templates');
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
    if (win) {
      win.loadFile(path.join(__dirname, '..', 'frontend', `${page}.html`));
    }
  });
}

module.exports = { setupIpcHandlers };
